"""Fail closed on missing PDFs/metadata/objects; Poppler renders and checks each PDF.

Automated checks complement mandatory human inspection of every rendered page.
No PDFs are created by this script; scientific authoring is native ROOT/C++.
"""
import argparse,hashlib,json,math,re,struct,subprocess,tempfile,zlib
from contextlib import contextmanager
import xml.etree.ElementTree as ET
from pathlib import Path

STANDARD='atlas-root-plot-v2'
OFFICIAL_LABELS=['ATLAS Preliminary','ATLAS Internal','ATLAS Official','ATLAS Simulation Preliminary']
VISIBLE_DIAGNOSTICS=['Inspected','Accepted','Entries [','Selection:','Units:','Record ',
                     'Raw unweighted counts','raw unweighted GamGam skim',
                     'not the official ATLAS HH analysis','Independent exploratory analysis',
                     'Independent numerical validation','Independent work;']
HATCHED_FIELDS=['source_object_name','source_intervals_object_name','band_object_name',
                'confidence_level','statistical_model','eligible_bin_indices',
                'structural_zero_exclusions','band_support','hatched_style']

@contextmanager
def native_serialization_style():
    """Read stored native styles without ROOT replacing them with current gStyle."""
    import ROOT
    previous=bool(ROOT.gROOT.GetForceStyle());ROOT.gROOT.ForceStyle(False)
    try:yield
    finally:ROOT.gROOT.ForceStyle(previous)

def fixture_directory(directory,marker):
    """Select a complete successful test run while preserving failed historical runs.

    This is opt-in for generated regression fixtures. Production directories
    retain the default exhaustive PDF/sidecar validation behavior.
    """
    directory=Path(directory).resolve();marker=Path(marker)
    if not marker.is_file():raise ValueError('Successful fixture marker missing')
    lines=marker.read_text().splitlines()
    if len(lines)!=1 or not lines[0].strip():raise ValueError('Invalid successful fixture marker')
    selected=Path(lines[0]).resolve()
    if not selected.is_relative_to(directory) or selected==directory:raise ValueError('Fixture marker escapes dedicated output directory')
    if not selected.is_dir():raise ValueError('Marked successful fixture directory absent')
    return selected

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
    period=m['hatched_style']['visible_period'] if m.get('plot_mode')=='HATCHED_STEP' else year.group(0)
    period_label=period if m.get('plot_mode')=='HATCHED_STEP' else period+' '+kind
    return ['ATLAS Open Data',f"{m['energy_tev']:g} TeV",period_label,
            'Exploratory, provisional' if m['unit_status']=='PROVISIONAL' else 'Exploratory, verified']

