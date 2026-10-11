"""Fail closed on missing PDFs/metadata/objects; Poppler renders and checks each PDF.

Automated checks complement mandatory human inspection of every rendered page.
No PDFs are created by this script; scientific authoring is native ROOT/C++.
"""
import argparse,hashlib,json,math,re,struct,subprocess,tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

STANDARD='atlas-root-plot-v2'
OFFICIAL_LABELS=['ATLAS Preliminary','ATLAS Internal','ATLAS Official','ATLAS Simulation Preliminary']
VISIBLE_DIAGNOSTICS=['Inspected','Accepted','Entries [','Selection:','Units:','Record ',
                     'Raw unweighted counts','raw unweighted GamGam skim',
                     'not the official ATLAS HH analysis','Independent exploratory analysis',
                     'Independent numerical validation','Independent work;']

def command(*args):
    return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT)

def ppm_pixels(data):
    match=re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s',data)
    if not match:raise ValueError('Malformed Poppler PPM render')
    width,height=map(int,match.groups());pixels=data[match.end():]
    if len(pixels)!=width*height*3:raise ValueError('Truncated render')
    total=0;interior=0
    for y in range(height):
        for x in range(width):
            i=3*(y*width+x)
            if min(pixels[i:i+3])<220:
                total+=1
                if .17*width<x<.93*width and .08*height<y<.83*height:interior+=1
    if total<1000 or interior<30:raise ValueError('Blank or malformed canvas/render')
    return width,height,total,interior

def validate_layout(layout):
    required=['left_margin','right_margin','top_margin','bottom_margin','axis_title_size',
              'axis_label_size','text_size','marker_style','marker_size','label_position',
              'label_x','label_y','single_series_legend','nominal_width','nominal_height','experiment_text_size']
    if not isinstance(layout,dict) or any(k not in layout for k in required):
        raise ValueError('Required publication layout metadata missing')
    def close(key,expected):
        value=layout[key]
        return type(value) in (int,float) and math.isfinite(value) and abs(value-expected)<1e-6
    for key,expected in [('left_margin',.16),('top_margin',.05),('bottom_margin',.16),
                         ('axis_title_size',.05),('axis_label_size',.045),('text_size',.04),
                         ('experiment_text_size',.045),
                         ('marker_style',20),('marker_size',.9),('nominal_width',800),('nominal_height',600)]:
        if not close(key,expected):raise ValueError('Non-publication layout: '+key)
    # A colour-bar plot has an explicitly recorded, modest right-margin adjustment.
    if not any(close('right_margin',v) for v in [.05,.16]):raise ValueError('Excessive publication margins')
    if layout['single_series_legend'] is not False:raise ValueError('Unnecessary single-series legend')
    if layout['label_position'] not in ['upper_left','upper_right']:raise ValueError('Invalid label placement')
    for key in ['label_x','label_y']:
        if type(layout[key]) not in (int,float) or not math.isfinite(layout[key]):raise ValueError('Invalid label coordinate')
    if not (.16<layout['label_x']<1-layout['right_margin'] and .70<=layout['label_y']<=.92):
        raise ValueError('Label coordinates outside publication plotting frame')
    if (layout['label_position']=='upper_left' and layout['label_x']>.45) or (layout['label_position']=='upper_right' and layout['label_x']<.50):
        raise ValueError('Label coordinate and named placement disagree')

