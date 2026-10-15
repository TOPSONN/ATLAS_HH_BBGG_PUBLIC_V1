#!/usr/bin/env python3
"""Bounded independent Zbb+stable-H LHE validation, with preserved raw bytes.

No generation, repairs, filtering, or BR adoption occurs here. Synthetic inputs
must declare METHOD_ONLY and never receive physical acceptance. Physical record
acceptance requires the executor's bound artifacts and actual run provenance;
it does not authorize generation or establish exclusive H->gamma gamma rates.
"""
from __future__ import annotations
from collections import Counter
from decimal import Decimal, localcontext
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import uuid
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
PROFILES = {"zh":"B04_ZH_BBGG", "tth":"B05_TTH_HGG", "bbgj":"B06_BBGJ"}
PROFILE = PROFILES["zh"]
AUTHORIZATION_ATTACHMENT_SHA256 = "65b25230b2c50c1c4c7bb253887a8934268732dfca8be9b05eb8aed18fd22d91"
MAX_BYTES = 64 * 1024**2
SHA = re.compile(r"[0-9a-f]{64}\Z")
EVENT = re.compile(rb"<event>.*?</event>", re.S)
HEADER = re.compile(rb"<header>.*?</header>", re.S)
SOURCE_IDENTITY = {"mg5_version":"3.5.16", "source_commit":"3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7",
                   "source_url":"https://github.com/mg5amcnlo/mg5amcnlo.git", "source_tag":"v3.5.16"}
TAGS = {"process_card":"MG5ProcCard", "run_card":"MGRunCard", "param_card":"slha"}
# Official RunCardLO defaults serialized by MG5 during configure_directory.
# These are not new cuts or matching choices. The exact values are pinned to
# banner.py at the already verified official source commit; unknown keys fail.
OFFICIAL_IMPLICIT_RUN_DEFAULTS = {"alpsfact":1.0,"asrwgtflavor":5,"auto_ptj_mjj":True,"chcluster":False,"xqcut":0.0}
LEGACY_BRIDGE = "caa6fbb5560a0069c557bb4253c8bb9dcf46420d5f1c8f69377377dd15a4ed59"
LEGACY_ZH_SOURCE = "526ac2896b4f8951a4514be2e97846cfbbee3d42ef4db047bf180c0ede7a82c6"
LEGACY_SOURCE_ONLY_MANIFEST_SHA = "17c83600f28fa20d6717ac831930a0080ed64cec4ffb7d393d079cca55eac8d8"
LEGACY_SOURCE_CHANGES = {
    "simulation/new_backgrounds/validate_lhe.py":"a229943fd62afbaa71b5676585417e14d2424fa25d7c1191b1e7a1e9443fa3ea",
    "simulation/new_backgrounds/controller.py":"cba865fbfee68bb2eda5aae2d567109612a77d8cd1c93103ae33bbba3489aebe",
    "simulation/new_backgrounds/delphes_stage.py":"a773f3f3302732075e1fc7e1a26ec830f419fca4ffb2044745dbf1e30ab2c991",
    "simulation/new_backgrounds/src/validate_background_hepmc3.cxx":"fbcac365c20f6c4d44dfb57945ab6b6a47354acc500c0dd28a163ae7c2ff0db9",
    "simulation/new_backgrounds/scripts/shower_stage.py":"507ec22e27fe130a08a849e70fa828fa58dcf1fdd32acd47614c0c0c32c2b636",
    "simulation/new_backgrounds/src/analyze_background_root.cxx":"8b6b62770e75c14b5d4ef4a185efa2ca11cf7e5a451136393eae3e121fbbc655",
}
DELPHES_FILENAME_ONLY_SHA = "5d9f91aebe24442debd732028de678b2fc2b9e63ba414344e39739894ac95d60"
DELPHES_REUSE_REPAIR_SHA = "b8e401857dc8f89a235602f5e9aba1b6268058eb1a4443a5e4203afebeff7e82"
ROOT_SIGNED_JET_REPAIR_SHA = "56938c0a3de331d939925ece06ed1ccebee11fdd7472b2c3d096ccd65d62a509"
# Exact reviewed completed repair bytes, tested on preserved genuine prefix10.
READER_STATUS_CONTEXT_SHA = "e0b03c81098fe63b99491e58a3c9979135f389f6a93e8ed7b799cdd97876977f"
SHOWER_PREFIX_REUSE_SHA = "34a3a62762f677939b22050da251adfe709a5b4154c493f9f77523668424c9e6"
NONEXECUTED_REVIEW_ADDITIONS = {
    "simulation/new_backgrounds/scripts/audit_payload.py",
    "simulation/new_backgrounds/scripts/publish_references.py",
    "simulation/new_backgrounds/scripts/validate_references.py",
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


FROZEN = load_module("background_frozen_profiles", REPO/"simulation/zh_pilot/scripts/validate_profiles.py")
CARDS = load_module("background_frozen_cards", REPO/"simulation/zh_pilot/scripts/check_generator.py")
STAGE = load_module("background_mg5_stage", REPO/"simulation/new_backgrounds/mg5_stage.py")
require, decimal, integer = FROZEN.require, FROZEN.decimal, FROZEN.integer


class ValidationError(ValueError):
    def __init__(self, message, report):
        super().__init__(message); self.report = report


def file_sha(path):
    return FROZEN.file_sha(path)


def canonical(text):
    return text.replace("\r\n", "\n").strip()


def parse_xml(raw):
    class Builder(ET.TreeBuilder):
        def __init__(self):super().__init__();self.count=0;self.depth=0
        def start(self,tag,attrs):
            self.count+=1;self.depth+=1
            require(self.count<=10000 and self.depth<=32,"LHE XML node/depth policy exceeded")
            return super().start(tag,attrs)
        def end(self,tag):
            value=super().end(tag);self.depth-=1;return value
    return ET.fromstring(raw,parser=ET.XMLParser(target=Builder()))


def bounded_bytes(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES, "Missing/unsafe/oversized LHE or evidence file")
    before = file_sha(path)
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as stream:
            raw = stream.read(MAX_BYTES+1)
            require(len(raw) <= MAX_BYTES, "Decompressed LHE exceeds bounded 1000-event policy")
            require(stream.read(1) == b"", "Extra data beyond decompression limit")
    except (OSError, EOFError) as error:
        raise ValueError("Gzip CRC/truncation/integrity failure: "+str(error)) from error
    require(file_sha(path) == before, "Input changed during complete read")
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "DTD/entities forbidden")
    return raw, before


