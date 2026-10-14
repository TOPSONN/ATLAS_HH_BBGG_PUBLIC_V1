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

REPO = Path(__file__).resolve().parents[3]
PROFILE = "ZH_ZBB_STABLE_H"
MAX_BYTES = 32 * 1024**2
SHA = re.compile(r"[0-9a-f]{64}\Z")
EVENT = re.compile(rb"<event>.*?</event>", re.S)
HEADER = re.compile(rb"<header>.*?</header>", re.S)
SOURCE_IDENTITY = {"mg5_version":"3.5.16", "source_commit":"3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7",
                   "source_url":"https://github.com/mg5amcnlo/mg5amcnlo.git", "source_tag":"v3.5.16"}
TAGS = {"process_card":"MG5ProcCard", "run_card":"MGRunCard", "param_card":"slha"}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


FROZEN = load_module("phase6g_frozen_profiles", REPO/"simulation/zh_pilot/scripts/validate_profiles.py")
CARDS = load_module("phase6g_frozen_cards", REPO/"simulation/zh_pilot/scripts/check_generator.py")
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
            require(len(raw) <= MAX_BYTES, "Decompressed LHE exceeds bounded 100-event policy")
            require(stream.read(1) == b"", "Extra data beyond decompression limit")
    except (OSError, EOFError) as error:
        raise ValueError("Gzip CRC/truncation/integrity failure: "+str(error)) from error
    require(file_sha(path) == before, "Input changed during complete read")
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "DTD/entities forbidden")
    return raw, before


def prepared_contract(seed=20261104):
    """Read frozen text and prepare only the reviewed seed field; never execute."""
    require(type(seed) is int and 1 <= seed <= 900000000, "Invalid seed")
    frozen = CARDS.validate_bundle()
    paths = {r["id"]:REPO/r["path"] for r in frozen["cards"]}
    run = paths["run"].read_text(encoding="utf-8")
    run, n = re.subn(r"^([^\n=]+)(=\s*iseed\b[^\n]*)$", lambda m:str(seed)+" "+m[2], run, flags=re.M)
    require(n == 1, "Missing/duplicate seed template")
    return {"profile":PROFILE, "process_card":paths["process_zbb"].read_text(encoding="utf-8"),
            "run_card":run, "param_card":paths["param"].read_text(encoding="utf-8")}


def commands(text):
    return [line.split("#",1)[0].strip() for line in text.splitlines() if line.split("#",1)[0].strip()]


def process_card(text, *, expanded=False):
    lines = commands(text)
    require([s for s in lines if s.startswith("import ")] == [CARDS.MODEL], "Actual source model differs")
    require([s for s in lines if s.startswith(("generate ","add process "))] == [CARDS.PROCESSES[PROFILE]],
            "Exact source process/coupling orders differ")
    if not expanded:
        require(lines == [CARDS.MODEL,CARDS.PROTON,CARDS.PROCESSES[PROFILE]], "Prepared process card changed")
        return
    aliases = [s.partition("=")[2].strip().split() for s in lines if re.match(r"define p\s*=",s)]
    require(aliases, "Missing actual proton definition")
    pdgs = {"g":21,"u":2,"c":4,"d":1,"s":3,"b":5,"u~":-2,"c~":-4,"d~":-1,"s~":-3,"b~":-5}
    last = [pdgs[x] if x in pdgs else integer(x) for x in aliases[-1]]
    require(sorted(last) == [-5,-4,-3,-2,-1,1,2,3,4,5,21], "Effective proton is not reviewed five-flavour scheme")
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
            require((key in fixed and value==fixed[key]) or
                    (key in ("fortran_compiler","cpp_compiler") and value and not any(c in value for c in ";\r\n")),
                    "Unknown/changed generator physics or worker setting: "+key)
        elif line.startswith("define "):
            require(line.split()[1] in ("p","j","l+","l-","vl","vl~"),"Unexpected process alias")
        elif line.startswith("output "):
            parts=line.split();require(len(parts)>=2 and all(x in ("-f","-nojpeg") for x in parts[2:]),"Unexpected output command")
            outputs.append(line)
        else:
            require(line in (CARDS.MODEL,CARDS.PROCESSES[PROFILE]),"Unexpected source process command")
    require(len(outputs)<=1,"Multiple process exports in actual banner")


