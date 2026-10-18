"""SOURCE/METHOD ONLY: synthetic receipts are not actual production builds."""
import ast,copy,hashlib,json,os,sys,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch,Mock
from . import route_a as a,approval,run,build
from .contract import HERE,REPO,PHYSICS_SHA,SEEDS,CAPS,identity,sha
from .build_plan import plan,LIBS

class ActivationSourceTests(unittest.TestCase):
    def test_lossless_toolchain_inventory_fits_unchanged_git_cap(self):
        from .git_precheck import OUTPUT_BYTES
        rows=a.toolchain_rows();self.assertEqual(len(rows),8166)
        self.assertLess((REPO/'metadata/phase7_final_route_a_toolchain.json').stat().st_size,OUTPUT_BYTES)
    def test_source_binding_has_canonical_posix_order(self):
        rows=a.full_sources()
        self.assertEqual(rows,sorted(rows,key=lambda row:row['path']))
    def test_exact_proposal_and_reversal_with_bounded_activation_delta(self):
        from ..guard_correction import builder_proposal as p
        self.assertEqual(hashlib.sha256(p.source().encode()).hexdigest(),'e74ee57c747e1a7d744a143789e7ee1fc15d5dde10ff41880ce1c454b32241c2')
        self.assertEqual(hashlib.sha256(p.restore(p.source()).encode()).hexdigest(),p.BUILDER_ORIGINAL_SHA256)
        self.assertEqual(sha(HERE.parent/'guard_correction/native_checks_corrected.f'),a.GUARD_SHA)
        self.assertEqual(sha(HERE/'native_checks.f'),'5cbe786a92c872cdbcd43440f8c5b8894b6d27da1ec883c66fc4ba6d402dabfb')
    def test_compile_and_link_plan_no_old_or_duplicate_guard(self):
        jobs=plan('/ISOLATED/process','/ISOLATED','/PINNED/bin/gfortran')
        inputs=[j[j.index('-c')+1] for j in jobs[:-1]]
        guards=[p for p in inputs if 'native_checks' in p]
        self.assertEqual(guards,['/ISOLATED/process/SubProcesses/P0_gg_hh/native_checks_corrected.f'])
        self.assertEqual(len(inputs),len(set(inputs)));self.assertEqual(len(inputs),27)
        objects=[j[j.index('-o')+1] for j in jobs[:-1]]
        self.assertEqual(len(objects),len(set(objects)))
        self.assertEqual(jobs[-1][3:3+len(objects)],objects)
        self.assertEqual(jobs[-1][-len(LIBS)-1:],[*['-l'+x for x in LIBS],'-lstdc++'])
        self.assertTrue(all('-O0' in j for j in jobs[:-1]))
        self.assertFalse(any('install' in x or 'make'==x for j in jobs for x in j))
    def test_builder_cannot_create_or_compile_without_human_review(self):
        with patch.object(build,'safe_root',lambda p:Path(p)),patch.object(build,'full_source_identity',return_value=[]),\
            patch.object(build,'check_revision') as rev,patch.object(build,'bounded_invoke') as invoke:
            for fake in [None,{'action':'BUILD_ONLY','revision':'e'*40,'human_approved':True}]:
                with self.assertRaisesRegex(ValueError,'SEPARATE_HUMAN_REVIEW'):
                    build.prepare('/METHOD_NEVER_CREATED',revision='e'*40,build_review=fake)
            rev.assert_not_called();invoke.assert_not_called()
    def test_consumed_revision_and_stale_scope(self):
        for rev in approval.CONSUMED:
            with self.assertRaisesRegex(ValueError,'CONSUMED'):
                approval.scope('BUILD_ONLY',rev,Path('/METHOD_ONLY'),[])
        with self.assertRaisesRegex(ValueError,'NO_FILE_OR_FLAG'):
            approval.HumanReview(object(),{})
        good=approval.scope('BUILD_ONLY','e'*40,Path('/METHOD_ONLY'),[])
        token=approval.HumanReview(approval._SEAL,good) # METHOD ONLY in-process fixture
        approval.verify(token,good)
        wrong=copy.deepcopy(good);wrong['action']='PHYSICAL_RESTART'
        with self.assertRaisesRegex(ValueError,'STALE_OR_WRONG'):approval.verify(token,wrong)
        token.scope['revision']='a'*40
        with self.assertRaises(ValueError):approval.verify(token,token.scope)
    def test_fake_human_pipe_is_not_a_review(self):
        stream=Mock();stream.__enter__=Mock(return_value=stream);stream.__exit__=Mock(return_value=False);stream.fileno.return_value=0
        with patch('builtins.open',return_value=stream),patch('os.isatty',return_value=False):
            with self.assertRaisesRegex(ValueError,'CONTROLLING_HUMAN_TERMINAL'):approval.confirm({})
    def test_nonseekable_terminal_io_on_isolated_method_pty(self):
        # Synthetic I/O method only. Never automate a real human terminal.
        import pty
        master,slave=pty.openpty();real_open=open
        try:
            expected=approval.scope('BUILD_ONLY','e'*40,Path('/SYNTHETIC_METHOD_ONLY'),[])
            os.write(master,('APPROVE BUILD_ONLY '+identity(expected)+'\n').encode())
            def fixture_open(path,mode,**kw):
                return os.fdopen(os.dup(slave),mode,**kw) if path=='/dev/tty' else real_open(path,mode,**kw)
            with patch('builtins.open',fixture_open):token=approval.confirm(expected)
            approval.verify(token,expected)
        finally:os.close(master);os.close(slave)
    def test_physical_default_denies_before_native_or_output(self):
        with patch.object(run,'safe_root',lambda p:Path(p)),patch.object(run,'check_build') as reader,patch.object(run,'supervise') as native:
            with self.assertRaisesRegex(ValueError,'SEPARATE_PHYSICAL_RESTART'):
                run.execute_reviewed('/METHOD_NEVER_CREATED','e'*40)
            reader.assert_not_called();native.assert_not_called()
    def test_build_source_uses_fresh_local_copies_and_zero_me_only(self):
        text=(HERE/'build.py').read_text();tree=ast.parse(text)
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertNotIn('execute_reviewed',calls);self.assertNotIn('capability',calls)
        self.assertIn("require(not root.exists()",text);self.assertIn("HH_PREFLIGHT_ONLY':'1'",text)
        self.assertIn('STALE_BUILD_OBJECT_OR_EXECUTABLE',text);self.assertIn('SOURCE_CHANGED_DURING_BUILD',text)
        self.assertLess(text.index('verify_human_review('),text.index('root.mkdir('))
        self.assertIn('verify_dependency_sources(process)',text)