def prepared_contract(seed=20261104, process="zh"):
    """Read and bind reviewed request cards without importing/starting MG5."""
    STAGE._request(1000,seed,13000,process)
    inputs=STAGE._frozen_inputs(REPO,events=1000,seed=seed,energy_gev=13000,process=process)
    return {"profile":PROFILES[process], "process":process,
            "process_card":inputs["process.mg5"].decode(), "run_card":inputs["run_card.dat"].decode(),
            "param_card":inputs["param_card.dat"].decode()}


def commands(text):
    return [line.split("#",1)[0].strip() for line in text.splitlines() if line.split("#",1)[0].strip()]


def process_card(text, *, expanded=False, process="zh"):
    lines = commands(text)
    require([s for s in lines if s.startswith("import ")] == [CARDS.MODEL], "Actual source model differs")
    require([s for s in lines if s.startswith(("generate ","add process "))] == [STAGE.PROCESS_COMMANDS[process][-1]],
            "Exact source process/coupling orders differ")
    if not expanded:
        require(lines == STAGE.PROCESS_COMMANDS[process], "Prepared process card changed")
        return
    aliases = [s.partition("=")[2].strip().split() for s in lines if re.match(r"define p\s*=",s)]
    require(aliases, "Missing actual proton definition")
    pdgs = {"g":21,"u":2,"c":4,"d":1,"s":3,"b":5,"u~":-2,"c~":-4,"d~":-1,"s~":-3,"b~":-5}
    last = [pdgs[x] if x in pdgs else integer(x) for x in aliases[-1]]
    require(sorted(last) == [-5,-4,-3,-2,-1,1,2,3,4,5,21], "Effective proton is not reviewed five-flavour scheme")
    j4=[s.partition("=")[2].strip().split() for s in lines if re.match(r"define j4\s*=",s)]
    require((bool(j4) and sorted(pdgs[x] if x in pdgs else integer(x) for x in j4[-1])==[-4,-3,-2,-1,1,2,3,4,21]) if process=="bbgj" else not j4,"Actual j4 parton definition differs")
    fixed = {"group_subprocesses":"Auto","ignore_six_quark_processes":"False","low_mem_multicore_nlo_generation":"False",
             "complex_mass_scheme":"False","include_lepton_initiated_processes":"False","gauge":"unitary",
             "loop_optimized_output":"True","loop_color_flows":"False","max_npoint_for_channel":"0",
             "default_unset_couplings":"99","max_t_for_channel":"99","zerowidth_tchannel":"True",
             "nlo_mixed_expansion":"True","automatic_html_opening":"False","auto_update":"0","nb_core":"1","run_mode":"0"}
    outputs = []
    for line in lines:
        if line.startswith("set "):
            parts=line.split(None,2);require(len(parts)==3,"Malformed actual MG setting")
            key,value=parts[1:]
            if value.endswith(" --no_save"):value=value[:-len(" --no_save")]
            require("--no_save" not in value,"Duplicate/misplaced no-save flag")
            require((key in fixed and value==fixed[key]) or
                    (key in ("fortran_compiler","cpp_compiler") and value and not any(c in value for c in ";\r\n")),
                    "Unknown/changed generator physics or worker setting: "+key)
        elif line.startswith("define "):
            require(line.split()[1] in ("p","j","j4","l+","l-","vl","vl~"),"Unexpected process alias")
        elif line.startswith("output "):
            parts=line.split();require(len(parts)>=2 and all(x in ("-f","-nojpeg") for x in parts[2:]),"Unexpected output command")
            outputs.append(line)
        else:
            require(line in (CARDS.MODEL,STAGE.PROCESS_COMMANDS[process][-1]),"Unexpected source process command")
    require(len(outputs)<=1,"Multiple process exports in actual banner")


def check_cards(actual, prepared, seed, process="zh"):
    require(prepared["profile"]==PROFILES[process] and all(isinstance(prepared[k],str) for k in TAGS),"Incomplete prepared cards")
    process_card(prepared["process_card"],process=process)
    process_card(actual["process_card"],expanded=True,process=process)
    target=prepared_contract(seed,process)
    rv=CARDS.parse_run(actual["run_card"]);expected=CARDS.parse_run(target["run_card"])
    require(CARDS.parse_run(prepared["run_card"])==expected,"Prepared run settings/cuts/count/seed changed")
    require(set(expected)<=set(rv) and set(rv)<=set(expected)|set(OFFICIAL_IMPLICIT_RUN_DEFAULTS),
            "Actual run card is missing an explicit setting or contains an unknown extra")
    require(all(rv[key]==value for key,value in expected.items()),"Actual explicit run physics/request setting differs")
    for key,value in OFFICIAL_IMPLICIT_RUN_DEFAULTS.items():
        if key in rv:
            require(rv[key]==value and (type(rv[key]) is type(value) if type(value) in (bool,int) else type(rv[key]) in (int,float)),
                    "Actual official implicit run default differs: "+key)
    params=CARDS.parse_param(target["param_card"])
    require(CARDS.parse_param(prepared["param_card"])==params and CARDS.parse_param(actual["param_card"])==params,
            "Actual complete mass/width/EW/Yukawa param card differs")
    return rv


def header_data(header):
    require(header.tag=="header", "Missing header")
    for tag in ["MGVersion","MGGenerationInfo","MGProcCard",*TAGS.values()]:
        require(len(header.findall(tag))==1,"Missing/duplicate banner declaration: "+tag)
    require(header.findtext("MGVersion","").strip()=="3.5.16","Wrong MG5 version")
    cards={key:header.findtext(tag) for key,tag in TAGS.items()}
    generation=header.findtext("MGGenerationInfo","")
    counts=re.findall(r"Number of Events\s*:\s*(\d+)",generation)
    sigmas=re.findall(r"Integrated weight \(pb\)\s*:\s*([^\s]+)",generation)
    require(len(counts)==len(sigmas)==1,"Missing/ambiguous complete generation banner")
    require(integer(counts[0])==1000 and decimal(sigmas[0])>0,"Banner count/cross section invalid")
    return cards,decimal(sigmas[0]),sigmas[0]


