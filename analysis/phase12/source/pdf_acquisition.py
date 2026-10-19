"""One-candidate bounded HTTPS acquisition; never installs or dispatches generators."""
import hashlib,json,os,time,urllib.request
from pathlib import Path
SET='NNPDF30_lo_as_0130_nf_4'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError('UNKNOWN_REDIRECT_REJECTED')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def output_path(c):
 parent=Path(c['allowed_output_parent'])
 if os.name=='nt':parent=Path('\\\\wsl.localhost\\Ubuntu'+str(parent).replace('/','\\'))
 return parent/c['output_leaf']
def verify_output_parent(parent):
 parent=Path(parent)
 require(parent.is_absolute() and '..' not in parent.parts,'UNSAFE_OUTPUT_PARENT')
 require(parent.exists() and parent.is_dir(),'OUTPUT_PARENT_MISSING_OR_NOT_DIRECTORY')
 require(not any(p.is_symlink() for p in (parent,*parent.parents)),'SYMLINK_OUTPUT_PARENT_FORBIDDEN')
 require(parent.resolve()==parent.absolute(),'RESOLVED_OUTPUT_PARENT_DRIFT')
 return parent
def validate_contract(c):
 require(c['candidate']==SET and type(c['member']) is int and c['member']==0 and c['LHAPDF_ID']==263400,'ONE_EXACT_CANDIDATE')
 require(type(c.get('timeout_seconds')) is int and c['timeout_seconds']==20 and type(c.get('total_wall_seconds')) is int and c['total_wall_seconds']==120,'FINITE_REVIEWED_TIMEOUTS')
 require(c['aggregate_HTTP_body_budget']==134217728 and c['single_payload_budget']==83886080 and c['maximum_selected_distributions']==1,'NETWORK_LIMITS')
 require(c['allowed_output_parent']=='/home/btu/simulations/hh_phase12/run_01' and c['output_leaf']=='public_pdf_01','UNEXPECTED_INSTALLED_PATH_WRITE')
 require(c['official_base']==f'https://lhapdfsets.web.cern.ch/current/{SET}/','UNREVIEWED_SOURCE_URL')
 require(c['terms_review']['checked'] is True and c['terms_review']['public_download_and_scientific_use_documented'] is True and c['terms_review']['redistribution_permission_claimed'] is False,'TERMS_NOT_REVIEWED')
 require(c['install_into_existing_directories'] is False and c['MG5_import_or_execution'] is False and c['physical_authorization'] is False,'EXECUTION_OR_INSTALL_FORBIDDEN')
 return True
def advertised_length(headers,limit):
 value=headers.get('Content-Length');require(isinstance(value,str) and value.isdigit(),'UNKNOWN_LENGTH_REJECTED');n=int(value);require(0<n<=limit,'OVERSIZE_PAYLOAD');require(headers.get('Content-Encoding','identity')=='identity','ENCODING_REJECTED');return n
def exact_complete(raw_count,expected):require(raw_count==expected,'PARTIAL_OR_BROKEN_DOWNLOAD')
def acquire(c):
 validate_contract(c);out=output_path(c);verify_output_parent(out.parent);require(not out.exists() and not out.is_symlink(),'FRESH_OUTPUT_REQUIRED');out.mkdir();folder=out/SET;folder.mkdir();ledger=out/'acquisition_receipt.json';start=time.monotonic();opener=urllib.request.build_opener(NoRedirect());rows=[];total=0
 receipt={'evidence_class':'PUBLIC_SOURCE_AUDIT','status':'IN_PROGRESS','candidate':SET,'member':0,'maximum_selected_distributions':1,'aggregate_body_bytes':0,'aggregate_body_budget':c['aggregate_HTTP_body_budget'],'single_payload_budget':c['single_payload_budget'],'TLS_certificate_verification':True,'unknown_redirects_allowed':False,'publisher_checksum':None,'publisher_payload_signature_or_checksum_authenticity':'NOT_CRYPTOGRAPHICALLY_ESTABLISHED','files':rows,'installed_path_writes':False,'physical_generation':False}
 def save():ledger.write_text(json.dumps(receipt,indent=2)+'\n')
 save()
 try:
  for role,name in [('info',SET+'.info'),('member',SET+'_0000.dat')]:
   url=c['official_base']+name;req=urllib.request.Request(url,method='HEAD',headers={'Accept-Encoding':'identity'})
   with opener.open(req,timeout=c['timeout_seconds']) as response:
    require(response.status==200 and response.url==url,'SOURCE_OR_HTTP_STATUS');expected=advertised_length(response.headers,c['single_payload_budget'])
   require(total+expected<=c['aggregate_HTTP_body_budget'],'AGGREGATE_NETWORK_BUDGET');part=folder/(name+'.part');digest=hashlib.sha256();count=0;record={'role':role,'relative_path':SET+'/'+name,'source_URL':url,'advertised_bytes':expected,'received_bytes':0,'status':'IN_PROGRESS'};rows.append(record);save()
   with opener.open(urllib.request.Request(url,headers={'Accept-Encoding':'identity'}),timeout=c['timeout_seconds']) as response,part.open('xb') as stream:
    require(response.status==200 and response.url==url,'SOURCE_OR_HTTP_STATUS');require(advertised_length(response.headers,c['single_payload_budget'])==expected,'HEAD_GET_LENGTH_MISMATCH')
    while count<expected:
     require(time.monotonic()-start<c['total_wall_seconds'],'ACQUISITION_WALL_LIMIT');chunk=response.read(min(65536,expected-count))
     if not chunk:break
     count+=len(chunk);total+=len(chunk);require(total<=c['aggregate_HTTP_body_budget'] and count<=c['single_payload_budget'],'NETWORK_BODY_LIMIT');stream.write(chunk);digest.update(chunk);record['received_bytes']=count;receipt['aggregate_body_bytes']=total;save()
   exact_complete(count,expected);raw=part.read_bytes();text=raw.decode('utf-8');require('<html' not in text[:200].lower(),'HTML_NOT_PDF_PAYLOAD')
   require(('SetIndex:' in text and 'AlphaS_MZ:' in text) if role=='info' else ('Format: lhagrid1' in text[:200] and text.rstrip().endswith('---')),'BROKEN_MEMBER_OR_INFO_FORMAT')
   final=folder/name;require(not final.exists(),'NO_OVERWRITE');part.rename(final);record.update(status='PASS_COMPLETE_PAYLOAD',bytes=count,sha256=digest.hexdigest());save()
  receipt.update(status='PASS_COMPLETE_SELECTED_MEMBER_ACQUISITION',wall_seconds=time.monotonic()-start,selected_member_only_not_all101=True);save();return receipt
 except Exception as error:
  receipt.update(status='FAILED_ACQUISITION_STOPPED_NO_RETRY',error_type=type(error).__name__,error=str(error),wall_seconds=time.monotonic()-start);save();raise