def validate_plot_mode(m):
    mode=m.get('plot_mode','ORIGINAL')
    if mode not in ['ORIGINAL','HATCHED_STEP']:raise ValueError('Unknown plot mode')
    if mode=='ORIGINAL':
        if any(key in m for key in HATCHED_FIELDS):raise ValueError('Original mode cannot masquerade as a hatched plot')
        return mode
    if any(key not in m for key in HATCHED_FIELDS):raise ValueError('Required hatched metadata missing')
    if m['sample_kind'] not in ['DATA','SYNTHETIC']:raise ValueError('Hatched count band cannot represent MC')
    for key in ['source_object_name','source_intervals_object_name','band_object_name']:
        if not isinstance(m[key],str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',m[key]):
            raise ValueError('Invalid native hatched object name')
    if m['source_intervals_object_name']!=m['source_object_name']+'_display' or m['band_object_name']!=m['source_object_name']+'_hatched_band':
        raise ValueError('Hatched native object names disagree')
    confidence=m['confidence_level']
    if type(confidence) not in [int,float] or not math.isfinite(confidence) or abs(confidence-.682689492137)>1e-14 or m['statistical_model']!='central Garwood Poisson':
        raise ValueError('Unvalidated hatched statistical model')
    style=m['hatched_style']
    required=['line_color','line_width','band_color','band_fill_style','band_draw_option',
              'line_draw_option','legend_labels','legend_box','annotation_box','y_headroom_factor','visible_period']
    if not isinstance(style,dict) or any(key not in style for key in required):raise ValueError('Required hatched style metadata missing')
    for key,expected in [('line_color',862),('line_width',2),('band_color',861),('band_fill_style',3354),
                         ('band_draw_option','2 SAME'),('line_draw_option','HIST SAME')]:
        if type(style[key]) is not type(expected) or style[key]!=expected:raise ValueError('Wrong hatched style: '+key)
    labels=['Data (step histogram)' if m['sample_kind']=='DATA' else 'Synthetic counts (step histogram)',
            '68.27% Poisson statistical interval']
    if style['legend_labels']!=labels:raise ValueError('Hatched legend misstates statistical meaning')
    expected_period='2015 Period D' if m['period']=='2015 periodD' else m['period']
    if m['sample_kind']=='DATA' and style['visible_period']!=expected_period:raise ValueError('Hatched visible period disagrees with provenance')
    if type(style['y_headroom_factor']) not in [int,float] or not math.isfinite(style['y_headroom_factor']) or style['y_headroom_factor']<1:
        raise ValueError('Invalid hatched y-axis headroom')
    boxes=[]
    for key in ['legend_box','annotation_box']:
        box=style[key]
        if not isinstance(box,list) or len(box)!=4 or any(type(value) not in [int,float] or not math.isfinite(value) for value in box):
            raise ValueError('Invalid hatched '+key)
        x1,y1,x2,y2=box
        if not (.16<=x1<x2<=.95 and .16<=y1<y2<=.95):raise ValueError('Hatched annotation/legend outside plotting frame')
        boxes.append(box)
    a,b=boxes
    if min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1]):raise ValueError('Hatched legend overlaps annotation')
    caption=m['caption'].lower()
    if not all(phrase in caption for phrase in ['poisson','garwood','statistical']) or not re.search(r'\bno\b[^.\n;]*\bsystematics\b',caption):
        raise ValueError('Hatched caption missing statistical scope')
    if 'mc uncertainty' in caption or 'systematic uncertainty band' in caption:
        raise ValueError('Hatched caption misstates count uncertainty')
    return mode