def init_data(init):
    require(not init.attrib,"Unexpected init attributes")
    rows=FROZEN.records(init.text or "");require(rows and len(rows[0])==10,"Malformed LHE init")
    row=rows[0]
    require([integer(x) for x in row[:2]]==[2212,2212] and [decimal(x) for x in row[2:4]]==[Decimal(6500)]*2,
            "Wrong proton beams/13-TeV energy")
    require([integer(x) for x in row[4:8]]==[0,0,10042,10042] and integer(row[8])==-4 and integer(row[9])==1,
            "PDF/group/source weight strategy/subprocess count changed")
    require(len(rows)==2 and len(rows[1])==4,"Incomplete init subprocess record")
    generator=init.findall("generator")
    require(len(generator)==1 and generator[0].get("name")=="MadGraph5_aMC@NLO" and generator[0].get("version")=="3.5.16",
            "Init generator identity missing/wrong")
    sigma,error,maximum=[decimal(x) for x in rows[1][:3]];pid=integer(rows[1][3])
    require(sigma>0 and error>=0 and maximum>0 and pid>0,"Invalid source cross section/error/max/process ID")
    return {"sigma":sigma,"uncertainty":error,"maximum":maximum,"process_id":pid,"sigma_token":rows[1][0],"error_token":rows[1][1]}


def half_print_unit(token, *, significant_digits=None):
    value=decimal(token)
    if significant_digits is not None and not value:return Decimal(0)
    exponent=value.adjusted()-significant_digits+1 if significant_digits is not None and value else value.as_tuple().exponent
    return Decimal(5).scaleb(exponent-1)


def parse_run_log(text,process="zh"):
    return STAGE.parse_generation_summary(text,process)


def bound_artifact(item):
    require(isinstance(item,dict) and isinstance(item.get("path"),str) and isinstance(item.get("sha256"),str) and SHA.fullmatch(item["sha256"]),"Missing artifact binding")
    path=Path(item["path"])
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=MAX_BYTES and file_sha(path)==item["sha256"],"Artifact bytes changed/missing/unsafe")
    return path


def compare_historical_source_bindings(original,current):
    """Pure file-list comparison; this alone never establishes provenance."""
    def mapping(entries):
        require(isinstance(entries,list) and entries,"Missing historical source file list")
        result={}
        for row in entries:
            require(isinstance(row,dict) and set(row)=={"path","sha256"} and isinstance(row["path"],str) and
                    isinstance(row["sha256"],str) and SHA.fullmatch(row["sha256"]),"Invalid historical source binding")
            path=Path(row["path"])
            require(not path.is_absolute() and ".." not in path.parts and row["path"]==path.as_posix() and row["path"] not in result,
                    "Duplicate/unsafe historical source path")
            result[row["path"]]=row["sha256"]
        return result
    old,new=mapping(original),mapping(current)
    require(set(old)<=set(new),"Historical executable source binding disappeared")
    additions=set(new)-set(old)
    require(additions<=NONEXECUTED_REVIEW_ADDITIONS,"Unreviewed new executable/configuration in historical recheck")
    changes=[]
    for path,value in old.items():
        if new[path]!=value:
            require(path in LEGACY_SOURCE_CHANGES and value==LEGACY_SOURCE_CHANGES[path],
                    "Original executed generator/physics/native source changed: "+path)
            role="READ_ONLY_VALIDATOR_OR_DOWNSTREAM_RESUME_CONTROLLER_ONLY"
            if path=="simulation/new_backgrounds/delphes_stage.py":
                require(new[path]==DELPHES_REUSE_REPAIR_SHA,"Delphes change exceeds exact relative-output and non-generating ROOT10/100 reuse repairs")
                role="DOWNSTREAM_RELATIVE_OUTPUT_AND_NON_GENERATING_ROOT10_100_REUSE"
            elif path=="simulation/new_backgrounds/src/validate_background_hepmc3.cxx":
                require(new[path]==READER_STATUS_CONTEXT_SHA,"Reader change exceeds exact read-only Event-context status repair")
                role="READ_ONLY_STATUS_CONTEXT_FIX"
            elif path=="simulation/new_backgrounds/scripts/shower_stage.py":
                require(new[path]==SHOWER_PREFIX_REUSE_SHA,"Shower helper change exceeds exact non-generating prefix10 reuse repair")
                role="NON_GENERATING_PREFIX10_REUSE"
            elif path=="simulation/new_backgrounds/src/analyze_background_root.cxx":
                require(new[path]==ROOT_SIGNED_JET_REPAIR_SHA,"ROOT analyzer change exceeds exact native signed-jet numerical validation repair")
                role="READ_ONLY_NATIVE_SIGNED_JET_NUMERICAL_VALIDATION_FIX_NO_MC"
            changes.append({"path":path,"original_sha256":value,"current_sha256":new[path],"role":role})
    return changes,sorted(additions)


def check_original_source_only_manifest(manifest):
    """Zero downstream physical execution guard; never a sample acceptance."""
    require(type(manifest.get("MG5_events_generated")) is int and manifest["MG5_events_generated"]==1000,
            "Historical source does not contain the exact original1000 MG5 events")
    counters=("Pythia_events_attempted","Pythia_events_written","HepMC_validated_events","Delphes_ROOT_entries")
    require(all(type(manifest.get(key)) is int and manifest[key]==0 for key in counters),
            "Historical source had prior downstream physical events; read-only exceptions unavailable")
    downstream={name+stage for name in ("shower_background_","background_reader_") for stage in ("prefix10","prefix100","full1000")}
    require(not any(row["stage"] in downstream or row["stage"].startswith("delphes_") for row in manifest["stages_attempted"]),
            "Historical source had a prior physical shower/reader/Delphes attempt")


