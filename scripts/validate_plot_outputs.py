"""Fail closed on missing PDFs/metadata/objects; Poppler renders and checks each PDF.

Automated checks complement mandatory human inspection of every rendered page.
No PDFs are created by this script; scientific authoring is native ROOT/C++.
"""
import argparse,hashlib,json,math,re,struct,subprocess,tempfile
from pathlib import Path

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
                if .17*width<x<.93*width and .30*height<y<.73*height:interior+=1
    if total<1000 or interior<30:raise ValueError('Blank or malformed canvas/render')
    return width,height,total,interior

def validate_one(sidecar,render_directory=None):
    import ROOT
    sidecar=Path(sidecar);base=Path(str(sidecar).removesuffix('.plot.json'));m=json.loads(sidecar.read_text())
    required=['standard','root_version','style','sample_kind','record','period','selection','unit_status','weighting','inspected','accepted','start','end','canvas_width','canvas_height']
    if any(k not in m for k in required):raise ValueError('Required plot metadata missing')
    if m['standard']!='atlas-root-plot-v1' or m['root_version']!='6.40.04' or m['style']!='ATLAS':raise ValueError('Wrong plotting backend/version')
    if m['sample_kind'] not in ['DATA','MC','SYNTHETIC'] or m['unit_status'] not in ['VERIFIED','PROVISIONAL']:raise ValueError('Unknown scientific metadata')
    for k in ['record','period','selection','weighting']:
        if not isinstance(m[k],str) or not m[k].strip():raise ValueError('Required metadata empty')
    if m['weighting']!='Raw unweighted counts':raise ValueError('Unvalidated weighting')
    if any(type(m[k]) is not int or m[k]<0 for k in ['accepted','inspected','start','end','canvas_width','canvas_height']):raise ValueError('Invalid integer metadata')
    if not (0<=m['accepted']<=m['inspected'] and m['inspected']>0 and m['end']-m['start']==m['inspected'] and m['canvas_width']>0 and m['canvas_height']>0):raise ValueError('Invalid event range/count')
    def positive_number(value):return type(value) in [int,float] and math.isfinite(value) and value>0
    if m['sample_kind']!='SYNTHETIC' and not positive_number(m.get('energy_tev')):raise ValueError('Collision energy missing')
    if m.get('energy_tev') is not None and not positive_number(m['energy_tev']):raise ValueError('Invalid collision energy')
    if m.get('luminosity_pb') is not None and (m.get('luminosity_validated') is not True or not isinstance(m.get('luminosity_evidence'),str) or not m['luminosity_evidence'].strip() or m['sample_kind']=='SYNTHETIC' or not positive_number(m['luminosity_pb'])):raise ValueError('Unvalidated luminosity')
    files={ext:Path(str(base)+ext) for ext in ['.pdf','.png','.root']}
    if any(not p.is_file() or p.stat().st_size==0 for p in files.values()):raise ValueError('Missing PDF/PNG/native ROOT object')
    if not files['.pdf'].read_bytes().startswith(b'%PDF-'):raise ValueError('Invalid PDF signature')
    png=files['.png'].read_bytes()
    if png[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid PNG preview')
    png_size=struct.unpack('>II',png[16:24])
    if png_size!=(m['canvas_width'],m['canvas_height']):raise ValueError('Preview/canvas dimensions disagree')
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
    expected=['Synthetic test','Independent numerical validation'] if m['sample_kind']=='SYNTHETIC' else ['ATLAS Open Data','Independent exploratory analysis']
    for needle in expected+['Record '+m['record'],m['period'],m['unit_status'],m['selection'],'Inspected '+str(m['inspected']),'accepted '+str(m['accepted']),m['weighting']]:
        if needle not in text:raise ValueError('Required metadata not visible in PDF: '+needle)
    for forbidden in ['ATLAS Preliminary','ATLAS Internal','ATLAS Official','ATLAS Simulation Preliminary']:
        if forbidden.lower() in text.lower():raise ValueError('Forbidden official-status label')
    with ROOT.TFile.Open(str(files['.root']),'READ') as root:
        if not root or root.IsZombie():raise ValueError('Unreadable ROOT object file')
        metadata=root.Get('atlas_plot_metadata')
        if not metadata or json.loads(metadata.GetTitle())!=m:raise ValueError('ROOT/sidecar metadata disagree')
        objects=[root.Get(k.GetName()) for k in root.GetListOfKeys() if k.GetName()!='atlas_plot_metadata']
        if not any(o.InheritsFrom('TH1') or o.InheritsFrom('TGraph') for o in objects):raise ValueError('Native scientific object absent')
        native=root.Get(base.name)
        if not native:raise ValueError('Named source object absent')
        axes=native if native.InheritsFrom('TH1') else native.GetHistogram()
        if not axes.GetXaxis().GetTitle() or not axes.GetYaxis().GetTitle():raise ValueError('Native axis titles missing')
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
            'vector_no_raster_images':True,'render_pixels':render[:2],'nonwhite_pixels':render[2],
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