def check_cards(actual, prepared, seed):
    require(prepared["profile"]==PROFILE and all(isinstance(prepared[k],str) for k in TAGS),"Incomplete prepared cards")
    process_card(prepared["process_card"])
    process_card(actual["process_card"],expanded=True)
    target=prepared_contract(seed)
    rv=CARDS.parse_run(actual["run_card"]);expected=CARDS.parse_run(target["run_card"])
    require(CARDS.parse_run(prepared["run_card"])==expected,"Prepared run settings/cuts/count/seed changed")
    require(rv==expected,"Actual complete run card differs from reviewed request")
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
    require(integer(counts[0])==100 and decimal(sigmas[0])>0,"Banner count/cross section invalid")
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


def parse_run_log(text):
    """Actual MG5 summary is only %.4g display precision, not full init precision."""
    text=re.sub(r"\x1b\[[0-9;]*m","",text)
    markers=list(re.finditer(r"=== Results Summary for run:\s*zh100\s+tag:\s*\S+.*?===",text))
    require(len(markers)==1,"Missing/ambiguous final zh100 run summary")
    pairs=re.findall(r"Cross-section\s*:\s*([^\s]+)\s*\+-\s*([^\s]+)\s*pb\s*\n\s*Nb of events\s*:\s*(\d+)",text[markers[0].end():])
    require(len(pairs)==1,"Missing/ambiguous single final MG5 run summary")
    sigma,error,count=pairs[0]
    require(decimal(sigma)>0 and decimal(error)>=0 and integer(count)==100,"Actual run summary invalid")
    return {"cross_section_pb":sigma,"uncertainty_pb":error,"events":100,"precision":"MG5_4_SIGNIFICANT_DIGIT_DISPLAY_ONLY"}


def bound_artifact(item):
    require(isinstance(item,dict) and isinstance(item.get("path"),str) and isinstance(item.get("sha256"),str) and SHA.fullmatch(item["sha256"]),"Missing artifact binding")
    path=Path(item["path"])
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=MAX_BYTES and file_sha(path)==item["sha256"],"Artifact bytes changed/missing/unsafe")
    return path


def check_provenance(provenance,prepared,seed,header_raw,init,source_path):
    require(isinstance(provenance,dict) and type(provenance.get("schema_version")) is int and provenance["schema_version"]==1,
            "Physical source provenance required")
    request=provenance["request"]
    require(request["profile"]==PROFILE and request["process"]=="zh" and type(request["events"]) is int and request["events"]==100 and
            type(request["seed"]) is int and request["seed"]==seed and decimal(request["energy_gev"])==13000,"Source request differs")
    identity=provenance["source_identity"]
    require(all(identity.get(k)==v for k,v in SOURCE_IDENTITY.items() if k!="mg5_version") and
            identity.get("mg5_version",identity.get("version"))=="3.5.16" and
            ("version" not in identity or identity["version"]=="3.5.16"),"Unverified official source identity")
    auth=provenance["authorization_receipt"]
    require(isinstance(auth.get("id"),str) and auth["id"],"Missing authorization receipt identity")
    auth_path=bound_artifact(auth)
    ticket=FROZEN.load_json(auth_path)
    require(ticket["status"]=="EXPLICIT_USER_AUTHORIZATION" and ticket["authorization_command"]=="AUTHORIZE_PHASE6G_ZH_100_RUN" and
            ticket["ticket_id"]==auth["id"] and str(uuid.UUID(ticket["ticket_id"]))==ticket["ticket_id"] and
            ticket["reviewed_base_head"]=="05cff9a5d991ba6782b339bc41932ae4da296d8c","Missing/contradictory explicit authorization content")
    require(auth_path.name.endswith(".consumed-"+ticket["ticket_id"]),"Authorization was not claimed by one-use controller")
    start,end=[datetime.fromisoformat(ticket[k]) for k in ("authorized_at_utc","expires_at_utc")]
    require(start.tzinfo is not None and end.tzinfo is not None and timedelta(0)<end-start<=timedelta(hours=24),"Malformed/unbounded authorization dates")
    auth_request=ticket["request"]
    require(auth_request["process"]=="zh" and type(auth_request["events"]) is int and auth_request["events"]==100 and
            type(auth_request["seed"]) is int and auth_request["seed"]==seed and type(auth_request["energy_gev"]) is int and auth_request["energy_gev"]==13000,
            "Authorization/source request differs")
    require(Path(source_path).resolve().is_relative_to(Path(auth_request["output"]).resolve()),"Source outside authorized output")
    common=load_module("phase6g_readonly_authorization",REPO/"simulation/zh_pilot/phase6g/common.py")
    bridge_sha,_=common.bridge_identity()
    require(ticket["bridge_sha256"]==bridge_sha,"Authorization binds different reviewed execution/validation bridge")
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
    log=parse_run_log(paths["run_log"].read_text(encoding="utf-8"))
    for key,actual,token in (("cross_section_pb",init["sigma"],init["sigma_token"]),("uncertainty_pb",init["uncertainty"],init["error_token"])):
        require(decimal(log[key])!=0 or actual==0,"A zero %.4g log value cannot hide a nonzero init value")
        require(abs(decimal(log[key])-actual)<=half_print_unit(log[key],significant_digits=4)+half_print_unit(token),
                "Independent actual run log/init "+key+" differs beyond printed precision")
    generation=provenance["generation"]
    require(type(generation["events"]) is int and generation["events"]==100 and
            generation["precision"]==log["precision"] and all(decimal(generation[k])==decimal(log[k]) for k in ("cross_section_pb","uncertainty_pb")),
            "Stage result not backed by independently parsed actual run log")
    bindings={key:dict(artifacts[key]) for key in paths};bindings["authorization_receipt"]=dict(auth)
    return {"status":"BOUND_ACTUAL_EXECUTOR_PROVENANCE","source_identity":identity,"authorization_receipt_id":auth["id"],
            "authorization_receipt_sha256":file_sha(auth_path),"artifacts":bindings,"independent_run_log_summary":log,
            "authorization_scope":"Executor validates human authorization, expiry, request/output/bundle and one-use consumption; this read-only check verifies preserved binding, never grants authorization"}