def historical_bridge_binding(ticket,source_path,current_entries):
    """Read-only, one known produced source; no generic old-bridge bypass.

    The exact original task, source SHA, complete original source-list digest,
    request, frozen generator/cards/native implementations and reviewed repair
    files must all bind. The original execution plan/authority remain untouched.
    This never authorizes fresh MG5 events or a downstream run.
    """
    require(ticket["bridge_sha256"]==LEGACY_BRIDGE and file_sha(source_path)==LEGACY_ZH_SOURCE,
            "Unreviewed historical bridge/source identity")
    req=ticket["request"]
    require(req["process"]=="zh" and req["events"]==1000 and req["seed"]==20261104 and req["energy_gev"]==13000,
            "Historical source request differs from the one verified ZH production")
    plan_path=Path(req["output"])/"execution_plan.json"
    require(plan_path.is_file() and not plan_path.is_symlink() and plan_path.stat().st_size<=MAX_BYTES,"Missing preserved original execution plan")
    before=file_sha(plan_path);plan=FROZEN.load_json(plan_path)
    require(plan["task"]=="PHASE6G_THREE_NEW_BACKGROUNDS_FULL_CHAIN_1K_V1" and plan["status"]=="PREPARED_TEXT_ONLY" and
            plan["reviewed_base_head"]==ticket["reviewed_base_head"] and plan["authorization_source_sha256"]==AUTHORIZATION_ATTACHMENT_SHA256 and
            plan["request"]==req and plan["profile"]==PROFILES["zh"] and plan["bridge_sha256"]==LEGACY_BRIDGE,
            "Historical preserved plan/request/authority differs")
    entries=plan["bridge_sources"]
    require(hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(",",":")).encode()).hexdigest()==LEGACY_BRIDGE,
            "Original complete source-list digest differs from pinned executed bridge")
    changes,additions=compare_historical_source_bindings(entries,current_entries)
    manifest_binding={}
    downstream_repairs={"simulation/new_backgrounds/delphes_stage.py","simulation/new_backgrounds/src/analyze_background_root.cxx",
                        "simulation/new_backgrounds/src/validate_background_hepmc3.cxx",
                        "simulation/new_backgrounds/scripts/shower_stage.py"}
    if any(row["path"] in downstream_repairs for row in changes):
        manifest_path=Path(req["output"])/"run_manifest.json"
        require(manifest_path.is_file() and not manifest_path.is_symlink() and manifest_path.stat().st_size<=MAX_BYTES,
                "Missing original source-only run manifest")
        manifest_sha=file_sha(manifest_path)
        require(manifest_sha==LEGACY_SOURCE_ONLY_MANIFEST_SHA,"Original pinned source-only manifest changed")
        manifest=FROZEN.load_json(manifest_path)
        check_original_source_only_manifest(manifest)
        require(file_sha(manifest_path)==manifest_sha,"Original source-only manifest changed during recheck")
        manifest_binding={"original_source_only_manifest":{"path":str(manifest_path),"sha256":manifest_sha,"bytes":manifest_path.stat().st_size}}
    require(file_sha(plan_path)==before,"Historical execution plan changed during read-only recheck")
    return {"status":"PASS_PINNED_HISTORICAL_SOURCE_BINDING_ONLY","original_bridge_sha256":LEGACY_BRIDGE,
            "original_execution_plan_sha256":before,"original_lhe_sha256":LEGACY_ZH_SOURCE,
            "original_execution_plan":{"path":str(plan_path),"sha256":before,"bytes":plan_path.stat().st_size},
            **manifest_binding,
            "reviewed_source_changes":changes,"current_nonexecuted_review_additions":additions,
            "scope":"One preserved actual ZH1000 source; generator/cards/shower runner/physics header unchanged. Exact implicit-default parser, downstream controller, relative ROOT output filename, reader Event-context status, non-generating shower10/ROOT10/100 reuse and native signed-jet numerical validation repairs only. Original source-only manifest has zero downstream physical events. No production permission or new events implied."}