class SyntheticReceiptMethods(unittest.TestCase):
    """Small ordinary files, no ELF/ME. Dependency/clone mocks are declared."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.stack=ExitStack();self.addCleanup(self.stack.close);self.addCleanup(self.tmp.cleanup)
        self.revision='e'*40;self.bindings=[{'path':'SYNTHETIC_METHOD_ONLY','sha256':'a'*64}]
        self.guard={'route':a.ROUTE,'native_guard_sha256':a.GUARD_SHA,'source_bindings':self.bindings,
            'source_binding_identity':identity(self.bindings),'physical_restart_authorized':False}
        self.compiler=self.root/'bin/gfortran';self.compiler.parent.mkdir();self.compiler.write_bytes(b'SYNTHETIC_COMPILER_NOT_EXECUTABLE')
        self.lib=self.root/'library';self.lib.write_bytes(b'SYNTHETIC_LIBRARY_NOT_LOADABLE')
        cfg={'toolchain_prefix':str(self.root)}
        for target,name,value in [(a,'descriptor',lambda:self.guard),(a,'full_sources',lambda:self.bindings),
            (a,'frozen_inputs',lambda:{'native':[],'cards':[]}),(a,'toolchain',lambda c:[{'path':'SYNTHETIC','sha256':sha(self.compiler)}]),
            (a,'verify_copies',lambda folder,seed:None),(run,'safe_root',lambda p:Path(p))]:
            self.stack.enter_context(patch.object(target,name,value))
        # Use a prefix matching the real compiler filename without invoking it.
        target=self.root/'bin/x86_64-conda-linux-gnu-gfortran';target.write_bytes(self.compiler.read_bytes());self.compiler=target
        original_read=a.read_json
        self.stack.enter_context(patch.object(a,'read_json',lambda p:cfg if str(p).endswith('/.local/mg5_installation.json') else original_read(p)))
        self.r={'schema':a.SCHEMA,'fixture_class':'SYNTHETIC_METHOD_ONLY_NOT_A_BUILD',
            'approved_build_source_revision':self.revision,'physics_contract_sha256':PHYSICS_SHA,'ceilings':CAPS,
            'source_identity':self.bindings,'guard_correction':self.guard,'frozen_source_cards':{'native':[],'cards':[]},
            'toolchain_identity':a.toolchain(self.compiler),'compile_plans':[],'build_commands':[],
            'actual_physical_execution':False,'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0,
            'preparation':{'pid':os.getpid(),'prepared_at_UTC':'SYNTHETIC_METHOD_TIME'},
            'resources_review_only':{'wall_seconds':.1,'child_CPU_seconds':.01},'replicas':[]}
        scope=approval.scope('BUILD_ONLY',self.revision,self.root,self.bindings)
        self.r['build_review']={'status':'EXTERNAL_OPERATOR_REVIEW_SCOPE_BOUND','scope':scope,'scope_sha256':identity(scope)}
        critical={x['path']:x['sha256'] for x in self.bindings}
        critical[a.RECOVERY_METADATA]=sha(REPO/a.RECOVERY_METADATA)
        critical['simulation/hh_signal/final_closure/config/physics_contract.json']=PHYSICS_SHA
        self.r['git_preflight']={'revision':self.revision,'physics_sha256':PHYSICS_SHA,
            'git_preflight':{'status':'PASS_FULL_TRACKED_PREFLIGHT','critical_source_sha256':critical}}
        for seed in SEEDS:
            folder=self.root/f'replica_{seed}';folder.mkdir();(folder/'hh_final_integral_reviewed').write_bytes(b'SYNTHETIC_NOT_AN_ELF_'+str(seed).encode())
            (folder/'card').write_text('SYNTHETIC_CARD')
            jobs=plan(folder/'process',folder,self.compiler);self.r['compile_plans'].append({'seed':seed,'commands':jobs})
            self.r['build_commands'].extend({'argv':j,'pid':os.getpid(),'exit':0,'wall_seconds':.01,'process_group_kill_cleanup':True} for j in jobs)
            self.r['build_commands'].append({'argv':[str(folder/'hh_final_integral_reviewed')],'pid':os.getpid(),'exit':80,'wall_seconds':.01,'process_group_kill_cleanup':True})
            pre=[]
            for stage,mo in [('adaptation',0),('measurement',1)]:
                work=folder/'process/SubProcesses/P0_gg_hh'/(stage+'_preflight');work.mkdir(parents=True)
                rec=[f'HH_PRE_SAMPLING_CONFIG_PASS {seed} 0 {mo}',f'HI_INPUTS 250 {4-mo} {4-mo} {2 if not mo else 0} 0 F',
                    'HI_PDF cteq6l1 cteq6l1 cteq6l1','HI_ALPHA .13 1','HI_MASS 125 173 4.7','HI_SCALE 4 .5 F F F',
                    'HI_BEAMS 6500 6500 1 1','H_IO 1 1','HI_PREFLIGHT_ZERO_ME']
                pre.append({'stage':stage,'execution_class':'REAL_NATIVE_SUPERVISED','exit':0,'failure':None,'pid':os.getpid(),
                    'wall_seconds':.01,'process_group_kill_cleanup':True,'raw_streams_retained':False,'records':rec,
                    'raw_stream_bytes':{'stdout':1,'stderr':0},'raw_stream_SHA256':{'stdout':'a'*64,'stderr':'b'*64},
                    'scope':'ACTUAL_NATIVE_INPUT_PARSE_EXIT_BEFORE_MAPPING_OR_ME','postcondition':a.no_events(work)})
            (folder/'process/SubProcesses/P0_gg_hh/denied_preflight').mkdir()
            self.r['replicas'].append({'seed':seed,'executable':'hh_final_integral_reviewed','executable_sha256':sha(folder/'hh_final_integral_reviewed'),
                'immutable':a.immutable(folder),'dynamic_dependencies':[{'name':self.lib.name,'path':str(self.lib),'sha256':sha(self.lib)}],
                'fortran_compiler_sha256':sha(self.compiler),'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0,'preflights':pre,
                'unsupervised_exit':80,'unsupervised_denial':{'exit':80,'record':'HI_FAILURE SUPERVISOR_REQUIRED','pid':os.getpid(),'wall_seconds':.01}})
        self.persist()
    def persist(self):
        self.r['immutable_binary_identity']=a.binary_identity(self.r)
        for row in self.r['replicas']:(self.root/f'replica_{row["seed"]}/build.json').write_text(json.dumps(row))
        (self.root/'review_build.json').write_text(json.dumps(self.r))
    def validate(self):return a.validate_receipt(self.r,self.root,self.revision,self.bindings)
    def test_correct_schema_is_method_acceptance_only(self):
        result=self.validate();self.assertFalse(result['physical_restart_authorized'])
        self.assertEqual(result['FULL_BUILD_RECEIPT_IDENTITY'],identity(self.r))
    def test_wrong_schema_and_old_binary(self):
        for mutate in [lambda r:r.update(schema='OLD'),lambda r:r['replicas'][0].update(executable_sha256=next(iter(a.OLD_EXECUTABLES)))]:
            old=copy.deepcopy(self.r);mutate(self.r)
            with self.assertRaises(ValueError):self.validate()
            self.r=old
    def test_edited_executable_and_incomplete_inventory(self):
        (self.root/'replica_910001/hh_final_integral_reviewed').write_bytes(b'EDITED')
        with self.assertRaisesRegex(ValueError,'EXECUTABLE_DRIFT'):self.validate()
    def test_extra_or_tampered_source_inventory(self):
        (self.root/'replica_910001/new_source.f').write_text('TAMPERED')
        with self.assertRaisesRegex(ValueError,'INCOMPLETE_OR_EDITED'):self.validate()
    def test_missing_or_edited_dependency(self):
        self.r['replicas'][0]['dynamic_dependencies']=[];self.persist()
        with self.assertRaisesRegex(ValueError,'MISSING_OR_DUPLICATE'):self.validate()
    def test_source_binding_and_seed_tamper(self):
        self.r['source_identity']=[]
        with self.assertRaisesRegex(ValueError,'SOURCE_OR_GUARD'):self.validate()
    def test_duplicate_seed_and_wrong_guard_rejected(self):
        original=copy.deepcopy(self.r);self.r['replicas'][1]['seed']=SEEDS[0]
        with self.assertRaisesRegex(ValueError,'FIXED_BUILD_SEED'):self.validate()
        self.r=original;self.r['guard_correction']=copy.deepcopy(self.guard)
        self.r['guard_correction']['native_guard_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'SOURCE_OR_GUARD'):self.validate()
    def test_dependency_bytes_are_rehashed(self):
        self.lib.write_bytes(b'EDITED_LIBRARY')
        with self.assertRaisesRegex(ValueError,'SHARED_LIBRARY_DRIFT'):self.validate()
    def test_loader_soname_is_distinct_from_resolved_filename(self):
        for row in self.r['replicas']:row['dynamic_dependencies'][0]['name']='libmethod.so.5'
        self.persist();self.validate() # METHOD ONLY; no fake library is loaded.
    def test_toolchain_or_compile_plan_cannot_be_self_relabelled(self):
        self.r['compile_plans'][0]['commands'][0][1]='-O2';self.persist()
        with self.assertRaisesRegex(ValueError,'COMPILE_LINK_PLAN'):self.validate()
    def test_denied_entry_evidence_cannot_be_missing(self):
        self.r['replicas'][0]['unsupervised_denial']={};self.persist()
        with self.assertRaisesRegex(ValueError,'UNSUPERVISED_ENTRY'):self.validate()
    def test_stale_authorization(self):
        self.r['approved_build_source_revision']=next(iter(approval.CONSUMED))
        with self.assertRaisesRegex(ValueError,'STALE_BUILD_SOURCE'):self.validate()
    def test_fabricated_preflight(self):
        self.r['replicas'][0]['preflights'][0]['records']=['HI_PREFLIGHT_ZERO_ME'];self.persist()
        with self.assertRaisesRegex(ValueError,'PROTOCOL'):self.validate()
    def test_preflight_file_changed(self):
        (self.root/'replica_910001/process/SubProcesses/P0_gg_hh/adaptation_preflight/fake.txt').write_text('FAKE')
        with self.assertRaisesRegex(ValueError,'PREFLIGHT_FILES_CHANGED'):self.validate()
    def test_fake_human_approval_never_reaches_dynamic_loader(self):
        with patch.object(a,'dependencies') as loader:
            with self.assertRaisesRegex(ValueError,'SEPARATE_HUMAN_REVIEW'):
                run.check_build(self.root,self.revision,binary_review={'human_approved':True})
            loader.assert_not_called()
    def test_edited_receipt_cannot_reuse_independent_binary_review(self):
        ids=a.identities(self.r)
        token=approval.HumanReview(approval._SEAL,approval.scope('BINARY_REVIEW',self.revision,self.root,self.bindings,
            full_receipt=ids['FULL_BUILD_RECEIPT_IDENTITY'],binary_identity=ids['IMMUTABLE_BINARY_SOURCE_IDENTITY']))
        self.r['resources_review_only']['wall_seconds']=12;self.persist()
        with self.assertRaisesRegex(ValueError,'STALE_OR_WRONG'):run.check_build(self.root,self.revision,binary_review=token)
    def test_clocks_differ_without_relabelling_binary(self):
        before=a.identities(self.r);self.r['preparation']['pid']+=1;self.r['resources_review_only']['wall_seconds']=21
        after=a.identities(self.r);self.assertNotEqual(before['FULL_BUILD_RECEIPT_IDENTITY'],after['FULL_BUILD_RECEIPT_IDENTITY'])
        self.assertEqual(before['IMMUTABLE_BINARY_SOURCE_IDENTITY'],after['IMMUTABLE_BINARY_SOURCE_IDENTITY'])
    def test_consumed_workspace(self):
        marker=self.root/'execution_receipt.json';marker.write_text('PRESERVE')
        with self.assertRaisesRegex(ValueError,'MUST_NOT_RESTART'):run.require_fresh_attempt(self.root)
        self.assertEqual(marker.read_text(),'PRESERVE')
    def test_unsafe_inventory_path(self):
        for name in ['../escape','/absolute','process/../card','process//card']:
            with self.assertRaises(ValueError):a.regular(self.root,name)

class BuildProcessMethods(unittest.TestCase):
    def test_actual_nonphysical_child_measurements_and_failure_retention(self):
        from .build_process import invoke
        from .containment import Budget
        with tempfile.TemporaryDirectory() as td:
            r,receipt=invoke([sys.executable,'-B','-c','print("METHOD_ONLY")'],td,os.environ,Budget(td,wall=30,cpu=30))
            self.assertEqual(r.returncode,0);self.assertGreater(receipt['pid'],0);self.assertIn('child_CPU_seconds',receipt)
            with self.assertRaises(ValueError) as caught:
                invoke([sys.executable,'-B','-c','raise SystemExit(7)'],td,os.environ,Budget(td,wall=30,cpu=30))
            self.assertEqual(caught.exception.build_measurement['exit'],7)
            self.assertTrue(caught.exception.build_measurement['process_group_kill_cleanup'])
    def test_aggregate_budget_terminates_child(self):
        from .build_process import invoke
        from .containment import Budget
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'RESOURCE_TIME') as caught:
                invoke([sys.executable,'-B','-c','import time;time.sleep(30)'],td,os.environ,Budget(td,wall=5.3,cpu=30))
            self.assertLess(caught.exception.build_measurement['wall_seconds'],3)
            self.assertTrue(caught.exception.build_measurement['process_group_kill_cleanup'])
    def test_live_descendant_cpu_uses_conservative_one_core_bound(self):
        from .build_process import invoke
        from .containment import Budget
        with tempfile.TemporaryDirectory() as td:
            code='import subprocess,sys;subprocess.run([sys.executable,"-c","while True:pass"])'
            with self.assertRaisesRegex(ValueError,'BUILD_AGGREGATE_CPU_RESERVE') as caught:
                invoke([sys.executable,'-B','-c',code],td,os.environ,Budget(td,wall=30,cpu=5.3))
            self.assertLess(caught.exception.build_measurement['wall_seconds'],3)
            self.assertTrue(caught.exception.build_measurement['process_group_kill_cleanup'])

if __name__=='__main__':unittest.main()