def validate_hatched_numerics(root,native,m):
    """Validate native rectangles against an independent ROOT kPoisson oracle."""
    import ROOT
    if native.ClassName()!='TH1D' or native.GetDimension()!=1:raise ValueError('Hatched source must be a native 1D TH1D')
    style=m['hatched_style']
    if native.GetLineColor()!=style['line_color'] or native.GetLineWidth()!=style['line_width']:
        raise ValueError('Native hatched step style disagrees')
    count=native.GetNbinsX();axis=native.GetXaxis()
    eligible=m['eligible_bin_indices'];excluded=m['structural_zero_exclusions']
    for name,mask in [('eligible',eligible),('excluded',excluded)]:
        if not isinstance(mask,list) or any(type(index) is not int or not 1<=index<=count for index in mask) or mask!=sorted(set(mask)):
            raise ValueError('Invalid or duplicate hatched '+name+' bin mask')
    support=m['band_support']
    if support is None:expected=list(range(1,count+1))
    else:
        if not isinstance(support,dict) or set(support)!= {'low','high'} or any(type(support[key]) not in [int,float] or not math.isfinite(support[key]) for key in support):
            raise ValueError('Invalid hatched support')
        low,high=support['low'],support['high']
        edges=[axis.GetBinLowEdge(index) for index in range(1,count+2)]
        if not edges[0]<=low<high<=edges[-1] or not any(abs(low-edge)<1e-10 for edge in edges) or not any(abs(high-edge)<1e-10 for edge in edges):
            raise ValueError('Hatched support is not aligned to source bin edges')
        expected=[index for index in range(1,count+1) if axis.GetBinLowEdge(index)>=low-1e-10 and axis.GetBinUpEdge(index)<=high+1e-10]
    complement=[index for index in range(1,count+1) if index not in expected]
    if not eligible or eligible!=expected or excluded!=complement:raise ValueError('Hatched mask does not match physical support')
    if any(native.GetBinContent(index)!=0 for index in excluded):raise ValueError('Excluded hatched bin contains events')
    for index in range(native.GetNcells()):
        value=native.GetBinContent(index)
        if not math.isfinite(value) or value<0 or value!=round(value):raise ValueError('Hatched source is not raw nonnegative integer counts')
    if native.GetSumw2N() and any(not math.isclose(native.GetSumw2().At(index),native.GetBinContent(index),rel_tol=1e-12,abs_tol=1e-10) for index in range(native.GetNcells())):
        raise ValueError('Weighted native histogram cannot represent raw Poisson counts')
    source=root.Get(m['source_intervals_object_name']);band=root.Get(m['band_object_name'])
    if not source or source.ClassName()!='TGraphAsymmErrors' or source.GetN()!=count:raise ValueError('Full native counting intervals absent')
    if not band or band.ClassName()!='TGraphAsymmErrors' or band.GetN()!=len(eligible):raise ValueError('Missing or duplicate hatched band bins')
    if band.GetFillStyle()!=style['band_fill_style'] or band.GetFillColor()!=style['band_color'] or band.GetLineColor()!=style['band_color']:
        raise ValueError('Native band is not the declared colored hatched style')
    oracle=native.Clone('hatched_gate_poisson_oracle');oracle.SetDirectory(0);oracle.SetBinErrorOption(ROOT.TH1.kPoisson)
    def same(a,b):return math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-7)
    for index in range(1,count+1):
        position=index-1;value=native.GetBinContent(index)
        if not math.isfinite(value) or value<0 or value!=round(value):raise ValueError('Hatched source is not raw nonnegative integer counts')
        expected_values=[axis.GetBinCenter(index),value,0.,0.,oracle.GetBinErrorLow(index),oracle.GetBinErrorUp(index)]
        values=[source.GetPointX(position),source.GetPointY(position),source.GetErrorXlow(position),source.GetErrorXhigh(position),source.GetErrorYlow(position),source.GetErrorYhigh(position)]
        if not all(same(a,b) for a,b in zip(values,expected_values)):raise ValueError('Full native Poisson counting intervals changed')
    regions=[];layout=m['layout'];y_max=native.GetMaximum()
    if not math.isfinite(y_max) or y_max<=0:raise ValueError('Invalid hatched display y maximum')
    def ndc_x(value):return layout['left_margin']+(value-axis.GetXmin())/(axis.GetXmax()-axis.GetXmin())*(1-layout['left_margin']-layout['right_margin'])
    def ndc_y(value):return layout['bottom_margin']+max(0.,value)/y_max*(1-layout['bottom_margin']-layout['top_margin'])
    for position,index in enumerate(eligible):
        value=native.GetBinContent(index);half=axis.GetBinWidth(index)/2
        expected_values=[axis.GetBinCenter(index),value,half,half,source.GetErrorYlow(index-1),source.GetErrorYhigh(index-1)]
        values=[band.GetPointX(position),band.GetPointY(position),band.GetErrorXlow(position),band.GetErrorXhigh(position),band.GetErrorYlow(position),band.GetErrorYhigh(position)]
        if not all(same(a,b) for a,b in zip(values,expected_values)):raise ValueError('Hatched rectangle coverage or Poisson errors changed')
        if band.GetPointY(position)-band.GetErrorYlow(position)<-1e-7:raise ValueError('Hatched rectangle has a negative count boundary')
        regions.append((ndc_x(axis.GetBinLowEdge(index)),ndc_y(value-band.GetErrorYlow(position)),
                        ndc_x(axis.GetBinUpEdge(index)),ndc_y(value+band.GetErrorYhigh(position))))
    return {'bins':count,'eligible_bins':len(eligible),'excluded_zero_bins':len(excluded),'native_poisson_oracle':'PASS','full_bin_rectangles':'PASS','hatch_regions_ndc':regions}