def validate_caption(m,caption_file):
    caption=m.get('caption')
    if not isinstance(caption,str) or not caption.strip():raise ValueError('Required figure caption missing')
    if not caption_file.is_file() or caption_file.read_text()!=caption:
        raise ValueError('Caption file/sidecar caption disagree')
    if any(value.lower() in caption.lower() for value in OFFICIAL_LABELS):raise ValueError('Forbidden official-status caption')
    for key in ['record','period','selection','unit_status','weighting']:
        if m[key] not in caption:raise ValueError('Scientific metadata missing from caption: '+key)
    # These labels avoid accidental matches to unrelated numbers elsewhere in a caption.
    for key in ['inspected','accepted']:
        if not re.search(r'\b'+key+r'\s*:?\s*'+str(m[key])+r'\b',caption,re.I):
            raise ValueError('Event count missing from caption: '+key)
    if not re.search(r'\[\s*'+str(m['start'])+r'\s*,\s*'+str(m['end'])+r'\s*\)',caption):
        raise ValueError('Source range missing from caption')
    if m['sample_kind']=='SYNTHETIC':
        expected=['Synthetic test','no collision data or MC','not an official ATLAS measurement']
    elif m['sample_kind']=='MC':
        expected=['MC simulation','no observed collision data','not an official ATLAS measurement']
    else:
        expected=['Independent exploratory analysis','not the official ATLAS HH analysis']
        if m['record']=='93915':expected+=['raw unweighted GamGam skim']
    for value in expected:
        if value.lower() not in caption.lower():raise ValueError('Scientific scope missing from caption: '+value)
    if m['sample_kind']!='SYNTHETIC' and f"{m['energy_tev']:g} TeV" not in caption:
        raise ValueError('Energy metadata missing from caption')
    if m.get('luminosity_pb') is not None and (f"{m['luminosity_pb']:g}" not in caption or m['luminosity_evidence'] not in caption):
        raise ValueError('Validated luminosity/evidence missing from caption')

def compact_labels(m):
    if m['sample_kind']=='SYNTHETIC':
        return ['Synthetic test','Numerical validation',
                'Verified fixture' if m['unit_status']=='VERIFIED' else 'Provisional fixture']
    year=re.search(r'\b(?:19|20)\d{2}\b',m['period'])
    if not year:raise ValueError('Collision period has no validated year for compact label')
    kind='data' if m['sample_kind']=='DATA' else 'MC simulation'
    return ['ATLAS Open Data',f"{m['energy_tev']:g} TeV",year.group(0)+' '+kind,
            'Exploratory, provisional' if m['unit_status']=='PROVISIONAL' else 'Exploratory, verified']

def annotation_boxes(bbox_xml,labels,layout,effective):
    """Check Poppler text boxes inside the frame; rotated PDF page attributes are unreliable.

    pdfinfo's effective CropBox supplies the displayed coordinates. Poppler word
    coordinates already follow display rotation, including for ROOT's 90 degree PDFs.
    This verifies compact labels, not their overlap with data; every page still needs QA.
    """
    tree=ET.fromstring(bbox_xml)
    lines=[]
    for element in tree.iter():
        if element.tag.rsplit('}',1)[-1]!='line':continue
        words=[word for word in element if word.tag.rsplit('}',1)[-1]=='word']
        if words:lines.append((' '.join((w.text or '') for w in words),words))
    width,height=effective;result=[]
    for label in labels:
        matches=[(text,words) for text,words in lines if label in text]
        if len(matches)!=1:raise ValueError('Compact label missing or repeated in PDF: '+label)
        text,words=matches[0]
        # Check just the label's words when Poppler groups unrelated text on one line.
        joined=' '.join(w.text or '' for w in words);start=joined.index(label);finish=start+len(label)
        positions=[];offset=0
        for word in words:
            token=word.text or ''
            if offset<finish and offset+len(token)>start:positions.append(word)
            offset+=len(token)+1
        box=(min(float(w.attrib['xMin']) for w in positions),min(float(w.attrib['yMin']) for w in positions),
             max(float(w.attrib['xMax']) for w in positions),max(float(w.attrib['yMax']) for w in positions))
        tol=.012
        if box[0]/width<layout['left_margin']-tol or box[2]/width>1-layout['right_margin']+tol or box[1]/height<layout['top_margin']-tol or box[3]/height>1-layout['bottom_margin']+tol:
            raise ValueError('Compact annotation lies outside plotting frame: '+label)
        result.append({'label':label,'box_points':box})
    return result