def check_provenance(provenance,prepared,seed,header_raw,init,source_path,process="zh"):
    require(isinstance(provenance,dict) and type(provenance.get("schema_version")) is int and provenance["schema_version"]==1,
            "Physical source provenance required")
    request=provenance["request"]
    require(request["profile"]==PROFILES[process] and request["process"]==process and type(request["events"]) is int and request["events"]==1000 and
            type(request["seed"]) is int and request["seed"]==seed and decimal(request["energy_gev"])==13000,"Source request differs")
    identity=provenance["source_identity"]
    require(all(identity.get(k)==v for k,v in SOURCE_IDENTITY.items() if k!="mg5_version") and
            identity.get("mg5_version",identity.get("version"))=="3.5.16" and
            ("version" not in identity or identity["version"]=="3.5.16"),"Unverified official source identity")
    auth=provenance["authorization_receipt"]
    require(isinstance(auth.get("id"),str) and auth["id"],"Missing authorization receipt identity")
    auth_path=bound_artifact(auth)
    ticket=FROZEN.load_json(auth_path)
    require(ticket["status"]=="AUTHORIZED_TASK_ATTACHMENT" and ticket["authorization_command"]=="PHASE6G_THREE_NEW_BACKGROUNDS_FULL_CHAIN_1K_V1" and
            ticket["attachment_sha256"]==AUTHORIZATION_ATTACHMENT_SHA256 and ticket["profile"]==PROFILES[process] and
            ticket["campaign_id"]==auth["id"] and str(uuid.UUID(ticket["campaign_id"]))==ticket["campaign_id"] and
            ticket["reviewed_base_head"]=="05cff9a5d991ba6782b339bc41932ae4da296d8c","Missing/contradictory explicit authorization content")
    require(auth_path.name=="authorization.json","Wrong preserved authority artifact")
    start=datetime.fromisoformat(ticket["authorized_at_utc"])
    require(start.tzinfo is not None,"Malformed authorization date")
    auth_request=ticket["request"]
    require(auth_request["process"]==process and type(auth_request["events"]) is int and auth_request["events"]==1000 and
            type(auth_request["seed"]) is int and auth_request["seed"]==seed and type(auth_request["energy_gev"]) is int and auth_request["energy_gev"]==13000,
            "Authorization/source request differs")
    require(Path(source_path).resolve().is_relative_to(Path(auth_request["output"]).resolve()),"Source outside authorized output")
    common=load_module("background_readonly_authorization",REPO/"simulation/new_backgrounds/common.py")
    bridge_sha,current_entries=common.bridge_identity()
    bridge_binding={"status":"PASS_CURRENT_EXECUTED_SOURCE_BINDING","bridge_sha256":bridge_sha}
    if ticket["bridge_sha256"]!=bridge_sha:
        bridge_binding=historical_bridge_binding(ticket,source_path,current_entries)
    require(type(auth_request["max_hours"]) in (int,float) and 0<float(auth_request["max_hours"])<=4 and
            type(auth_request["max_disk_gb"]) in (int,float) and 0<float(auth_request["max_disk_gb"])<=10,"Unbounded source execution budgets")
    reservation=Path(auth_request["output"])/"source_attempt_reservation.json"
    require(reservation.is_file() and not reservation.is_symlink(),"Missing one-source-attempt reservation")
    reserved=FROZEN.load_json(reservation)
    require(reserved["campaign_id"]==ticket["campaign_id"] and reserved["status"]=="RESERVED_ONE_SOURCE_ATTEMPT_NOT_GENERATION_PROOF", "Wrong one-source-attempt reservation")
    artifacts=provenance["artifacts"]
    paths={key:bound_artifact(artifacts[key]) for key in ("banner","run_log","prepared_process","prepared_run","prepared_param","lhe_gz")}
    require(paths["lhe_gz"].resolve()==Path(source_path).resolve(),"Validated LHE is not the executor's exact output artifact")
    for key,name in (("prepared_process","process_card"),("prepared_run","run_card"),("prepared_param","param_card")):
        require(paths[key].read_bytes()==prepared[name].encode("utf-8"),"Prepared artifact/card text mismatch")
    banner=paths["banner"].read_bytes();require(b"<!DOCTYPE" not in banner.upper() and b"<!ENTITY" not in banner.upper(),"Invalid banner entities")
    require(HEADER.findall(banner)==[header_raw],"Standalone complete banner differs from LHE header bytes")
    parsed=parse_xml(banner)
    require(parsed.tag=="LesHouchesEvents" and parsed.get("version")=="3.0" and len(parsed)==1 and parsed[0].tag=="header",
            "Standalone banner schema/content differs")
    log=parse_run_log(paths["run_log"].read_text(encoding="utf-8"),process)
    for key,actual,token in (("cross_section_pb",init["sigma"],init["sigma_token"]),("uncertainty_pb",init["uncertainty"],init["error_token"])):
        require(decimal(log[key])!=0 or actual==0,"A zero %.4g log value cannot hide a nonzero init value")
        require(abs(decimal(log[key])-actual)<=half_print_unit(log[key],significant_digits=4)+half_print_unit(token),
                "Independent actual run log/init "+key+" differs beyond printed precision")
    generation=provenance["generation"]
    require(type(generation["events"]) is int and generation["events"]==1000 and
            generation["precision"]==log["precision"] and all(decimal(generation[k])==decimal(log[k]) for k in ("cross_section_pb","uncertainty_pb")),
            "Stage result not backed by independently parsed actual run log")
    bindings={key:dict(artifacts[key]) for key in paths};bindings["authorization_receipt"]=dict(auth)
    if "original_execution_plan" in bridge_binding:bindings["original_execution_plan"]=bridge_binding["original_execution_plan"]
    if "original_source_only_manifest" in bridge_binding:bindings["original_source_only_manifest"]=bridge_binding["original_source_only_manifest"]
    amplitude=bound_artifact(provenance["amplitude_validation"])
    amp=FROZEN.load_json(amplitude)
    expected=STAGE._amplitude_contract(REPO,{"run_card.dat":prepared["run_card"].encode()},process)
    require(amp["status"]=="PASS_ACTUAL_TREE_AMPLITUDES_AND_OFFICIAL_CARDS" and amp["process"]==process and
            amp["profile"]==PROFILES[process] and amp["source_commit"]==SOURCE_IDENTITY["source_commit"] and
            amp["actual_parameters"]==expected["model_parameters"] and amp["official_run_readback"]==expected["official_run_checks"], "Missing/changed actual preintegration amplitude/card gate")
    validate_amplitude_records(amp["amplitude_records"],process)
    bindings["amplitude_validation"]=dict(provenance["amplitude_validation"])
    return {"status":"BOUND_ACTUAL_EXECUTOR_PROVENANCE","source_identity":identity,"authorization_receipt_id":auth["id"],
            "authorization_receipt_sha256":file_sha(auth_path),"artifacts":bindings,"independent_run_log_summary":log,"execution_bridge_binding":bridge_binding,
            "authorization_scope":"Executor validates authorized human attachment, request/output/bundle and one-source-attempt reservation; this read-only check verifies preserved binding, never grants authorization"}


def validate_amplitude_records(records,process):
    require(isinstance(records,list) and records,"Missing actual amplitude records")
    decays=0
    for row in records:
        require(type(row["diagram_count"]) is int and row["diagram_count"]>0,"Missing retained tree diagrams")
        incoming,final=sorted(row["initial_pdgs"]),sorted(row["final_pdgs"])
        if row["scope"]=="Z_decay":
            require(process=="zh" and incoming==[23] and final==[-5,5] and row["actual_amplitude_orders"]==[{"QCD":0,"QED":1}],"Wrong actual Z decay amplitude")
            decays+=1
        else:
            require(row["scope"]=="production" and row["actual_amplitude_orders"]==[STAGE.PRODUCTION_ORDERS[process]],"Wrong actual production amplitude order")
            if process=="zh":require(incoming in [[-i,i] for i in range(1,6)] and final==[23,25],"Wrong qqbar ZH amplitude")
            elif process=="tth":require(incoming in [[21,21]]+[[-i,i] for i in range(1,6)] and final==[-6,6,25],"Wrong QCD ttH amplitude")
            else:
                require(len(incoming)==2 and all(i in [-5,-4,-3,-2,-1,1,2,3,4,5,21] for i in incoming) and
                        len(final)==4 and all(final.count(i)==1 for i in (5,-5,22)) and
                        next(i for i in final if i not in (5,-5,22)) in [-4,-3,-2,-1,1,2,3,4,21],"Wrong one-photon bbj amplitude")
    require((process=="zh")==bool(decays),"Missing/unexpected source decay amplitude")