def pdf_hatch_paths(path,band_rgb,band_regions=None):
    """Count colored diagonal paths in the actual ROOT PDF page content.

    ROOT emits unused pattern resources even in plain plots. Inspecting resource
    presence would be a false positive, so only Page/Contents objects are audited.
    This is a bounded ROOT PDF check, not a replacement for rendered visual QA.
    """
    data=Path(path).read_bytes();objects={int(number):body for number,body in re.findall(rb'(?ms)^(\d+)\s+\d+\s+obj\s*(.*?)\s*endobj',data)}
    content_ids=[]
    for body in objects.values():
        if re.search(rb'/Type\s*/Page\b',body):
            match=re.search(rb'/Contents\s*(\[[^]]+\]|\d+\s+\d+\s+R)',body)
            if match:content_ids.extend(int(number) for number in re.findall(rb'(\d+)\s+\d+\s+R',match.group(1)))
    if not content_ids:raise ValueError('Native PDF page content cannot be inspected')
    diagonal=0
    token_pattern=r'\((?:\\.|[^\\)])*\)|<[^>]*>|/[^\s<>\[\]()]+|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?|[A-Za-z][A-Za-z*]*'
    for ident in content_ids:
        body=objects.get(ident,b'');match=re.search(rb'stream\r?\n(.*?)\r?\nendstream',body,re.S)
        if not match:raise ValueError('Native PDF content stream missing')
        stream=match.group(1)
        if b'/FlateDecode' in body[:match.start()]:stream=zlib.decompress(stream)
        text=re.sub(r'(?m)%[^\r\n]*','',stream.decode('latin1'));numbers=[];point=None;color=None;saved=[];pending=0;canvas=None
        for token in re.findall(token_pattern,text):
            try:numbers.append(float(token));continue
            except ValueError:pass
            if token in ['RG','rg'] and len(numbers)>=3:color=tuple(numbers[-3:])
            elif token=='q':saved.append(color)
            elif token=='Q':color=saved.pop() if saved else None
            elif token=='re' and len(numbers)>=4 and canvas is None and numbers[-4:-2]==[0.,0.] and all(value>300 for value in numbers[-2:]):canvas=tuple(numbers[-2:])
            elif token=='m' and len(numbers)>=2:point=tuple(numbers[-2:])
            elif token=='l' and len(numbers)>=2:
                destination=tuple(numbers[-2:])
                inside=True
                if band_regions is not None:
                    if canvas is None:raise ValueError('ROOT PDF canvas bounds unavailable for hatch proof')
                    x1,y1=point if point else (0,0);x2,y2=destination;cw,ch=canvas
                    inside=any(rx1-.001<=min(x1,x2)/cw and max(x1,x2)/cw<=rx2+.001 and ry1-.001<=min(y1,y2)/ch and max(y1,y2)/ch<=ry2+.001 for rx1,ry1,rx2,ry2 in band_regions)
                if point and color and inside and all(abs(a-b)<.005 for a,b in zip(color,band_rgb)) and abs(destination[0]-point[0])>.05 and abs(destination[1]-point[1])>.05:pending+=1
                point=destination
            elif token in ['S','s','f','f*','B','B*','b','b*']:diagonal+=pending;pending=0;point=None
            elif token=='n':pending=0;point=None
            numbers=[]
    if diagonal<4:raise ValueError('Required colored diagonal vector hatch paths absent')
    return diagonal

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
    mode=validate_plot_mode(m)
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
    legend_boxes=[];hatched_audit=None;hatch_paths=None
    if mode=='HATCHED_STEP':
        legend_boxes=annotation_boxes(command('pdftotext','-cropbox','-bbox-layout',str(files['.pdf']),'-'),m['hatched_style']['legend_labels'],m['layout'],effective)
        for label_boxes,key in [(boxes,'annotation_box'),(legend_boxes,'legend_box')]:
            x1,y1,x2,y2=m['hatched_style'][key]
            for item in label_boxes:
                bx1,by1,bx2,by2=item['box_points'];width,height=effective
                if bx1/width<x1-.012 or bx2/width>x2+.012 or 1-by2/height<y1-.012 or 1-by1/height>y2+.012:
                    raise ValueError('Visible hatched text disagrees with declared '+key)
    with native_serialization_style(),ROOT.TFile.Open(str(files['.root']),'READ') as root:
        if not root or root.IsZombie():raise ValueError('Unreadable ROOT object file')
        metadata=root.Get('atlas_plot_metadata')
        if not metadata or json.loads(metadata.GetTitle())!=m:raise ValueError('ROOT/sidecar metadata disagree')
        caption=root.Get('atlas_plot_caption')
        if not caption or caption.GetTitle()!=m['caption']:raise ValueError('ROOT/sidecar caption disagree')
        objects=[root.Get(k.GetName()) for k in root.GetListOfKeys() if k.GetName() not in ['atlas_plot_metadata','atlas_plot_caption']]
        if not any(o.InheritsFrom('TH1') or o.InheritsFrom('TGraph') for o in objects):raise ValueError('Native scientific object absent')
        native=root.Get(m['source_object_name'] if mode=='HATCHED_STEP' else base.name)
        if not native:raise ValueError('Named source object absent')
        axes=native if native.InheritsFrom('TH1') else native.GetHistogram()
        if not axes.GetXaxis().GetTitle() or not axes.GetYaxis().GetTitle():raise ValueError('Native axis titles missing')
        for axis in [axes.GetXaxis(),axes.GetYaxis()]:
            if axis.GetLabelFont()!=42 or axis.GetTitleFont()!=42 or abs(axis.GetLabelSize()-.045)>1e-6 or abs(axis.GetTitleSize()-.05)>1e-6:
                raise ValueError('Native publication axis typography mismatch')
        if mode=='HATCHED_STEP':
            hatched_audit=validate_hatched_numerics(root,native,m)
            color=ROOT.gROOT.GetColor(m['hatched_style']['band_color'])
            if not color:raise ValueError('Native band color unavailable')
            regions=hatched_audit.pop('hatch_regions_ndc')
            hatch_paths=pdf_hatch_paths(files['.pdf'],(color.GetRed(),color.GetGreen(),color.GetBlue()),regions)
    with tempfile.TemporaryDirectory() as temp:
        prefix=Path(temp)/'page';subprocess.run(['pdftoppm','-cropbox','-r','75','-singlefile',str(files['.pdf']),str(prefix)],check=True,capture_output=True)
        render=ppm_pixels(prefix.with_suffix('.ppm').read_bytes())
    rendered_path=None
    if render_directory:
        target=Path(render_directory);target.mkdir(parents=True,exist_ok=True)
        prefix=target/(base.name+'_'+hashlib.sha256(str(base).encode()).hexdigest()[:8])
        subprocess.run(['pdftoppm','-cropbox','-r','120','-singlefile','-png',str(files['.pdf']),str(prefix)],check=True,capture_output=True)
        rendered_path=str(prefix)+'.png'
    result={'plot':str(base),'pages':1,'page_points':dimensions,'page_rotation':rotation,'effective_crop_points':effective,'png_pixels':png_size,'font_report':fonts,
            'standard':STANDARD,'compact_annotation_boxes':boxes,'caption_preservation':'PASS','layout':m['layout'],
            'png_decode':'PASS','vector_no_raster_images':True,'render_pixels':render[:2],'nonwhite_pixels':render[2],
            'plot_interior_pixels':render[3],'rendered_png':rendered_path,'automated_status':'PASS','visual_status':'REQUIRES_HUMAN_INSPECTION'}
    if mode=='HATCHED_STEP':result.update({'plot_mode':mode,'hatched_numerics':hatched_audit,'legend_boxes':legend_boxes,'colored_diagonal_vector_paths':hatch_paths})
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--expected-count',type=int);parser.add_argument('--render-dir',type=Path);parser.add_argument('--report',type=Path);parser.add_argument('--fixture-marker',type=Path)
    args=parser.parse_args();directory=fixture_directory(args.directory,args.fixture_marker) if args.fixture_marker else args.directory
    sidecars=sorted(directory.rglob('*.plot.json'))
    pdfs=sorted(directory.rglob('*.pdf'))
    if not sidecars or len(pdfs)!=len(sidecars) or (args.expected_count is not None and len(sidecars)!=args.expected_count):raise ValueError('Missing required PDFs or sidecars')
    result=[validate_one(p,args.render_dir) for p in sidecars]
    if args.report:args.report.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS PDF/PNG/ROOT automated quality gates:',len(result),'plots; visual review remains required')
if __name__=='__main__':main()