def validate_one(sidecar,render_directory=None):
    import ROOT
    sidecar=Path(sidecar);base=Path(str(sidecar).removesuffix('.plot.json'));m=json.loads(sidecar.read_text())
    required=['standard','root_version','style','sample_kind','record','period','selection','unit_status','weighting','inspected','accepted','start','end','canvas_width','canvas_height','caption','layout','energy_tev','luminosity_pb','luminosity_validated','luminosity_evidence']
    if any(k not in m for k in required):raise ValueError('Required plot metadata missing')
    if m['standard']!=STANDARD or m['root_version']!='6.40.04' or m['style']!='ATLAS':raise ValueError('Wrong plotting backend/version')
    if m['sample_kind'] not in ['DATA','MC','SYNTHETIC'] or m['unit_status'] not in ['VERIFIED','PROVISIONAL']:raise ValueError('Unknown scientific metadata')
    for k in ['record','period','selection','weighting']:
        if not isinstance(m[k],str) or not m[k].strip():raise ValueError('Required metadata empty')
        if any(forbidden.lower() in m[k].lower() for forbidden in OFFICIAL_LABELS):raise ValueError('Forbidden official-status metadata')
    if m['weighting']!='Raw unweighted counts':raise ValueError('Unvalidated weighting')
    if any(type(m[k]) is not int or m[k]<0 for k in ['accepted','inspected','start','end','canvas_width','canvas_height']):raise ValueError('Invalid integer metadata')
    if not (0<=m['accepted']<=m['inspected'] and m['inspected']>0 and m['end']-m['start']==m['inspected'] and m['canvas_width']>0 and m['canvas_height']>0):raise ValueError('Invalid event range/count')
    def positive_number(value):return type(value) in [int,float] and math.isfinite(value) and value>0
    if m['sample_kind']!='SYNTHETIC' and not positive_number(m.get('energy_tev')):raise ValueError('Collision energy missing')
    if m.get('energy_tev') is not None and not positive_number(m['energy_tev']):raise ValueError('Invalid collision energy')
    if m.get('luminosity_pb') is not None and (m.get('luminosity_validated') is not True or not isinstance(m.get('luminosity_evidence'),str) or not m['luminosity_evidence'].strip() or m['sample_kind']=='SYNTHETIC' or not positive_number(m['luminosity_pb'])):raise ValueError('Unvalidated luminosity')
    if (m['canvas_width'],m['canvas_height'])!=(800,600):raise ValueError('Expected actual 800 x 600 canvas')
    validate_layout(m['layout'])
    validate_caption(m,Path(str(base)+'.caption.md'))
    files={ext:Path(str(base)+ext) for ext in ['.pdf','.png','.root']}
    if any(not p.is_file() or p.stat().st_size==0 for p in files.values()):raise ValueError('Missing PDF/PNG/native ROOT object')
    if not files['.pdf'].read_bytes().startswith(b'%PDF-'):raise ValueError('Invalid PDF signature')
    png=files['.png'].read_bytes()
    if png[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid PNG preview')
    png_size=struct.unpack('>II',png[16:24])
    if png_size!=(m['canvas_width'],m['canvas_height']):raise ValueError('Preview/canvas dimensions disagree')
    # IHDR alone cannot prove that a preview is readable: a 24-byte truncated
    # PNG still carries the signature and the expected dimensions. Decode it
    # with ROOT's existing image backend, without adding an authoring backend.
    try:
        decoded=ROOT.TImage.Open(str(files['.png']))
        if not decoded or (int(decoded.GetWidth()),int(decoded.GetHeight()))!=png_size or not decoded.GetArgbArray():
            raise ValueError('PNG preview cannot be decoded')
    except Exception as error:
        raise ValueError('PNG preview cannot be decoded') from error
    info=command('pdfinfo','-box',str(files['.pdf']))
    if not re.search(r'Pages:\s+1\b',info):raise ValueError('Expected exactly one page')
    size=re.search(r'Page size:\s+([\d.]+) x ([\d.]+) pts',info)
    if not size:raise ValueError('Page dimensions unavailable')
    dimensions=tuple(map(float,size.groups()))
    if not all(300<v<1200 for v in dimensions):raise ValueError('Unexpected page dimensions')
    rotation=int(re.search(r'Page rot:\s+(\d+)',info).group(1))
    if rotation not in [0,90,180,270]:raise ValueError('Unexpected page rotation')
    effective=dimensions[::-1] if rotation in [90,270] else dimensions
    if abs(effective[0]/effective[1]-m['canvas_width']/m['canvas_height'])>.015:raise ValueError('PDF CropBox/canvas aspect ratio disagree')
    fonts=command('pdffonts',str(files['.pdf']))
    if 'Helvetica' not in fonts:raise ValueError('Helvetica-compatible text font missing')
    images=command('pdfimages','-list',str(files['.pdf'])).splitlines()[2:]
    if any(line.strip() for line in images):raise ValueError('Raster image embedded in required vector figure')
    text=command('pdftotext','-cropbox','-layout',str(files['.pdf']),'-')
    normalized=' '.join(text.split());expected=compact_labels(m)
    for needle in expected:
        if needle not in normalized:raise ValueError('Compact scientific label missing in PDF: '+needle)
    for forbidden in OFFICIAL_LABELS:
        if forbidden.lower() in text.lower():raise ValueError('Forbidden official-status label')
    for forbidden in VISIBLE_DIAGNOSTICS:
        if forbidden.lower() in normalized.lower():raise ValueError('Diagnostic header/footer visible in publication figure: '+forbidden)
    boxes=annotation_boxes(command('pdftotext','-cropbox','-bbox-layout',str(files['.pdf']),'-'),expected,m['layout'],effective)
    with ROOT.TFile.Open(str(files['.root']),'READ') as root:
        if not root or root.IsZombie():raise ValueError('Unreadable ROOT object file')
        metadata=root.Get('atlas_plot_metadata')
        if not metadata or json.loads(metadata.GetTitle())!=m:raise ValueError('ROOT/sidecar metadata disagree')
        caption=root.Get('atlas_plot_caption')
        if not caption or caption.GetTitle()!=m['caption']:raise ValueError('ROOT/sidecar caption disagree')
        objects=[root.Get(k.GetName()) for k in root.GetListOfKeys() if k.GetName() not in ['atlas_plot_metadata','atlas_plot_caption']]
        if not any(o.InheritsFrom('TH1') or o.InheritsFrom('TGraph') for o in objects):raise ValueError('Native scientific object absent')
        native=root.Get(base.name)
        if not native:raise ValueError('Named source object absent')
        axes=native if native.InheritsFrom('TH1') else native.GetHistogram()
        if not axes.GetXaxis().GetTitle() or not axes.GetYaxis().GetTitle():raise ValueError('Native axis titles missing')
        for axis in [axes.GetXaxis(),axes.GetYaxis()]:
            if axis.GetLabelFont()!=42 or axis.GetTitleFont()!=42 or abs(axis.GetLabelSize()-.045)>1e-6 or abs(axis.GetTitleSize()-.05)>1e-6:
                raise ValueError('Native publication axis typography mismatch')
    with tempfile.TemporaryDirectory() as temp:
        prefix=Path(temp)/'page';subprocess.run(['pdftoppm','-cropbox','-r','75','-singlefile',str(files['.pdf']),str(prefix)],check=True,capture_output=True)
        render=ppm_pixels(prefix.with_suffix('.ppm').read_bytes())
    rendered_path=None
    if render_directory:
        target=Path(render_directory);target.mkdir(parents=True,exist_ok=True)
        prefix=target/(base.name+'_'+hashlib.sha256(str(base).encode()).hexdigest()[:8])
        subprocess.run(['pdftoppm','-cropbox','-r','120','-singlefile','-png',str(files['.pdf']),str(prefix)],check=True,capture_output=True)
        rendered_path=str(prefix)+'.png'
    return {'plot':str(base),'pages':1,'page_points':dimensions,'page_rotation':rotation,'effective_crop_points':effective,'png_pixels':png_size,'font_report':fonts,
            'standard':STANDARD,'compact_annotation_boxes':boxes,'caption_preservation':'PASS','layout':m['layout'],
            'png_decode':'PASS','vector_no_raster_images':True,'render_pixels':render[:2],'nonwhite_pixels':render[2],
            'plot_interior_pixels':render[3],'rendered_png':rendered_path,'automated_status':'PASS','visual_status':'REQUIRES_HUMAN_INSPECTION'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--expected-count',type=int);parser.add_argument('--render-dir',type=Path);parser.add_argument('--report',type=Path)
    args=parser.parse_args();sidecars=sorted(args.directory.rglob('*.plot.json'))
    pdfs=sorted(args.directory.rglob('*.pdf'))
    if not sidecars or len(pdfs)!=len(sidecars) or (args.expected_count is not None and len(sidecars)!=args.expected_count):raise ValueError('Missing required PDFs or sidecars')
    result=[validate_one(p,args.render_dir) for p in sidecars]
    if args.report:args.report.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS PDF/PNG/ROOT automated quality gates:',len(result),'plots; visual review remains required')
if __name__=='__main__':main()
