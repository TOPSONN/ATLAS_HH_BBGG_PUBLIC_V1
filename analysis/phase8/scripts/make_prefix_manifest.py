#!/usr/bin/env python3
"""Prepare only an existing-reference readback manifest; never creates ROOT/events."""
import argparse,copy,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location("phase8_input_audit",Path(__file__).with_name("audit_inputs.py"))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def build_prefix_manifest(full_manifest, repository):
    result=copy.deepcopy(full_manifest);root=Path(repository)
    result["readback_evidence_class"]="REFERENCE_PREFIX_TEST"
    result["status"]="PREFIX_HASH_PASS_PENDING_NATIVE_READ"
    result["prefix_events_expected"]=800
    for row in result["datasets"]:
        key=row["dataset_id"]
        if row["truth_format"]=="signal":
            directory=root/"reference_samples/hh_signal/S01_ggf_hh_sm"/("phase7b_100" if key=="S01_B100" else "phase7c_1000")
            public=json.loads((directory/"manifest.json").read_text());item=next(f for f in public["files"] if f["path"]=="detector_100.root")
            path=directory/item["path"];expected=item["sha256"]
        elif row["truth_format"]=="continuum":
            name="pp_"+("jjgg_light" if key=="B03" else row["process"])+"_atlas_like"
            directory=root/"reference_samples/delphes"/name;public=json.loads((directory/"sample_manifest.json").read_text())
            item=public["root_file"];path=root/item["path"];expected=item["sha256"]
        else:
            name={"B04":"B04_ZH","B05":"B05_TTH","B06":"B06_BBGJ"}[key]
            directory=root/"reference_samples/new_backgrounds"/name;public=json.loads((directory/"manifest.json").read_text());item=next(f for f in public["files"] if f["path"]=="delphes/detector_100.root")
            path=directory/item["path"];expected=item["sha256"]
        audit.check_file("published_reference_ROOT",path,expected)
        row["root_path"]=str(path.resolve());row["root_sha256"]=expected
        row["expected_entries"]=100;row["is_full"]=(row["N_original"]==100)
        row["reference_prefix_status"]="PUBLISHED_100_REFERENCE_NO_ADDITIONAL_INDEPENDENT_EVENTS"
        row["verification_status"]="PREFIX_HASH_PASS_PENDING_NATIVE_READ"
        row["readback_evidence_class"]="REFERENCE_PREFIX_TEST"
        row["actual_TTree_entries"]=None
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,required=True);p.add_argument("--repository",type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    value=build_prefix_manifest(json.loads(a.manifest.read_text()),a.repository)
    audit.require(not a.output.exists(),"existing prefix manifest overwrite refused")
    audit.write_new(a.output,value)
    print(json.dumps({"status":value["status"],"datasets":len(value["datasets"]),"prefix_events_expected":800,"new_events":0}))
if __name__=="__main__":main()