def event_particles(event,process,physics):
    """Independent full record gate for three fixed Born topologies."""
    if process=="zh":return FROZEN.event_particles(event,"ZH_ZBB_STABLE_H",physics)
    rows=FROZEN.records(event.text or "")
    require(rows and len(rows[0])==6,"Malformed LHE event header")
    nup,pid=[integer(x) for x in rows[0][:2]]
    weight,scale,aqed,aqcd=[decimal(x) for x in rows[0][2:]]
    require(nup==(5 if process=="tth" else 6) and len(rows)==nup+1 and scale>0 and aqed>0 and aqcd>0,"Source count/scale/couplings invalid")
    require(FROZEN.close(scale,physics["scales"]["muR_gev"]),"Source scale differs from fixed process-specific prescription")
    particles=[];colors=Counter()
    for index,row in enumerate(rows[1:],1):
        require(len(row)==13,"Malformed source particle")
        pdg,status,m1,m2,c1,c2=[integer(x) for x in row[:6]]
        values=[float(decimal(x)) for x in row[6:]]
        px,py,pz,energy,mass,lifetime,spin=values
        require(status in (-1,1) and energy>0 and mass>=0 and lifetime>=0 and (abs(spin)<=1 or spin==9),"Invalid source particle metadata/status")
        require((m1,m2)==(0,0) if status==-1 else (m1,m2)==(1,2),"Unexpected/cyclic source mothers")
        require(c1>=0 and c2>=0,"Negative color ID")
        if 1<=abs(pdg)<=6:
            require((c1>0 and c2==0) if pdg>0 else (c1==0 and c2>0),"Quark color/sign mismatch")
            require(FROZEN.close(mass,173) if abs(pdg)==6 else mass==0,"Wrong top or restricted massless-quark mass")
        elif pdg==21:require(c1>0 and c2>0 and c1!=c2 and mass==0,"Invalid massless-gluon color")
        else:require(pdg in (22,25) and c1==c2==0 and (mass==0 if pdg==22 else FROZEN.close(mass,125)),"Unexpected/colored photon or Higgs")
        p2=math.fsum((px*px,py*py,pz*pz))
        require(abs(energy*energy-p2-mass*mass)<=1e-6+5e-9*max(energy*energy,p2,mass*mass,1),"Particle mass-shell failure")
        direction=-1 if status==-1 else 1
        if c1:colors[c1]+=direction
        if c2:colors[c2]-=direction
        particles.append({"id":index,"pdg_id":pdg,"status":status,"mothers":list(range(m1,m2+1)) if m1 else [],"p4_gev":values[:4],"mass_gev":mass})
    incoming=[p for p in particles if p["status"]==-1];final=[p for p in particles if p["status"]==1]
    require(len(incoming)==2 and [p["id"] for p in incoming]==[1,2] and all(p["pdg_id"] in [-5,-4,-3,-2,-1,1,2,3,4,5,21] for p in incoming),"Wrong source incoming partons")
    require(all(p["p4_gev"][0]==p["p4_gev"][1]==0 and p["p4_gev"][3]<=6500+1e-6 for p in incoming) and incoming[0]["p4_gev"][2]>0>incoming[1]["p4_gev"][2],"Wrong collinear source beams")
    if process=="tth":
        require(sorted(p["pdg_id"] for p in incoming) in [[21,21]]+[[-i,i] for i in range(1,6)] and Counter(p["pdg_id"] for p in final)==Counter([6,-6,25]),"Wrong stable ttH Born topology")
    else:
        require(len(final)==4 and all(sum(p["pdg_id"]==i for p in final)==1 for i in (5,-5,22)) and
                next(p["pdg_id"] for p in final if p["pdg_id"] not in (5,-5,22)) in [-4,-3,-2,-1,1,2,3,4,21],"bbgj needs exactly b/bbar/one Born photon/one j4")
        for p in final:
            px,py,pz,energy=p["p4_gev"];pt=math.hypot(px,py)
            require(pt>=25-1e-6 and abs(math.asinh(pz/pt))<=2.5+1e-6,"bbgj pT/eta generation-cut failure")
        for i,a in enumerate(final):
            for b in final[i+1:]:
                ax,ay,az,_=a["p4_gev"];bx,by,bz,_=b["p4_gev"]
                delta_phi=math.remainder(math.atan2(ay,ax)-math.atan2(by,bx),2*math.pi)
                delta_eta=math.asinh(az/math.hypot(ax,ay))-math.asinh(bz/math.hypot(bx,by))
                require(math.hypot(delta_eta,delta_phi)>=0.4-1e-6,"bbgj all-parton/photon DeltaR cut failure")
    require(all(v==0 for v in colors.values()),"Source color-flow conservation failure")
    residual=max(abs(math.fsum(p["p4_gev"][k] for p in incoming)-math.fsum(p["p4_gev"][k] for p in final)) for k in range(4))
    require(residual<=1e-6+5e-9*sum(p["p4_gev"][3] for p in incoming),"Global source four-momentum closure failure")
    return {"process_id":pid,"weight":weight,"particles":particles,"closure_residual_gev":residual}


def assess_event(element,index,raw,physics,init,process="zh"):
    require(not element.attrib,"Unexpected event attributes")
    value=event_particles(element,process,physics)
    require(value["process_id"]==init["process_id"],"Unknown event process ID")
    rows=FROZEN.records(element.text or "")
    require(FROZEN.close(decimal(rows[0][4]),Decimal(1)/decimal(physics["electroweak_inputs"]["aEWM1"]),1e-12,5e-9),"Event alpha_EW inconsistent with card input")
    require(0<decimal(rows[0][5])<1,"Nonphysical/missing source alpha_s header")
    ids=[]
    for weight in element.findall(".//wgt"):
        require(isinstance(weight.get("id"),str) and weight.get("id"),"Missing auxiliary weight ID")
        ids.append(weight.get("id"));decimal(weight.text or "")
    require(len(ids)==len(set(ids)),"Duplicate auxiliary weight ID")
    shell=0.
    for p in value["particles"]:
        px,py,pz,e=p["p4_gev"]
        shell=max(shell,abs(e*e-math.fsum((px*px,py*py,pz*pz))-p["mass_gev"]**2))
    anchors={name:next(p["id"] for p in value["particles"] if p["pdg_id"]==pdg) for name,pdg in ({"zh":(("Z",23),("H",25),("b",5),("bbar",-5)),"tth":(("H",25),("t",6),("tbar",-6)),"bbgj":(("b",5),("bbar",-5),("photon",22))}[process])}
    if process=="bbgj":anchors["jet"]=next(p["id"] for p in value["particles"] if p["status"]==1 and p["pdg_id"] not in (5,-5,22))
    return {"source_event_index":index,"source_event_content_hash":hashlib.sha256(raw).hexdigest(),
            "nominal_generator_weight":str(value["weight"]),"scale_gev":rows[0][3],"aqed":rows[0][4],"aqcd":rows[0][5],
            "rows":rows,"original_resonance_and_bottom_ids":anchors,"particles":value["particles"],
            "closure_residual_gev":value["closure_residual_gev"],"mass_shell_residual_gev2":shell}


