#!/usr/bin/env python3
"""Remove ROOT paper whitespace without altering vector drawing streams or data.

Uses an existing pypdf installation and Poppler. Rasterization only determines
page bounds; scientific content stays vector and byte-identical after decoding.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ppm_bounds(raw):
    index=0;tokens=[]
    while len(tokens)<4:
        while raw[index:index+1].isspace():index+=1
        if raw[index:index+1]==b'#':index=raw.index(b'\n',index)+1;continue
        end=index
        while not raw[end:end+1].isspace():end+=1
        tokens.append(raw[index:end]);index=end
    if tokens[0]!=b'P6' or tokens[3]!=b'255':raise ValueError('EXPECTED_POPPLER_BINARY_RGB_PPM')
    if raw[index:index+2]==b'\r\n':index+=2
    else:index+=1
    width,height=map(int,tokens[1:3]);pixels=raw[index:]
    if len(pixels)!=width*height*3:raise ValueError('INCOMPLETE_PPM')
    left=width;right=-1;top=height;bottom=-1
    for y in range(height):
        for x in range(width):
            k=(y*width+x)*3
            if min(pixels[k:k+3])<248:left=min(left,x);right=max(right,x);top=min(top,y);bottom=max(bottom,y)
    if right<left:raise ValueError('EMPTY_ROOT_PDF_PAGE')
    pad=16
    return width,height,(max(0,left-pad),max(0,top-pad),min(width,right+pad+1),min(height,bottom+pad+1))

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pypdf-path',type=Path);a=p.parse_args()
    if a.pypdf_path:sys.path.insert(0,str(a.pypdf_path))
    from pypdf import PdfReader,PdfWriter
    from pypdf.generic import RectangleObject
    if a.output.exists():raise ValueError('REFUSE_FIGURE_VERSION_OVERWRITE')
    a.output.mkdir();manifest=json.loads((a.source/'phase9_plot_manifest.json').read_text());source_manifest_sha=sha(a.source/'phase9_plot_manifest.json')
    if manifest['figure_count']!=12:raise ValueError('EXACT_TWELVE_REQUIRED')
    for row in manifest['figures']:
        source=Path(row['pdf']);target=a.output/source.name
        if sha(source)!=row['pdf_sha256']:raise ValueError('ROOT_PDF_SOURCE_CHANGED')
        reader=PdfReader(source)
        if len(reader.pages)!=1 or reader.pages[0].rotation!=0:raise ValueError('ONE_UNROTATED_PAGE_REQUIRED')
        page=reader.pages[0];before=hashlib.sha256(page.get_contents().get_data()).hexdigest();old=list(map(float,page.mediabox))
        raw=subprocess.check_output(['/usr/bin/pdftoppm','-scale-to','1400','-singlefile',str(source)],timeout=30)
        w,h,(l,t,r,b)=ppm_bounds(raw);pw=old[2]-old[0];ph=old[3]-old[1];box=[old[0]+l/w*pw,old[1]+(h-b)/h*ph,old[0]+r/w*pw,old[1]+(h-t)/h*ph]
        page.mediabox=RectangleObject(box);page.cropbox=RectangleObject(box);writer=PdfWriter();writer.add_page(page);writer.add_metadata({'/Title':row['figure_id'],'/Producer':'CERN ROOT 6.40.04 drawing; pypdf whitespace-only page trim'})
        with target.open('xb') as f:writer.write(f)
        after=hashlib.sha256(PdfReader(target).pages[0].get_contents().get_data()).hexdigest()
        if before!=after:raise ValueError('SCIENTIFIC_DRAWING_STREAM_CHANGED')
        png=a.output/Path(row['png']).name;shutil.copyfile(row['png'],png)
        row['paper_trim']={'source_ROOT_PDF_sha256':row['pdf_sha256'],'source_media_box':old,'final_media_box':box,'decoded_vector_stream_sha256_before':before,'decoded_vector_stream_sha256_after':after,'data_or_drawing_changed':False,'raster_used_only_for_page_bounds':True}
        row.update(pdf=str(target),png=str(png),pdf_sha256=sha(target),png_sha256=sha(png),status='LOCAL_DRAFT')
    manifest.update(status='LOCAL_DRAFT',source_ROOT_manifest_sha256=source_manifest_sha,postprocessing='WHITESPACE_ONLY_PAGE_BOX_TRIM; CERN_ROOT_VECTOR_STREAM_UNCHANGED')
    (a.output/'phase9_plot_manifest.json').open('x').write(json.dumps(manifest,indent=2,allow_nan=False)+'\n');print(json.dumps({'status':'PASS_ROOT_VECTOR_PRESERVING_PDF_PAGE_TRIM','figures':12,'publication_authorized':False}))
if __name__=='__main__':main()