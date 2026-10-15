"""METHOD_ONLY guard/driver checks; no generator import or physical events."""
from copy import deepcopy
import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("background_test_mg",REPO/"simulation/new_backgrounds/mg5_stage.py")
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


class MG5StageTests(unittest.TestCase):
    def setUp(self):
        scratch=REPO/".local/phase6g_backgrounds/tests";scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix="method_only_mg_",dir=scratch);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.fake_repo=self.root/"method_repo"
        for subtree in ("simulation/zh_pilot/cards","simulation/zh_pilot/config","simulation/zh_pilot/scripts","simulation/new_backgrounds/cards","simulation/new_backgrounds/config"):
            shutil.copytree(REPO/subtree,self.fake_repo/subtree)
        self.install={"mg5_path":str(self.root/"installation/mg5"),"toolchain_prefix":str(self.root/"installation/toolchain"),
                      "source_commit":stage.MG5_COMMIT,"source_tag":"v3.5.16","source_url":"https://github.com/mg5amcnlo/mg5amcnlo.git"}
        self.work=self.root/"run/mg5"
    def plan(self,**kwargs):return stage.prepare_mg5_stage(self.work,repo=self.fake_repo,installation=self.install,**kwargs)
    def rewrite(self,plan):(self.work/"prepared_stage.json").write_text(json.dumps(plan),encoding="utf-8")
    def callback(self,calls,count=1000,fail=None,amplitude_status="PASS_ACTUAL_TREE_AMPLITUDES_AND_OFFICIAL_CARDS"):
        def run(argv,cwd,label):
            calls.append((argv,cwd,label));log=cwd/("process_generation.log" if label=="mg5_process_export" else "event_generation.log")
            if fail==label:
                log.write_text("METHOD_ONLY simulated failure\n");return {"exit_code":7,"log_path":str(log),"method_only":True}
            plan=json.loads((cwd/"prepared_stage.json").read_bytes());alias=plan["request"]["process"]
            if label=="mg5_process_export":
                cards=cwd/"process/Cards";cards.mkdir(parents=True)
                for name in ("run_card.dat","param_card.dat","proc_card_mg5.dat","me5_configuration.txt"):(cards/name).write_text("METHOD_ONLY_INVALID_EXPORT\n")
                (cwd/"amplitude_validation.json").write_text(json.dumps({"status":amplitude_status,"process":alias,"profile":stage.PROFILES[alias],"event_generation_invocations":0}))
                log.write_text("METHOD_ONLY no MG5 called\n")
            else:
                target=cwd/"process/Events"/plan["run_name"];target.mkdir(parents=True)
                (target/"unweighted_events.lhe.gz").write_bytes(gzip.compress(b"METHOD_ONLY_INVALID_NOT_A_REFERENCE"))
                (target/(plan["run_name"]+"_method_banner.txt")).write_text("METHOD_ONLY_INVALID_BANNER")
                log.write_text("METHOD_ONLY no generator called\n=== Results Summary for run: "+plan["run_name"]+" tag: method ===\nCross-section : 0.1234 +- 0.001234 pb\nNb of events : "+str(count)+"\n")
            return {"exit_code":0,"log_path":str(log),"method_only":True}
        return run
    def test_three_bound_text_profiles_have_exact_count_orders_scales_and_finite_bbgj_cuts(self):
        for alias,scale in (("zh",216.188),("tth",235.5),("bbgj",125.0)):
            with self.subTest(alias=alias):
                self.work=self.root/alias/"mg5";plan=self.plan(process=alias,seed=42)
                self.assertEqual(plan["status"],"PREPARED_TEXT_ONLY");self.assertEqual(plan["new_physics_events_generated"],0)
                self.assertFalse((self.work/"process").exists())
                values=stage._checker(REPO).parse_run((self.work/"inputs/run_card.dat").read_text())
                self.assertEqual((values["nevents"],values["iseed"],values["scale"]),(1000,42,scale))
                self.assertEqual(values["pdlabel"],"cteq6l1")
                self.assertEqual((self.work/"inputs/param_card.dat").read_bytes(),(REPO/"simulation/zh_pilot/cards/param_card.dat").read_bytes())
                if alias=="bbgj":
                    self.assertEqual(values["maxjetflavor"],4)
                    for key in ("ptb","ptj","pta"):self.assertEqual(values[key],25)
                    for key in ("etab","etaj","etaa"):self.assertEqual(values[key],2.5)
                    for key in ("drbb","drbj","drab","draj","drjj"):self.assertEqual(values[key],0.4)
                    self.assertEqual(values["ptgmin"],0)
    def test_only_one_launch_one_worker_relative_export_and_no_installer_or_madspin(self):
        self.plan(process="tth");gen=(self.work/"generate.mg5").read_text();launch=(self.work/"launch.mg5").read_text()
        self.assertIn("output process -nojpeg",gen);self.assertIn("set nb_core 1",gen+launch)
        self.assertEqual(launch.count("launch "),1);self.assertIn("madspin=OFF",launch)
        self.assertIn("set fortran_compiler x86_64-conda-linux-gnu-gfortran",gen)
        self.assertNotIn("/home/",gen);self.assertNotIn("install ",gen+launch)
        for line in (gen+launch).splitlines():
            if line.startswith("set "):self.assertTrue(line.endswith(" --no_save"))
    def test_unreviewed_count_seed_energy_or_process_rejected_before_output(self):
        for kwargs in ({"events":100},{"events":10000},{"events":True},{"seed":0},{"seed":True},{"seed":900000001},{"energy_gev":14000},{"energy_gev":float("nan")},{"process":"hh"}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):self.plan(**kwargs)
            self.assertFalse(self.work.exists())
    def test_protected_or_existing_output_preserved(self):
        with self.assertRaisesRegex(ValueError,"protected"):stage.prepare_mg5_stage(REPO/".local/forbidden",installation=self.install)
        self.work.mkdir(parents=True);(self.work/"keep").write_text("keep")
        with self.assertRaises(ValueError):self.plan()
        self.assertEqual((self.work/"keep").read_text(),"keep")
    def test_changed_cards_drivers_and_contract_stop_before_callback(self):
        plan=self.plan();calls=[]
        for name in ("inputs/run_card.dat","inputs/param_card.dat","generate.mg5","amplitude_contract.json"):
            p=self.work/name;raw=p.read_bytes();p.write_bytes(raw+b"changed")
            with self.subTest(name=name),self.assertRaises(ValueError):stage.execute_mg5_stage(plan,run_command=self.callback(calls))
            p.write_bytes(raw)
        self.assertEqual(calls,[])
    def test_metadata_cannot_grant_authority_or_change_worker_interpreter(self):
        plan=self.plan();calls=[]
        for key,val in (("execution_authority","AUTHORIZED"),("schema_version",True),("python_executable",str(self.root/"wrong")),("readonly_runtime_adapter_sha256","0"*64)):
            modified=deepcopy(plan);modified[key]=val;self.rewrite(modified)
            with self.subTest(key=key),self.assertRaises(ValueError):stage.execute_mg5_stage(modified,run_command=self.callback(calls))
        self.assertEqual(calls,[])
    def test_callback_required_and_pending_result_never_claims_physical_acceptance(self):
        plan=self.plan(process="bbgj");calls=[]
        with self.assertRaisesRegex(ValueError,"capability"):stage.execute_mg5_stage(plan,run_command=None)
        report=stage.execute_mg5_stage(plan,run_command=self.callback(calls))
        self.assertEqual([c[2] for c in calls],["mg5_process_export","mg5_1000_event_generation"])
        self.assertEqual(report["status"],"MG5_OUTPUT_PRESENT_PENDING_INDEPENDENT_LHE_PHYSICS_VALIDATION")
        self.assertEqual(report["full_original_event_denominator"],1000);self.assertEqual(report["source_included_decay_ids"],[])
        self.assertFalse(report["retry_or_event_replacement_performed"])
        with self.assertRaisesRegex(ValueError,"rerun"):stage.execute_mg5_stage(plan,run_command=self.callback(calls))
        self.assertEqual(len(calls),2)
    def test_failed_export_or_amplitude_gate_prevents_integration(self):
        for index,options in enumerate(({"fail":"mg5_process_export"},{"amplitude_status":"METHOD_ONLY_INVALID_ORDER"})):
            self.work=self.root/("failure"+str(index))/"mg5"
            plan=self.plan();calls=[]
            with self.assertRaises(ValueError):stage.execute_mg5_stage(plan,run_command=self.callback(calls,**options))
            self.assertEqual(len(calls),1)
    def test_wrong_actual_count_is_retained_and_not_replaced(self):
        plan=self.plan();calls=[]
        with self.assertRaisesRegex(ValueError,"other than 1000"):stage.execute_mg5_stage(plan,run_command=self.callback(calls,count=999))
        self.assertEqual(len(calls),2);self.assertTrue((self.work/"process/Events/zh1000/unweighted_events.lhe.gz").is_file())
    def test_actual_log_display_parser_rejects_duplicates_zero_nonfinite_negative_errors(self):
        good="=== Results Summary for run: tth1000 tag: phase6g_tth_1k ===\nCross-section : 1.234e-1 +- 1.2e-3 pb\nNb of events : 1000\n"
        self.assertEqual(stage.parse_generation_summary(good,"tth")["events"],1000)
        for text in (good+good,good.replace("tth1000","zh1000"),good.replace("1.2e-3","-0.1"),good.replace("1.234e-1","0"),good.replace("1.2e-3","NaN"),good.replace("1000\n","999\n")):
            with self.subTest(text=text),self.assertRaises(ValueError):stage.parse_generation_summary(text,"tth")
    def test_retained_runtime_audit_blocks_installation_mutations(self):
        fake=ModuleType("madgraph");fake.MG5DIR=self.install["mg5_path"];fake.ReadWrite=True
        hooks=[];old_argv=sys.argv[:];old_path=sys.path[:]
        try:
            sys.argv=["-c",self.install["mg5_path"],str(self.work/"generate.mg5"),self.install["toolchain_prefix"]]
            prefix=stage.READONLY_MG5_ADAPTER.split("from madgraph.interface.master_interface")[0]
            with patch.dict(sys.modules,{"madgraph":fake}),patch.object(sys,"addaudithook",side_effect=hooks.append):exec(prefix,{})
            self.assertFalse(fake.ReadWrite);self.assertEqual(len(hooks),1)
            for event,args in (("open",(str(Path(self.install["mg5_path"])/"models/cache.pkl"),"wb",os.O_CREAT)),("os.remove",(str(Path(self.install["toolchain_prefix"])/"bin/python"),-1))):
                with self.assertRaisesRegex(PermissionError,"BLOCKED_INSTALLATION_WRITE"):hooks[0](event,args)
            hooks[0]("open",(str(self.work/"output"),"w",os.O_CREAT))
        finally:sys.argv=old_argv;sys.path=old_path


if __name__=="__main__":unittest.main()