def validate_file(path,expected_events=1000,expected_seed=20261104,profile=PROFILE,card_contract=None,provenance=None,*,method_only=False,process=None):
    """Validate actual LHE records against exact future executor evidence.

    A physical result is PASS_LHE_RECORDS only, separate from missing H-decay
    normalization/native stages. Missing/contradictory evidence fails closed.
    ValidationError.report retains observed assessment counts and failures.
    """
    report={"schema_version":1,"status":"FAILED_PHYSICAL_VALIDATION","profile":profile,"physical_acceptance":False,
            "expected_events":expected_events,"source_total_events":None,"actual_events":None,"events_assessed":0,
            "events_valid":0,"events_invalid":0,"events_not_assessed":None,"event_failures":[],
            "normalization_scope":"RAW_GENERATED_SOURCE; model BR adjustment requires later actual weight closure",
            "physical_BR_adoption":"NONE_AT_SOURCE_STAGE","exclusive_physical_normalization":"PENDING_DOWNSTREAM_WEIGHT_CLOSURE"}
    try:
        if process is not None:
            require(process in PROFILES and profile in (PROFILE,PROFILES[process]),"Process/profile mismatch")
            profile=PROFILES[process];report["profile"]=profile
        require(type(method_only) is bool and profile in PROFILES.values() and type(expected_events) is int and expected_events==1000,
                "Only reviewed background profiles with full original1000 supported")
        process=next(key for key,value in PROFILES.items() if value==profile)
        require(type(expected_seed) is int and 1<=expected_seed<=900000000,"Invalid expected seed")
        prepared=prepared_contract(expected_seed,process) if card_contract is None else card_contract
        require(method_only or card_contract is not None,"Physical validation requires exact executor prepared cards")
        raw,source_sha=bounded_bytes(path)
        report.update(source_file_sha256=source_sha,compressed_file_sha256=source_sha if Path(path).suffix==".gz" else None,
                      decompressed_file_sha256=hashlib.sha256(raw).hexdigest(),decompressed_bytes=len(raw))
        try:root=parse_xml(raw)
        except ET.ParseError as error:raise ValueError("Complete LHE XML/truncation failure: "+str(error)) from error
        require(root.tag=="LesHouchesEvents" and root.attrib=={"version":"3.0"},"Wrong LHE root/version/schema")
        require(len(root.findall("header"))==len(root.findall("init"))==1 and
                root[0].tag=="header" and root[1].tag=="init" and all(e.tag=="event" for e in root[2:]),"Duplicate/missing/out-of-order LHE sections")
        header=root[0];scope=header.findall("ZHFixtureScope")+header.findall("BackgroundFixtureScope")
        require((len(scope)==1 and scope[0].text=="METHOD_ONLY") if method_only else not scope,
                "Synthetic METHOD_ONLY fixture cannot receive physical acceptance; method declaration required")
        actual,banner_sigma,banner_token=header_data(header)
        rv=check_cards(actual,prepared,expected_seed,process)
        init=init_data(root[1]);header_raws=HEADER.findall(raw)
        require(len(header_raws)==1,"Missing/ambiguous raw complete banner")
        require(abs(banner_sigma-init["sigma"])<=half_print_unit(banner_token)+half_print_unit(init["sigma_token"]),
                "Banner/init integrated cross section differs beyond printed precision")
        report.update(cross_section_pb=str(init["sigma"]),cross_section_uncertainty_pb=str(init["uncertainty"]),
                      banner_cross_section_pb=str(banner_sigma),idwtup=-4,beam_energies_gev=[6500,6500],seed=rv["iseed"],
                      actual_cards=actual,card_hashes={k:hashlib.sha256(v.encode()).hexdigest() for k,v in actual.items()},
                      header_sha256=hashlib.sha256(header_raws[0]).hexdigest(),run_values=rv,
                      source_included_decay_ids=["Z_to_b_bbar"] if process=="zh" else [],missing_decay_ids=["H_to_gamma_gamma"] if process!="bbgj" else [])
        report["provenance"]={"status":"SYNTHETIC_METHOD_ONLY_NOT_GENERATOR_PROOF"} if method_only else check_provenance(provenance,prepared,expected_seed,header_raws[0],init,path,process)
        elements=list(root[2:]);raw_events=EVENT.findall(raw)
        require(len(elements)==len(raw_events),"Exact raw event boundaries/complete XML count differ")
        report.update(actual_events=len(elements),source_total_events=len(elements),events_not_assessed=len(elements))
        source_events=[];weights=[];physics=CARDS.validate_bundle()["physics"]
        physics={**physics,"scales":{**physics["scales"],"muR_gev":STAGE.RUN_OVERRIDES[process].get("scale",216.188)}}
        for index,(element,event_raw) in enumerate(zip(elements,raw_events),1):
            report["events_assessed"]+=1;report["events_not_assessed"]-=1
            try:
                assessed=assess_event(element,index,event_raw,physics,init,process)
                source_events.append(assessed);weights.append(decimal(assessed["nominal_generator_weight"]));report["events_valid"]+=1
            except (ValueError,KeyError,TypeError,OverflowError) as error:
                report["events_invalid"]+=1;report["event_failures"].append({"source_event_index":index,"source_event_sha256":hashlib.sha256(event_raw).hexdigest(),"error":str(error)})
        report["source_events"]=source_events
        report["event_content_sha256"]=hashlib.sha256(b"".join(raw_events)).hexdigest()
        require(len(elements)==1000,"Actual event count differs from original1000; no replacement/removal permitted")
        require(report["events_invalid"]==0,"Invalid LHE event records: "+str(report["events_invalid"]))
        with localcontext() as ctx:
            ctx.prec=60;total=sum(weights,Decimal(0));mean=total/1000
            variance=sum((w-mean)**2 for w in weights)/999;se=(variance/1000).sqrt()
            printed=half_print_unit(init["sigma_token"])+sum(half_print_unit(e["rows"][0][2]) for e in source_events)/1000
            require(abs(mean-init["sigma"])<=init["uncertainty"]+3*se+printed,"Signed nominal mean/init cross-section closure failed")
            report["weights"]={"sum_pb":str(total),"mean_pb":str(mean),"sum_abs_pb":str(sum(abs(w) for w in weights)),
                "sum_squared_pb2":str(sum(w*w for w in weights)),"source_event_sampling_se_pb":str(se),
                "negative_count":sum(w<0 for w in weights),"zero_count":sum(w==0 for w in weights),
                "full_original_source_denominator":1000,"normalization":"Each preserved raw XWGTUP_pb divided once by original1000",
                "closure_scope":"Printed precision plus reported integration error and three event-level sampling SE; not precision cross-section acceptance"}
        report.update(maximum_closure_residual_gev=max(e["closure_residual_gev"] for e in source_events),
                      maximum_mass_shell_residual_gev2=max(e["mass_shell_residual_gev2"] for e in source_events),
                      distinct_source_event_hashes=len({e["source_event_content_hash"] for e in source_events}),
                      independence_scope="Generator run/seed provenance; record-level hashes do not prove statistical independence")
        require(file_sha(path)==source_sha,"Source changed during validation")
        if not method_only:
            for binding in report["provenance"]["artifacts"].values():bound_artifact(binding)
        report.update(status="METHOD_ONLY" if method_only else "PASS_LHE_RECORDS",physical_acceptance=not method_only,
                      physical_pilot_acceptance="NOT_EVALUATED",validation_scope="Complete process-specific source records, not shower/BR/native acceptance")
        return report
    except (OSError,ValueError,KeyError,TypeError,OverflowError,ET.ParseError) as error:
        report["error"]=str(error);report["status"]="FAILED_METHOD_ONLY" if method_only else "FAILED_PHYSICAL_VALIDATION"
        raise ValidationError(str(error),report) from error


