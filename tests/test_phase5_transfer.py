#!/usr/bin/env python3
"""Deterministic budget/identity/redirect checks; no network requests."""
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch,Mock
import urllib.error
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fetch_phase5_continuum as subject


def record():
    return {'metadata':{'recid':'93922','doi':'10.7483/OPENDATA.ATLAS.IMZO.7U52','_files':[
        {'key':subject.NAME,'size':subject.SIZE,'checksum':subject.CHECKSUM,
         'uri':'root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/'+subject.NAME}]}}


class Response:
    def __init__(self,body=b'',status=200,length=None):
        self.status=status;self.headers={'Content-Length':str(len(body) if length is None else length)}
        self.stream=io.BytesIO(body);self.read_sizes=[];self.closed=False
    def read(self,size):self.read_sizes.append(size);return self.stream.read(size)
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True


class Child:
    def __init__(self,raw=b'',timeout=False):
        self.stdin=io.BytesIO();self.stdout=io.BytesIO(raw);self.stderr=io.BytesIO(b'capability=secret')
        self.terminated=0;self.killed=0;self.waits=0;self.timeout=timeout
    def poll(self):return None
    def terminate(self):self.terminated+=1
    def kill(self):self.killed+=1
    def wait(self,timeout):
        self.waits+=1
        if self.timeout and self.waits==1:raise subject.subprocess.TimeoutExpired('synthetic child',timeout)
        return 0


def metadata_frame(status=200,headers=None):
    return (json.dumps({'status':status,'headers':headers or {'Content-Length':'3'}})+'\n').encode()


def inputs(directory):
    output=directory/'download';output.mkdir()
    for name,payload in [('record',record()),('p4',{'cumulative_charged_bytes':77740806}),
                         ('p4docs',{'charged_bytes':393216}),('p5docs',{'charged_bytes':747003})]:
        (directory/name).write_text(json.dumps(payload))
    return output,*(directory/name for name in ('record','p4','p4docs','p5docs'))


def fake_request(body,head_length=None):
    def request(transfer,url,method='GET',headers=None,allowance=0):
        response=Response(b'' if method=='HEAD' else body,length=subject.SIZE if head_length is None else head_length)
        item={'url':subject.safe_url(url),'method':method,'payload_bytes':0}
        transfer.requests.append(item);transfer.save();return response,item
    return request