def assess_event(element,index,raw,physics,init):
    require(not element.attrib,"Unexpected event attributes")
    value=FROZEN.event_particles(element,PROFILE,physics)
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
    anchors={name:next(p["id"] for p in value["particles"] if p["pdg_id"]==pdg) for name,pdg in (("Z",23),("H",25),("b",5),("bbar",-5))}
    return {"source_event_index":index,"source_event_content_hash":hashlib.sha256(raw).hexdigest(),
            "nominal_generator_weight":str(value["weight"]),"scale_gev":rows[0][3],"aqed":rows[0][4],"aqcd":rows[0][5],
            "rows":rows,"original_resonance_and_bottom_ids":anchors,"particles":value["particles"],
            "closure_residual_gev":value["closure_residual_gev"],"mass_shell_residual_gev2":shell}


def validate_file(path,expected_events=100,expected_seed=20261104,profile=PROFILE,card_contract=None,provenance=None,*,method_only=False):
    """Validate actual LHE records against exact future executor evidence.

    A physical result is PASS_LHE_RECORDS only, separate from missing H-decay
    normalization/native stages. Missing/contradictory evidence fails closed.
    ValidationError.report retains observed assessment counts and failures.
    """
    report={"schema_version":1,"status":"FAILED_PHYSICAL_VALIDATION","profile":profile,"physical_acceptance":False,
            "expected_events":expected_events,"source_total_events":None,"actual_events":None,"events_assessed":0,
            "events_valid":0,"events_invalid":0,"events_not_assessed":None,"event_failures":[],
            "normalization_scope":"RAW_ZBB_STABLE_H_SOURCE; Z decay already included, no H BR adopted",
            "physical_BR_adoption":"NONE_AUTHORIZED","exclusive_physical_normalization":"BLOCKED_BR_WEIGHT_CLOSURE"}
    try:
        require(type(method_only) is bool and profile==PROFILE and type(expected_events) is int and expected_events==100,
                "Only bounded reviewed ZH_ZBB_STABLE_H/100 profile supported")
        require(type(expected_seed) is int and 1<=expected_seed<=900000000,"Invalid expected seed")
        prepared=prepared_contract(expected_seed) if card_contract is None else card_contract
        require(method_only or card_contract is not None,"Physical validation requires exact executor prepared cards")
        raw,source_sha=bounded_bytes(path)
        report.update(source_file_sha256=source_sha,compressed_file_sha256=source_sha if Path(path).suffix==".gz" else None,
                      decompressed_file_sha256=hashlib.sha256(raw).hexdigest(),decompressed_bytes=len(raw))
        try:root=parse_xml(raw)
        except ET.ParseError as error:raise ValueError("Complete LHE XML/truncation failure: "+str(error)) from error
        require(root.tag=="LesHouchesEvents" and root.attrib=={"version":"3.0"},"Wrong LHE root/version/schema")
        require(len(root.findall("header"))==len(root.findall("init"))==1 and
                root[0].tag=="header" and root[1].tag=="init" and all(e.tag=="event" for e in root[2:]),"Duplicate/missing/out-of-order LHE sections")
        header=root[0];scope=header.findall("ZHFixtureScope")
        require((len(scope)==1 and scope[0].text=="METHOD_ONLY") if method_only else not scope,
                "Synthetic METHOD_ONLY fixture cannot receive physical acceptance; method declaration required")
        actual,banner_sigma,banner_token=header_data(header)
        rv=check_cards(actual,prepared,expected_seed)
        init=init_data(root[1]);header_raws=HEADER.findall(raw)
        require(len(header_raws)==1,"Missing/ambiguous raw complete banner")
        require(abs(banner_sigma-init["sigma"])<=half_print_unit(banner_token)+half_print_unit(init["sigma_token"]),
                "Banner/init integrated cross section differs beyond printed precision")
        report.update(cross_section_pb=str(init["sigma"]),cross_section_uncertainty_pb=str(init["uncertainty"]),
                      banner_cross_section_pb=str(banner_sigma),idwtup=-4,beam_energies_gev=[6500,6500],seed=rv["iseed"],
                      actual_cards=actual,card_hashes={k:hashlib.sha256(v.encode()).hexdigest() for k,v in actual.items()},
                      header_sha256=hashlib.sha256(header_raws[0]).hexdigest(),run_values=rv,
                      source_included_decay_ids=["Z_to_b_bbar"],missing_decay_ids=["H_to_gamma_gamma"])
        report["provenance"]={"status":"SYNTHETIC_METHOD_ONLY_NOT_GENERATOR_PROOF"} if method_only else check_provenance(provenance,prepared,expected_seed,header_raws[0],init,path)
        elements=list(root[2:]);raw_events=EVENT.findall(raw)
        require(len(elements)==len(raw_events),"Exact raw event boundaries/complete XML count differ")
        report.update(actual_events=len(elements),source_total_events=len(elements),events_not_assessed=len(elements))
        source_events=[];weights=[];physics=CARDS.validate_bundle()["physics"]
        for index,(element,event_raw) in enumerate(zip(elements,raw_events),1):
            report["events_assessed"]+=1;report["events_not_assessed"]-=1
            try:
                assessed=assess_event(element,index,event_raw,physics,init)
                source_events.append(assessed);weights.append(decimal(assessed["nominal_generator_weight"]));report["events_valid"]+=1
            except (ValueError,KeyError,TypeError,OverflowError) as error:
                report["events_invalid"]+=1;report["event_failures"].append({"source_event_index":index,"source_event_sha256":hashlib.sha256(event_raw).hexdigest(),"error":str(error)})
        report["source_events"]=source_events
        report["event_content_sha256"]=hashlib.sha256(b"".join(raw_events)).hexdigest()
        require(len(elements)==100,"Actual event count differs from original100; no replacement/removal permitted")
        require(report["events_invalid"]==0,"Invalid LHE event records: "+str(report["events_invalid"]))
        with localcontext() as ctx:
            ctx.prec=60;total=sum(weights,Decimal(0));mean=total/100
            variance=sum((w-mean)**2 for w in weights)/99;se=(variance/100).sqrt()
            printed=half_print_unit(init["sigma_token"])+sum(half_print_unit(e["rows"][0][2]) for e in source_events)/100
            require(abs(mean-init["sigma"])<=init["uncertainty"]+3*se+printed,"Signed nominal mean/init cross-section closure failed")
            report["weights"]={"sum_pb":str(total),"mean_pb":str(mean),"sum_abs_pb":str(sum(abs(w) for w in weights)),
                "sum_squared_pb2":str(sum(w*w for w in weights)),"source_event_sampling_se_pb":str(se),
                "negative_count":sum(w<0 for w in weights),"zero_count":sum(w==0 for w in weights),
                "full_original_source_denominator":100,"normalization":"Each preserved raw XWGTUP_pb divided once by original100",
                "closure_scope":"Printed precision plus reported integration error and three event-level sampling SE; not precision cross-section acceptance"}
        report.update(maximum_closure_residual_gev=max(e["closure_residual_gev"] for e in source_events),
                      maximum_mass_shell_residual_gev2=max(e["mass_shell_residual_gev2"] for e in source_events),
                      distinct_source_event_hashes=len({e["source_event_content_hash"] for e in source_events}),
                      independence_scope="Generator run/seed provenance; record-level hashes do not prove statistical independence")
        require(file_sha(path)==source_sha,"Source changed during validation")
        if not method_only:
            for binding in report["provenance"]["artifacts"].values():bound_artifact(binding)
        report.update(status="METHOD_ONLY" if method_only else "PASS_LHE_RECORDS",physical_acceptance=not method_only,
                      physical_pilot_acceptance="NOT_EVALUATED",validation_scope="Complete Zbb+stable-H source records, not shower/BR/native acceptance")
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
    require(type(method_only) is bool and type(expected_output_count) is int and expected_output_count in (10,100),"Wrong smoke/full scope")
    require(source["status"]==("METHOD_ONLY" if method_only else "PASS_LHE_RECORDS") and source["source_total_events"]==100,
            "Missing full original source validation")
    require(isinstance(records,list) and len(records)==expected_output_count,"Missing downstream original-source outputs")
    original={e["source_event_index"]:e for e in source["source_events"]};seen=set()
    names=["input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb","converter_weight_0_pb"]
    for row in records:
        require(row.get("fixture_scope")=="METHOD_ONLY" if method_only else "fixture_scope" not in row,"Synthetic/physical downstream scope mismatch")
        index=integer(row["source_event_index"]);require(index in original and index not in seen,"Missing/duplicate downstream source index")
        seen.add(index);event=original[index]
        require(row["source_file_sha256"]==source["source_file_sha256"] and row["source_event_sha256"]==event["source_event_content_hash"] and
                type(row["source_total_events"]) is int and row["source_total_events"]==100,"Source identity/denominator mismatch")
        weight_names=row["weight_names"];values=row["weight_values"]
        require(isinstance(weight_names,list) and isinstance(values,list) and weight_names[:4]==names and len(weight_names)==len(values) and 4<=len(weight_names)<=259 and
                weight_names[4:]==["converter_weight_"+str(i)+"_pb" for i in range(1,len(weight_names)-3)],"Actual named vector mismatch")
        weights=[decimal(v) for v in values];raw=decimal(event["nominal_generator_weight"])
        require(FROZEN.close(weights[0],raw/100,1e-15,1e-12) and FROZEN.close(weights[1],raw,1e-15,1e-12) and
                FROZEN.close(weights[2],weights[3],1e-15,1e-12),"Raw/Info/converter source-normalization mismatch")
    require(seen==set(range(1,expected_output_count+1)),"Output is not exact original prefix/full source set")
    return {"status":"METHOD_ONLY" if method_only else "PASS_SOURCE_BINDING_ONLY","source_total_events":100,
            "output_events":len(records),"independent_additional_hard_events":0,"exclusive_physical_normalization":"BLOCKED_BR_WEIGHT_CLOSURE",
            "actual_ReaderAscii_physics_validation":"SEPARATELY_REQUIRED_NOT_IMPLIED","physical_BR_adoption":"NONE_AUTHORIZED"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file",type=Path,required=True);parser.add_argument("--events",type=int,default=100)
    parser.add_argument("--seed",type=int,default=20261104);parser.add_argument("--cards",type=Path)
    parser.add_argument("--provenance",type=Path);parser.add_argument("--method-only",action="store_true")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    try:
        value=validate_file(args.file,args.events,args.seed,card_contract=FROZEN.load_json(args.cards) if args.cards else None,
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