def iter_lhe_events(path):
    """Exact source event elements compatible with the frozen source-index API.

    Call after complete validate_file acceptance; this iterator alone is not
    a physics/provenance validator. Original bytes are never reserialized.
    """
    raw,before=bounded_bytes(path)
    for index,match in enumerate(EVENT.finditer(raw),1):
        event_raw=match.group();element=ET.fromstring(event_raw);rows=FROZEN.records(element.text or "")
        require(rows and len(rows[0])==6,"Malformed source header")
        yield {"source_event_index":index,"source_event_content_hash":hashlib.sha256(event_raw).hexdigest(),"raw":event_raw,
               "nominal_generator_weight":float(decimal(rows[0][2])),"scale_gev":float(decimal(rows[0][3])),"rows":rows}
    require(file_sha(path)==before,"Source changed during event iteration")


def validate_downstream_binding(source,records,*,expected_output_count,method_only=False):
    """Identity/nominal-column algebra only; actual ReaderAscii QA is separate.

    No inference about an embedded H BR is made. Preserve Info/converter values
    even if different from raw LHE, and leave exclusive normalization blocked.
    """
    require(type(method_only) is bool and type(expected_output_count) is int and expected_output_count in (10,100,1000),"Wrong smoke/full scope")
    require(source["status"]==("METHOD_ONLY" if method_only else "PASS_LHE_RECORDS") and source["source_total_events"]==1000,
            "Missing full original source validation")
    require(isinstance(records,list) and len(records)==expected_output_count,"Missing downstream original-source outputs")
    original={e["source_event_index"]:e for e in source["source_events"]};seen=set()
    names=["input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb","converter_weight_0_pb"]
    for row in records:
        require(row.get("fixture_scope")=="METHOD_ONLY" if method_only else "fixture_scope" not in row,"Synthetic/physical downstream scope mismatch")
        index=integer(row["source_event_index"]);require(index in original and index not in seen,"Missing/duplicate downstream source index")
        seen.add(index);event=original[index]
        require(row["source_file_sha256"]==source["source_file_sha256"] and row["source_event_sha256"]==event["source_event_content_hash"] and
                type(row["source_total_events"]) is int and row["source_total_events"]==1000,"Source identity/denominator mismatch")
        weight_names=row["weight_names"];values=row["weight_values"]
        require(isinstance(weight_names,list) and isinstance(values,list) and weight_names[:4]==names and len(weight_names)==len(values) and 4<=len(weight_names)<=259 and
                weight_names[4:]==["converter_weight_"+str(i)+"_pb" for i in range(1,len(weight_names)-3)],"Actual named vector mismatch")
        weights=[decimal(v) for v in values];raw=decimal(event["nominal_generator_weight"])
        require(FROZEN.close(weights[0],raw/1000,1e-15,1e-12) and FROZEN.close(weights[1],raw,1e-15,1e-12) and
                FROZEN.close(weights[2],weights[3],1e-15,1e-12),"Raw/Info/converter source-normalization mismatch")
    require(seen==set(range(1,expected_output_count+1)),"Output is not exact original prefix/full source set")
    return {"status":"METHOD_ONLY" if method_only else "PASS_SOURCE_BINDING_ONLY","source_total_events":1000,
            "output_events":len(records),"independent_additional_hard_events":0,"exclusive_physical_normalization":"BLOCKED_BR_WEIGHT_CLOSURE",
            "actual_ReaderAscii_physics_validation":"SEPARATELY_REQUIRED_NOT_IMPLIED","physical_BR_adoption":"SEPARATE_DOWNSTREAM_CLOSURE_REQUIRED"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file",type=Path,required=True);parser.add_argument("--events",type=int,default=1000)
    parser.add_argument("--seed",type=int,default=20261104);parser.add_argument("--process",choices=list(PROFILES),default="zh");parser.add_argument("--cards",type=Path)
    parser.add_argument("--provenance",type=Path);parser.add_argument("--method-only",action="store_true")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    try:
        value=validate_file(args.file,args.events,args.seed,profile=PROFILES[args.process],card_contract=FROZEN.load_json(args.cards) if args.cards else None,
                            provenance=FROZEN.load_json(args.provenance) if args.provenance else None,method_only=args.method_only)
        rc=0
    except ValidationError as error:value=error.report;rc=2
    if args.report:
        with args.report.open("x",encoding="utf-8",newline="\n") as stream:stream.write(json.dumps(value,indent=2,allow_nan=False)+"\n")
    print(json.dumps(value,indent=2,allow_nan=False));return rc


if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError) as error:
        print("FAIL: "+str(error),file=sys.stderr);raise SystemExit(2)