class Contract(unittest.TestCase):
    def test_exact_object(self):
        self.assertEqual(subject.select(json.dumps(record()).encode())['dsid'],302521)
    def test_mutated_identity(self):
        for field,value in [('recid','93915'),('doi','unverified')]:
            with self.subTest(field=field):
                raw=record();raw['metadata'][field]=value
                with self.assertRaises(ValueError): subject.select(json.dumps(raw).encode())
    def test_mutated_file(self):
        for field,value in [('key','unapproved.root'),('size',subject.SIZE+1),('checksum','adler32:00000000'),
                            ('uri','root://other.cern.ch//eos/opendata/atlas/rucio/opendata/'+subject.NAME)]:
            with self.subTest(field=field):
                raw=record();raw['metadata']['_files'][0][field]=value
                with self.assertRaises(ValueError): subject.select(json.dumps(raw).encode())
    def test_ambiguous_file(self):
        raw=record();raw['metadata']['_files'].append(copy.deepcopy(raw['metadata']['_files'][0]))
        with self.assertRaises(ValueError): subject.select(json.dumps(raw).encode())
    def test_new_cap_includes_documents(self):
        self.assertEqual(subject.budget(78134022,747003),subject.PHASE5_LIMIT-747003)
    def test_cumulative_cap_still_applies(self):
        reserve=12*65536
        remaining=subject.SIZE+reserve
        self.assertEqual(subject.budget(subject.CUMULATIVE_LIMIT-remaining-747003,747003),remaining)
        with self.assertRaises(ValueError): subject.budget(subject.CUMULATIVE_LIMIT-remaining-747003+1,747003)
    def test_invalid_budget(self):
        for prior,docs in [(-1,0),(0,-1),(0,subject.PHASE5_LIMIT),('78134022',0),(True,0)]:
            with self.subTest(prior=prior,docs=docs):
                with self.assertRaises(ValueError): subject.budget(prior,docs)
    def test_checked_redirect_no_userinfo(self):
        from fetch_phase4_samples import CheckedRedirect
        for target in ['https://name:secret@st-1.cern.ch:8443/path','https://st-1.cern.ch:8443/path#secret']:
            with self.assertRaises(ValueError): CheckedRedirect().redirect_request(None,None,307,'',{},target)
    def test_https_upgrade_exact_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            transfer=subject.ContinuumTransfer(Path(folder),https_storage=True)
            path='/eos/opendata/atlas/rucio/opendata/'+subject.NAME
            transfer.facts['https_url']='https://eospublic.cern.ch'+path
            calls=[]
            def fake(url,**kwargs):
                calls.append(url)
                if len(calls)==1:
                    raise urllib.error.HTTPError(url,307,'redirect',{'Location':'http://st-1.cern.ch:8443'+path+'?capability=testonly'},io.BytesIO())
                return 'response','item'
            transfer.request=fake
            self.assertEqual(transfer.eos_request(transfer.facts['https_url'],{},subject.SIZE),('response','item'))
            self.assertTrue(calls[1].startswith('https://st-1.cern.ch:8443'))
            saved=(Path(folder)/'access.json').read_text()
            self.assertNotIn('testonly',saved);self.assertNotIn('capability=',saved)
    def test_https_upgrade_rejects_unscoped_redirects(self):
        with tempfile.TemporaryDirectory() as folder:
            transfer=subject.ContinuumTransfer(Path(folder),https_storage=True)
            transfer.facts['https_url']='https://eospublic.cern.ch/exact'
            for target in ['http://evil.invalid:8443/exact','http://st-1.cern.ch:80/exact',
                           'http://st-1.cern.ch:8443/other','http://a:b@st-1.cern.ch:8443/exact',
                           'http://st-1.cern.ch:8443/exact#fragment','file:///exact']:
                with self.subTest(target=target):
                    def fake(url,**kwargs):
                        raise urllib.error.HTTPError(url,307,'redirect',{'Location':target},io.BytesIO())
                    transfer.request=fake
                    with self.assertRaises(ValueError): transfer.eos_request(transfer.facts['https_url'],{},subject.SIZE)
    def test_existing_final_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder);output=d/'download';output.mkdir()
            (output/subject.NAME).write_bytes(b'user-owned')
            for name,payload in [('record',record()),('p4',{'cumulative_charged_bytes':77740806}),
                                 ('p4docs',{'charged_bytes':393216}),('p5docs',{'charged_bytes':747003})]:
                (d/name).write_text(json.dumps(payload))
            with self.assertRaises(ValueError):subject.download(output,d/'record',d/'p4',d/'p4docs',d/'p5docs')
            self.assertEqual((output/subject.NAME).read_bytes(),b'user-owned')
            self.assertEqual(json.loads((output/'access.json').read_text())['payload_bytes'],0)

    def test_exclusive_publication_and_collision_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);partial=directory/'partial';final=directory/'final'
            partial.write_bytes(b'new');final.write_bytes(b'user-owned')
            with self.assertRaises(FileExistsError):subject.publish_exclusively(partial,final)
            self.assertEqual(partial.read_bytes(),b'new');self.assertEqual(final.read_bytes(),b'user-owned')
            other=directory/'other';subject.publish_exclusively(partial,other)
            self.assertEqual(other.read_bytes(),b'new');self.assertFalse(partial.exists())

    def test_wsl_metadata_does_not_request_body(self):
        child=Child(metadata_frame()+b'3\nabc');response=subject.WSLResponse(child,3)
        self.assertEqual(child.stdin.getvalue(),b'');self.assertEqual(child.stdout.tell(),len(metadata_frame()))
        self.assertEqual(response.read(3),b'abc');self.assertEqual(child.stdin.getvalue(),b'READ 3\n')
        response.__exit__();self.assertTrue(all(pipe.closed for pipe in (child.stdin,child.stdout,child.stderr)))

    def test_wsl_bounded_and_cumulative_read_guard(self):
        for size in (0,65537,True,4):
            child=Child(metadata_frame());response=subject.WSLResponse(child,2)
            with self.subTest(size=size),self.assertRaises(ValueError):response.read(size)
            self.assertTrue(child.stdin.closed);self.assertGreater(child.terminated,0)
        child=Child(metadata_frame()+b'2\nab');response=subject.WSLResponse(child,1)
        self.assertEqual(response.read(2),b'ab')
        with self.assertRaises(ValueError):response.read(1)
        self.assertTrue(child.stdout.closed)

    def test_wsl_invalid_frames_and_cleanup(self):
        for frame in (b'4\nabcd',b'-1\n',b'not-a-size\n',b'3\nab',b''):
            with self.subTest(frame=frame):
                child=Child(metadata_frame()+frame);response=subject.WSLResponse(child,3)
                with self.assertRaises((RuntimeError,ValueError)):response.read(3)
                self.assertTrue(all(pipe.closed for pipe in (child.stdin,child.stdout,child.stderr)))
        for frame in (b'',b'not-json\n',b'x'*8193,metadata_frame(headers={'Location':'?secret'})):
            with self.subTest(metadata=frame[:10]):
                child=Child(frame)
                with self.assertRaises((RuntimeError,ValueError)):subject.WSLResponse(child,3)
                self.assertTrue(child.stderr.closed)

    def test_teardown_timeout_and_stream_error(self):
        child=Child(timeout=True);subject.teardown_child(child)
        self.assertEqual(child.killed,1);self.assertEqual(child.waits,2)
        self.assertTrue(all(pipe.closed for pipe in (child.stdin,child.stdout,child.stderr)))
        child=Child();child.stdin=Mock();child.stdin.close.side_effect=OSError('secret query')
        subject.teardown_child(child);self.assertTrue(child.stdout.closed);self.assertTrue(child.stderr.closed)
        child.stdin.close.assert_called_once()

    def test_wsl_request_initialization_failure_cleans_and_redacts(self):
        with tempfile.TemporaryDirectory() as folder:
            transfer=subject.ContinuumTransfer(Path(folder),storage_via_wsl=True)
            transfer.facts['https_url']='https://eospublic.cern.ch/exact';child=Child(b'not-json\n')
            with patch.object(subject.os,'name','nt'),patch.object(subject.subprocess,'Popen',return_value=child):
                with self.assertRaises(ValueError):transfer.request('http://st-1.cern.ch:8443/exact?capability=secret',allowance=3)
            self.assertTrue(all(pipe.closed for pipe in (child.stdin,child.stdout,child.stderr)))
            raw=(Path(folder)/'access.json').read_text();self.assertNotIn('capability=',raw);self.assertNotIn('secret',raw)
            self.assertEqual(transfer.requests[0]['payload_bytes'],0)

    def test_wsl_request_broken_stdin_cleans_and_redacts(self):
        with tempfile.TemporaryDirectory() as folder:
            transfer=subject.ContinuumTransfer(Path(folder),storage_via_wsl=True)
            transfer.facts['https_url']='https://eospublic.cern.ch/exact';child=Child(metadata_frame())
            child.stdin.close()
            with patch.object(subject.os,'name','nt'),patch.object(subject.subprocess,'Popen',return_value=child):
                with self.assertRaises(ValueError):transfer.request('http://st-1.cern.ch:8443/exact?capability=secret',allowance=3)
            self.assertGreater(child.terminated,0)
            self.assertTrue(all(pipe.closed for pipe in (child.stdin,child.stdout,child.stderr)))
            raw=(Path(folder)/'access.json').read_text();self.assertNotIn('capability=',raw);self.assertNotIn('secret',raw)

    def test_child_protocol_enforces_body_cap_without_prefetch(self):
        spec={'url':'http://st-1.cern.ch:8443/exact?capability=secret','expected_path':'/exact',
              'headers':{},'safe_headers':list(subject.transport.SAFE_HEADERS),'maximum_body_bytes':1}
        for commands,expected in [('',[]),('READ 1\n',[1]),('READ 2\nREAD 1\n',[2])]:
            response=Response(b'abc');stdout=types.SimpleNamespace(buffer=io.BytesIO());stderr=io.StringIO()
            opener=Mock();opener.open.return_value=response
            with patch('urllib.request.build_opener',return_value=opener),patch.object(sys,'stdin',io.StringIO(json.dumps(spec)+'\n'+commands)),patch.object(sys,'stdout',stdout),patch.object(sys,'stderr',stderr):
                try:exec(subject.WSL_HTTP_CLIENT,{})
                except SystemExit as error:self.assertEqual(error.code,1)
            self.assertEqual(response.read_sizes,expected);self.assertNotIn('secret',stderr.getvalue())

    def test_inherited_error_log_redacts_query_and_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            transfer=subject.ContinuumTransfer(Path(folder))
            transfer.opener.open=Mock(side_effect=urllib.error.URLError('https://name:password@st-1.cern.ch/exact?capability=secret'))
            with self.assertRaises(urllib.error.URLError):transfer.request('https://eospublic.cern.ch/exact?capability=secret')
            raw=(Path(folder)/'access.json').read_text()
            for token in ('secret','password','capability='):self.assertNotIn(token,raw)
            self.assertEqual(transfer.requests[0]['error'],'URLError')

    def test_bad_head_size_no_body_read(self):
        with tempfile.TemporaryDirectory() as folder:
            args=inputs(Path(folder))
            with patch.object(subject.ContinuumTransfer,'trust_cern_ca'),patch.object(subject.ContinuumTransfer,'request',fake_request(b'abc',subject.SIZE+1)):
                with self.assertRaises(ValueError):subject.download(*args)
            receipt=json.loads((args[0]/'access.json').read_text())
            self.assertEqual(receipt['payload_bytes'],0);self.assertEqual(len(receipt['requests']),1)
            self.assertFalse((args[0]/subject.NAME).exists())

    def test_bad_payload_size_checksum_and_preserved_failed_partial(self):
        body=b'abcde'
        for actual,checksum in [(body[:-1],f'adler32:{zlib.adler32(body):08x}'),(body,'adler32:00000000')]:
            with tempfile.TemporaryDirectory() as folder,patch.object(subject,'SIZE',len(body)),patch.object(subject,'CHECKSUM',checksum):
                args=inputs(Path(folder))
                with patch.object(subject.ContinuumTransfer,'trust_cern_ca'),patch.object(subject.ContinuumTransfer,'request',fake_request(actual)):
                    with self.assertRaises(RuntimeError if len(actual)<len(body) else ValueError):subject.download(*args)
                receipt=json.loads((args[0]/'access.json').read_text())
                self.assertEqual(receipt['status'],'BLOCKED_ACCESS');self.assertEqual(receipt['payload_bytes'],len(actual))
                self.assertFalse((args[0]/subject.NAME).exists());self.assertEqual(len(list(args[0].glob('*.partial'))),1)

    def test_complete_synthetic_payload_checksum_publication_and_charges(self):
        body=b'abcde';checksum=f'adler32:{zlib.adler32(body):08x}'
        with tempfile.TemporaryDirectory() as folder,patch.object(subject,'SIZE',len(body)),patch.object(subject,'CHECKSUM',checksum):
            args=inputs(Path(folder))
            with patch.object(subject.ContinuumTransfer,'trust_cern_ca'),patch.object(subject.ContinuumTransfer,'request',fake_request(body)):
                receipt=subject.download(*args)
            self.assertEqual(receipt['status'],'PASS');self.assertEqual(receipt['payload_bytes'],len(body))
            self.assertEqual(receipt['charged_bytes'],len(body)+2*65536)
            self.assertEqual(receipt['phase5_charged_bytes'],747003+len(body)+2*65536)
            self.assertEqual(receipt['cumulative_charged_bytes'],78134022+747003+len(body)+2*65536)
            self.assertEqual((args[0]/subject.NAME).read_bytes(),body);self.assertFalse(list(args[0].glob('*.partial')))
            self.assertEqual(receipt['files'][0]['sha256'],subject.sha(body))
            self.assertEqual(receipt['files'][0]['checksum_status'],'PASS')

    def test_resume_pins_and_charges_not_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            args=inputs(Path(folder))
            with patch.object(subject.ContinuumTransfer,'trust_cern_ca',side_effect=RuntimeError('first blocked attempt')):
                with self.assertRaises(RuntimeError):subject.download(*args)
            path=args[0]/'access.json';receipt=json.loads(path.read_text())
            receipt['requests']=[{'url':'https://eospublic.cern.ch/exact','payload_bytes':7}]
            receipt['payload_bytes']=7;receipt['charged_bytes']=65543;path.write_text(json.dumps(receipt))
            with patch.object(subject.ContinuumTransfer,'trust_cern_ca',side_effect=RuntimeError('second blocked attempt')):
                with self.assertRaises(RuntimeError):subject.download(*args,resume=True)
            resumed=json.loads(path.read_text());self.assertEqual(resumed['payload_bytes'],7);self.assertEqual(resumed['charged_bytes'],65543)
            self.assertEqual(resumed['phase5_charged_bytes'],747003+65543)
            self.assertEqual(resumed['cumulative_charged_bytes'],78134022+747003+65543)
            before=path.read_bytes();args[-1].write_text(json.dumps({'charged_bytes':747004}))
            with patch.object(subject.ContinuumTransfer,'trust_cern_ca') as network:
                with self.assertRaises(ValueError):subject.download(*args,resume=True)
                network.assert_not_called()
            self.assertEqual(path.read_bytes(),before)

    def test_resume_receipt_inconsistent_charges_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);receipt={'status':'BLOCKED_ACCESS','requests':[{'payload_bytes':7}],
                                          'payload_bytes':0,'charged_bytes':65536}
            path=directory/'access.json';path.write_text(json.dumps(receipt));before=path.read_bytes()
            with self.assertRaises(ValueError):subject.ContinuumTransfer(directory,resume=True)
            self.assertEqual(path.read_bytes(),before)

    def test_existing_ledger_requires_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            args=inputs(Path(folder));path=args[0]/'access.json';path.write_bytes(b'user-owned ledger')
            with self.assertRaises(ValueError):subject.download(*args)
            self.assertEqual(path.read_bytes(),b'user-owned ledger')


if __name__=='__main__':unittest.main()
