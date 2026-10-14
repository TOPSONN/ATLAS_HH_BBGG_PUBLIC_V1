#!/usr/bin/env python3
"""New ZH methods; historical validators remain unchanged.

Phase6F cannot issue physical ZH acceptance. Labelled synthetic fixtures may
exercise parser/graph/weight algebra and receive METHOD_ONLY. The physical
entry point fails closed until a separately authorized actual-execution phase.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation, localcontext
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[3]
CONFIG = REPO / "simulation/zh_pilot/config/input_profiles.json"
DECAYS = ("Z_to_b_bbar", "H_to_gamma_gamma")
PROFILES = ("ZH_STABLE", "ZH_ZBB_STABLE_H", "ZH_BBGG_FORCED_DECAYS")
MAX_BYTES, MAX_NODES = 32*1024**2, 100000
HASH = re.compile(r"[0-9a-f]{64}\Z")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def decimal(value):
    require(not isinstance(value, bool), "Boolean is not a number")
    try:
        result = Decimal(str(value).replace("D", "E").replace("d", "e"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("UNKNOWN/invalid number") from None
    require(result.is_finite(), "Nonfinite number")
    return result


def integer(value):
    require(not isinstance(value, bool) and re.fullmatch(r"[+-]?\d+", str(value)), "Invalid integer")
    return int(value)


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    path = Path(path)
    require(path.stat().st_size <= MAX_BYTES, "Oversized JSON")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def validate_profile_config(config):
    require(type(config["schema_version"]) is int and config["schema_version"] == 1 and tuple(config["profiles"]) == PROFILES, "Unknown/missing profile definition")
    require(config["physical_execution_authorized"] is False and config["physical_success_enabled_in_this_phase"] is False,
            "Phase6F physical production/acceptance is not authorized")
    require(config["required_physical_decay_ids"] == list(DECAYS) and config["target_independent_source_events"] == 100,
            "Decay IDs/original source target changed")
    require(config["profiles"]["ZH_STABLE"]["source_included_decay_ids"] == [] and
            config["profiles"]["ZH_ZBB_STABLE_H"]["source_included_decay_ids"] == [DECAYS[0]], "BR source inclusion changed")
    for name,final,resonances,missing in (("ZH_STABLE",[23,25],[],list(DECAYS)),("ZH_ZBB_STABLE_H",[5,-5,25],[23],[DECAYS[1]])):
        profile=config["profiles"][name]
        require(profile["source_lhe_profile"]==name and profile["stable_lhe_pdgs"]==final and
                profile["retained_lhe_resonances"]==resonances and profile["future_missing_decay_ids"]==missing,
                "Contradictory source topology/BR profile")
    forced=config["profiles"]["ZH_BBGG_FORCED_DECAYS"]
    require(forced["required_higgs_photon_birth_pdgs"]==[22,22] and forced["required_z_bottom_birth_pdgs"]==[5,-5] and
            forced["source_lhe_profile"]=="EXPLICIT_ZH_STABLE_OR_ZH_ZBB_STABLE_H_REQUIRED", "Continuum assumptions or missing original profile")
    require(config["nominal_weight_names"] == ["input_contribution_pb", "LHE_XWGTUP_pb", "Pythia_Info_weight_pb", "converter_weight_0_pb"],
            "Original weight columns changed")
    require(config["units"]["pb_per_mb"] == "1000000000" and config["synthetic_success_label"] == "METHOD_ONLY" and
            config["synthetic_success_is_physical_acceptance"] is False, "Unit/synthetic scope changed")
    require(config["future_native_detector"]["canonical_card_sha256"] ==
            "cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47", "Historical native detector card changed")
    require(config["lhe_numeric_tolerances"]=={"closure_atol_gev":1e-6,"closure_rtol":5e-9,"mass_shell_atol_gev2":1e-6,"mass_shell_rtol":5e-9},"LHE tolerance metadata changed")
    require(config["new_physics_events_generated"]==0 and type(config["new_physics_events_generated"]) is int and
            config["future_native_detector"]["card_path"]=="simulation/delphes/cards/atlas_like_bbgg_baseline.tcl" and
            config["future_native_detector"]["mgg_window_gev"]==[105,160] and config["future_native_detector"]["mbb_cut"]=="NONE_ADOPTED",
            "Physical/native detector scope or historical selection changed")
    return {"status": "METHOD_PROFILE_DEFINITIONS_PREPARED", "physical_validation": "NOT_EXECUTED", "profiles": list(PROFILES)}


def validate_card_contract(contract, *, root=REPO):
    """Frozen proposed cards, independent parameter consistency, no integration."""
    checker = module("phase6f_generator_parser", REPO / "simulation/zh_pilot/scripts/check_generator.py")
    checker.validate_bundle(contract, repo=root)
    cards = {row["id"]: Path(root)/row["path"] for row in contract["cards"]}
    param = checker.parse_param(cards["param"].read_text(encoding="utf-8"))
    p = contract["physics"]
    expected = {("mass",23):p["masses_gev"]["Z"], ("mass",25):p["masses_gev"]["H"],
                ("mass",5):p["masses_gev"]["b"], ("mass",4):p["masses_gev"]["c"],
                ("decay",23):p["widths_gev"]["Z"], ("decay",25):p["widths_gev"]["H"],
                ("sminputs",1):p["electroweak_inputs"]["aEWM1"], ("sminputs",2):p["electroweak_inputs"]["Gf"]}
    require(all(param[key] == decimal(value) for key,value in expected.items()), "Parameter mass/width/EW convention differs")
    scale = decimal(p["masses_gev"]["Z"]) + decimal(p["masses_gev"]["H"])
    require(p["scales"]["prescription"] == "FIXED_MZ_PLUS_MH" and
            all(decimal(p["scales"][k]) == scale for k in ("muR_gev","muF1_gev","muF2_gev")), "Wrong ZH scale")
    return {"status":"CARD_CONTRACT_CHECKED_READINESS_ONLY", "physical_validation":"NOT_EXECUTED",
            "cards_checked":len(cards), "profile_ids":["ZH_STABLE","ZH_ZBB_STABLE_H"], "new_events_generated":0}


def method_gate(method_only, fixture=None):
    require(type(method_only) is bool, "Literal method_only Boolean required")
    require(method_only, "PHYSICAL_PROFILE_NOT_AUTHORIZED: complete actual generation/decay/weight/native receipts are absent; GateL remainsNOT_AUTHORIZED")
    if fixture is not None:
        require(fixture.get("fixture_scope") == "METHOD_ONLY", "Synthetic method fixture must be explicitly labelled METHOD_ONLY")


def result(**fields):
    return {"status":"METHOD_ONLY", "physical_validation":"NOT_EXECUTED", "physical_acceptance":False,
            "new_physics_events_generated":0, **fields}


class BoundedReader:
    def __init__(self, stream):
        self.stream, self.total, self.tail = stream, 0, b""
        self.digest = hashlib.sha256()
    def read(self, size=-1):
        data = self.stream.read(65536 if size<0 else min(size,65536))
        self.total += len(data)
        require(self.total <= MAX_BYTES, "LHE decompression limit exceeded")
        scan = (self.tail+data).upper()
        require(b"<!DOCTYPE" not in scan and b"<!ENTITY" not in scan, "DTD/entity forbidden")
        self.tail = data[-16:]; self.digest.update(data)
        return data


def records(text):
    return [line.split("#",1)[0].split() for line in text.splitlines() if line.split("#",1)[0].strip()]


def close(a,b,atol=1e-6,rtol=5e-9):
    return abs(float(a)-float(b)) <= atol+rtol*max(abs(float(a)),abs(float(b)),1)


def event_particles(event, profile, physics):
    rows = records(event.text or "")
    require(rows and len(rows[0])==6, "Malformed LHE event header")
    nup, process = [integer(x) for x in rows[0][:2]]
    weight, scale, aqed, aqcd = [decimal(x) for x in rows[0][2:]]
    require(nup == (4 if profile=="ZH_STABLE" else 6) and len(rows)==nup+1 and scale>0 and aqed>0 and aqcd>=0,
            "Event particle count/scale/couplings invalid")
    require(close(scale,physics["scales"]["muR_gev"]), "Event scale differs from frozen ZH prescription")
    particles, colors = [], Counter()
    for index,row in enumerate(rows[1:],1):
        require(len(row)==13, "Malformed LHE particle")
        pdg,status,m1,m2,c1,c2 = [integer(x) for x in row[:6]]
        v=[float(decimal(x)) for x in row[6:]]
        px,py,pz,energy,mass,lifetime,spin=v
        require(status in (-1,1,2) and energy>0 and mass>=0 and lifetime>=0 and (abs(spin)<=1 or spin==9), "Invalid particle metadata")
        require((m1,m2)==(0,0) if status==-1 else 0<m1<=m2<index, "Invalid/cyclic LHE mother range")
        require(c1>=0 and c2>=0, "Negative color index")
        if abs(pdg) in range(1,6):
            require((c1>0 and c2==0) if pdg>0 else (c1==0 and c2>0), "Quark color/sign mismatch")
            require(mass==0, "Restricted five-flavour mass must be zero")
        else:
            require(pdg in (23,25) and c1==c2==0, "Unexpected/colored resonance")
        p2=math.fsum((px*px,py*py,pz*pz))
        require(abs(energy*energy-p2-mass*mass)<=1e-6+5e-9*max(energy*energy,p2,mass*mass,1), "Particle mass-shell failure")
        direction=-1 if status==-1 else 1 if status==1 else 0
        if c1: colors[c1]+=direction
        if c2: colors[c2]-=direction
        particles.append({"id":index,"pdg_id":pdg,"status":status,"mothers":list(range(m1,m2+1)) if m1 else [],"p4_gev":v[:4],"mass_gev":mass})
    incoming=[p for p in particles if p["status"]==-1]; final=[p for p in particles if p["status"]==1]
    require(len(incoming)==2 and [p["id"] for p in incoming]==[1,2] and
            1<=abs(incoming[0]["pdg_id"])<=5 and incoming[0]["pdg_id"] == -incoming[1]["pdg_id"], "Not the reviewed qqbar tree component")
    require(all(p["p4_gev"][0]==p["p4_gev"][1]==0 and p["p4_gev"][3]<=6500+1e-6 for p in incoming) and
            incoming[0]["p4_gev"][2]>0>incoming[1]["p4_gev"][2], "Invalid collinear parton beams")
    require(Counter(p["pdg_id"] for p in final)==Counter([23,25] if profile=="ZH_STABLE" else [5,-5,25]), "Wrong stable production final state")
    require(all(c==0 for c in colors.values()), "Color-flow conservation failed")
    residual=max(abs(math.fsum(p["p4_gev"][k] for p in incoming)-math.fsum(p["p4_gev"][k] for p in final)) for k in range(4))
    require(residual<=1e-6+5e-9*sum(p["p4_gev"][3] for p in incoming), "Global LHE momentum closure failure; intermediate Z must not be double counted")
    higgs=[p for p in particles if p["pdg_id"]==25]
    require(len(higgs)==1 and higgs[0]["status"]==1 and higgs[0]["mothers"]==[1,2] and close(higgs[0]["mass_gev"],physics["masses_gev"]["H"]), "Wrong H source mass/ancestry")
    z=[p for p in particles if p["pdg_id"]==23]
    require(len(z)==1 and z[0]["mothers"]==[1,2], "Missing/ambiguous hard Z")
    if profile=="ZH_STABLE":
        require(z[0]["status"]==1 and close(z[0]["mass_gev"],physics["masses_gev"]["Z"]), "Wrong stable Z mass/status")
    else:
        mz=float(decimal(physics["masses_gev"]["Z"])); width=float(decimal(physics["widths_gev"]["Z"]))
        require(z[0]["status"]==2 and abs(z[0]["mass_gev"]-mz)<=float(physics["generation_cuts"]["bwcutoff"])*width+1e-6, "Z resonance mass/window invalid")
        children=[p for p in particles if p["mothers"]==[z[0]["id"]]]
        require(Counter(p["pdg_id"] for p in children)==Counter([5,-5]) and
                all(close(math.fsum(p["p4_gev"][k] for p in children),z[0]["p4_gev"][k]) for k in range(4)), "b/bbar do not reconstruct the retained mother Z")
    return {"process_id":process,"weight":weight,"particles":particles,"closure_residual_gev":residual}


def validate_lhe(path, profile, expected_events, card_contract, *, method_only=False, receipt=None):
    method_gate(method_only)
    validate_card_contract(card_contract)
    require(profile in PROFILES[:2], "Forced-decay acceptance cannot be inferred from a stable-H LHE source alone")
    require(type(expected_events) is int and 0<expected_events<=100, "Bounded method fixture/event-count required")
    path=Path(path); before=file_sha(path)
    require(path.stat().st_size<=MAX_BYTES, "Oversized source LHE")
    physics=card_contract["physics"]
    opener=gzip.open if path.suffix==".gz" else open
    count,weights,processes,cards,max_residual=0,[],{},None,0.
    checker=module("phase6f_card_reader",REPO/"simulation/zh_pilot/scripts/check_generator.py")
    with opener(path,"rb") as stream:
        reader=BoundedReader(stream)
        try:
            for _,element in ET.iterparse(reader,events=("end",)):
                if element.tag=="header":
                    require(cards is None and element.findtext("MGVersion","").strip()=="3.5.16", "Missing/duplicate MG header/version")
                    require(len(element.findall("MGVersion"))==len(element.findall("ZHFixtureScope"))==1,"Duplicate version/fixture declaration")
                    require(element.findtext("ZHFixtureScope","")=="METHOD_ONLY", "Current synthetic LHE fixture must declare METHOD_ONLY; no real ZH physical acceptance is enabled")
                    tags={"process":"MG5ProcCard","run":"MGRunCard","param":"slha"}
                    require(all(len(element.findall(tag))==1 for tag in tags.values()), "Missing/duplicate generator card")
                    cards={name:element.findtext(tag) for name,tag in tags.items()}
                    commands=[line.split("#",1)[0].strip() for line in cards["process"].splitlines() if line.split("#",1)[0].strip()]
                    expected=[checker.MODEL,checker.PROTON,checker.PROCESSES[profile]]
                    require(commands==expected,"Process/model/coupling card differs")
                    rv=checker.parse_run(cards["run"])
                    for key,value in physics["run_values"].items():
                        if key not in ("nevents","iseed"):
                            require(rv.get(key)==value,"LHE run-card value differs: "+key)
                    require(rv["nevents"]==expected_events and type(rv["iseed"]) is int and 1<=rv["iseed"]<=900000000,"Source request count/seed differs")
                    pc=checker.parse_param(cards["param"])
                    template=next(row for row in card_contract["cards"] if row["id"]=="param")
                    require(pc==checker.parse_param((REPO/template["path"]).read_text(encoding="utf-8")),"Actual full SLHA differs from reviewed restricted-model card")
                    for key,value in {("mass",23):physics["masses_gev"]["Z"],("mass",25):physics["masses_gev"]["H"],("decay",23):physics["widths_gev"]["Z"],("decay",25):physics["widths_gev"]["H"],("sminputs",1):physics["electroweak_inputs"]["aEWM1"],("sminputs",2):physics["electroweak_inputs"]["Gf"]}.items():
                        require(pc[key]==decimal(value),"Actual LHE mass/width/EW input differs")
                elif element.tag=="init":
                    require(not processes and cards is not None,"Duplicate/out-of-order init")
                    rows=records(element.text or "")
                    require(rows and len(rows[0])==10,"Malformed init")
                    row=rows[0]
                    require([integer(x) for x in row[:2]]==[2212,2212] and [decimal(x) for x in row[2:4]]==[Decimal(6500)]*2 and
                            [integer(x) for x in row[6:8]]==[10042]*2 and integer(row[8])==-4,"Beam/PDF/weight strategy changed")
                    gen=element.find("generator")
                    require(gen is not None and len(element.findall("generator"))==1 and gen.get("name")=="MadGraph5_aMC@NLO" and gen.get("version")=="3.5.16","Init generator identity missing/wrong")
                    require(len(rows)==integer(row[9])+1,"Init subprocess count differs")
                    for row in rows[1:]:
                        require(len(row)==4,"Malformed subprocess")
                        sigma,error,xmax=[decimal(x) for x in row[:3]];pid=integer(row[3])
                        require(sigma>0 and error>=0 and xmax>0 and pid not in processes,"Invalid subprocess cross section")
                        processes[pid]=(sigma,error)
                elif element.tag=="event":
                    require(processes,"Event before header/init")
                    assessed=event_particles(element,profile,physics)
                    require(assessed["process_id"] in processes,"Unknown event process")
                    weights.append(assessed["weight"]);count+=1
                    require(count<=expected_events,"Extra event")
                    max_residual=max(max_residual,assessed["closure_residual_gev"])
                    for weight in element.findall(".//wgt"): decimal(weight.text or "")
                    element.clear()
            require(count==expected_events and count>0,"Missing/truncated/no events")
            require(element.tag=="LesHouchesEvents" and element.get("version")=="3.0","Wrong LHE root/version")
        except (ET.ParseError,EOFError,OSError) as error:
            raise ValueError("LHE/XML/gzip integrity failure: "+str(error)) from error
    require(file_sha(path)==before,"Source LHE changed during validation")
    with localcontext() as ctx:
        ctx.prec=60
        mean=sum(weights)/count;sigma=sum(p[0] for p in processes.values());error=sum(p[1] for p in processes.values())
        sampling=(sum((w-mean)**2 for w in weights)/(count*(count-1))).sqrt() if count>1 else Decimal(0)
        require(abs(mean-sigma)<=error+3*sampling+Decimal("1e-7")*max(abs(sigma),Decimal(1)),"Mean nominal weights/init cross section inconsistent")
    return result(profile=profile,events=count,source_file_sha256=before,decompressed_file_sha256=reader.digest.hexdigest(),
                  source_cross_section_pb=str(sigma),source_cross_section_uncertainty_pb=str(error),nominal_weight_mean_pb=str(mean),
                  negative_weights=sum(w<0 for w in weights),zero_weights=sum(w==0 for w in weights),maximum_closure_residual_gev=max_residual,
                  generator_cards_sha256={k:hashlib.sha256(v.encode()).hexdigest() for k,v in cards.items()},
                  scope="Bounded labelled synthetic LHE parser/profile method; no physical generation provenance or forced-H decay acceptance")


def graph_map(particles):
    require(isinstance(particles,list) and 0<len(particles)<=MAX_NODES,"Missing/oversized graph")
    graph={}
    for p in particles:
        pid=integer(p["id"])
        require(pid>0 and pid not in graph and integer(p["pdg_id"])!=0,"Duplicate/invalid particle ID")
        require(type(p["status"]) is int and isinstance(p["mothers"],list) and isinstance(p["daughters"],list),"Invalid graph status/links")
        require(len(p["p4_gev"])==4 and all(math.isfinite(float(decimal(v))) for v in p["p4_gev"]) and decimal(p["p4_gev"][3])>=0 and decimal(p["mass_gev"])>=0,"Invalid graph p4/mass")
        require(all(type(i) is int and i>0 for i in p["mothers"]+p["daughters"]) and
                len(set(p["mothers"]))==len(p["mothers"]) and len(set(p["daughters"]))==len(p["daughters"]),"Duplicate/invalid graph edge")
        graph[pid]=p
    colors={}
    def visit(pid):
        require(colors.get(pid)!=1,"Graph cycle")
        if colors.get(pid)==2:return
        colors[pid]=1
        for parent in graph[pid]["mothers"]:
            require(parent in graph and pid in graph[parent]["daughters"],"Missing/nonreciprocal mother edge")
            visit(parent)
        for daughter in graph[pid]["daughters"]:
            require(daughter in graph and pid in graph[daughter]["mothers"],"Missing/nonreciprocal daughter edge")
        colors[pid]=2
    for pid in graph:visit(pid)
    return graph


def ancestors(graph,pid):
    require(pid in graph,"Missing particle identity")
    seen=set();pending=list(graph[pid]["mothers"])
    while pending:
        p=pending.pop()
        if p not in seen:seen.add(p);pending.extend(graph[p]["mothers"])
    return seen


def decay_ancestry(record):
    graph=graph_map(record["particles"])
    ids=record["resonance_ids"]
    h,z=integer(ids["H"]),integer(ids["Z"])
    require(h!=z and h in graph and z in graph and graph[h]["pdg_id"]==25 and graph[z]["pdg_id"]==23,"Wrong original resonance identity")
    require(not any(graph[i]["pdg_id"]==25 for i in ancestors(graph,h)) and
            not any(graph[i]["pdg_id"]==23 for i in ancestors(graph,z)),"Resonance anchor is a copy rather than the unique source lineage")
    for pdg,anchor in ((25,h),(23,z)):
        roots=[i for i,p in graph.items() if p["pdg_id"]==pdg and not any(graph[a]["pdg_id"]==pdg for a in ancestors(graph,i))]
        require(roots==[anchor],"Multiple/missing original resonance lineages")
    def births(key,pdgs,resonance,other):
        selected=record[key]
        require(isinstance(selected,list) and len(selected)==2 and len(set(selected))==2 and
                Counter(graph[i]["pdg_id"] for i in selected)==Counter(pdgs),"Wrong/missing/ambiguous decay birth IDs")
        for pid in selected:
            parent=graph[pid]["mothers"]
            require(len(parent)==1 and graph[parent[0]]["pdg_id"]==graph[resonance]["pdg_id"],"Selected birth is not direct resonance decay")
            a=ancestors(graph,pid)
            roots=[i for i in a if graph[i]["pdg_id"]==graph[resonance]["pdg_id"] and
                   not any(graph[j]["pdg_id"]==graph[i]["pdg_id"] for j in ancestors(graph,i))]
            require(roots==[resonance] and other not in a,"Multiple/wrong/mixed H/Z ancestry")
        require(graph[selected[0]]["mothers"]==graph[selected[1]]["mothers"],"Decay products do not share one resonance copy")
        decay_parent=graph[selected[0]]["mothers"][0]
        require(Counter(graph[i]["pdg_id"] for i in graph[decay_parent]["daughters"])==Counter(pdgs),"Actual declared decay is not the forced two-body channel")
    births("higgs_photon_birth_ids",[22,22],h,z)
    births("z_bottom_birth_ids",[5,-5],z,h)
    final_ids=record.get("higgs_final_photon_ids",[])
    require(isinstance(final_ids,list) and len(final_ids)==len(set(final_ids)),"Duplicate/malformed selected final photon IDs")
    declared_births=set(record["higgs_photon_birth_ids"]);final_births={}
    for pid in final_ids:
        require(pid in graph and graph[pid]["pdg_id"]==22 and graph[pid]["status"]==1 and h in ancestors(graph,pid) and z not in ancestors(graph,pid),"Wrong selected stable H-photon ancestry")
        pending=[pid]; seen=set();matched_births=set()
        while pending:
            current=pending.pop()
            if current in seen:continue
            seen.add(current)
            if current in declared_births:
                matched_births.add(current);continue
            require(graph[current]["mothers"],"Final photon copy chain does not reach a declared H-decay birth")
            for parent in graph[current]["mothers"]:
                require(graph[parent]["pdg_id"]==22,"Final photon is not a copy of a declared H-decay birth")
                pending.append(parent)
        require(len(matched_births)==1,"Missing/ambiguous declared H-photon birth lineage")
        birth=next(iter(matched_births))
        require(birth not in final_births.values(),"Multiple selected stable photons claim the same declared H-decay birth")
        final_births[pid]=birth
    return {"higgs_photon_birth_ids":record["higgs_photon_birth_ids"],"z_bottom_birth_ids":record["z_bottom_birth_ids"],"nodes":len(graph),
            "selected_final_photon_birth_ids":final_births,
            "scope":"Exact declared graph IDs, no Pythia/HepMC/ROOT barcode equivalence; photon conversion/loss does not alter originalN"}


def br_factor_and_variance(values,standard_deviations,covariance):
    """Two-factor first-order propagation only; synthetic algebra is not BR physics."""
    a,b=[decimal(x) for x in values];sa,sb=[decimal(x) for x in standard_deviations];c=decimal(covariance)
    require(0<=a<=1 and 0<=b<=1 and sa>=0 and sb>=0 and abs(c)<=sa*sb,"BR/covariance violates probability or Cauchy/PSD bounds")
    with localcontext() as ctx:
        ctx.prec=60
        variance=b*b*sa*sa+a*a*sb*sb+2*a*b*c
        require(variance>=0,"Negative propagated variance")
        return {"factor":str(a*b),"first_order_variance":str(variance),"scope":"METHOD_ONLY_DELTA_METHOD; no unsupported zero-covariance assumption"}


def validate_weights(record,source_profile):
    require(source_profile in PROFILES[:2],"Missing explicit original LHE profile")
    n=integer(record["source_total_events"]);require(n>0,"Invalid original denominator")
    require(record["cross_section_unit"]=="PB" and record["pythia_sigmaGen_unit"]=="MB","PB/MB units missing/wrong")
    raw=decimal(record["LHE_XWGTUP_pb"]);info=decimal(record["Pythia_Info_weight_pb"]);converter=decimal(record["converter_weight_0_pb"])
    names=record["weight_names"];values=record["weight_values"]
    required=["input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb","converter_weight_0_pb"]
    require(isinstance(names,list) and isinstance(values,list) and len(names)==len(values) and 4<=len(names)<=259 and
            names[:4]==required and names[4:]==["converter_weight_"+str(i)+"_pb" for i in range(1,len(names)-3)] and
            len(set(names))==len(names),"Actual named weight vector/column binding differs")
    require(all(close(decimal(value),decimal(record[name]),1e-15,1e-12) for name,value in zip(names,values)),"Named weight value differs from preserved column")
    require(close(info,converter,1e-15,1e-12),"Actual Info/converter weight mismatch")
    require(close(decimal(record["input_contribution_pb"]),raw/n,1e-15,1e-12),"Original source denominator changed")
    ledger=record["br_ledger"]
    included=[] if source_profile=="ZH_STABLE" else [DECAYS[0]]
    source,embedded,external=[ledger[key] for key in ("source_included_decay_ids","nominal_decay_ids_in_pythia_weight","missing_external_decay_ids")]
    require(source==included and all(isinstance(ids,list) and len(ids)==len(set(ids)) and set(ids)<=set(DECAYS) for ids in (source,embedded,external)),"Unknown/duplicate/source-included decay ID")
    require(not(set(source)&set(embedded) or set(source)&set(external) or set(embedded)&set(external)) and
            set(source+embedded+external)==set(DECAYS),"BR factors missing or counted twice")
    require(set(ledger["branching_ratios"])==set(DECAYS),"Missing physical/model BR values")
    br={k:decimal(v) for k,v in ledger["branching_ratios"].items()};require(all(0<=v<=1 for v in br.values()),"Invalid BR")
    embedded_factor=math.prod(br[k] for k in embedded);external_factor=math.prod(br[k] for k in external)
    require(close(info,raw*embedded_factor,1e-15,1e-12),"Observed nominal weight transfer is inconsistent with explicit BR ledger")
    require(close(decimal(record["physical_BR_factor"]),external_factor,1e-15,1e-12) and
            close(decimal(record["exclusive_contribution_pb"]),info/n*external_factor,1e-15,1e-12),"Repeated BR or wrong exclusive contribution")
    sigma=decimal(record["source_cross_section_pb"]);mb=decimal(record["pythia_sigmaGen_mb"])
    require(sigma>0 and mb>=0 and close(mb*Decimal(1000000000),decimal(record["pythia_sigmaGen_pb"]),1e-15,1e-12),"Cross-section PB/MB conversion mismatch")
    return {"source_total_events":n,"raw_nominal_pb":str(raw),"external_BR_factor":str(external_factor),
            "exclusive_contribution_pb":str(info/n*external_factor),"source_Z_BR_reapplied":False,
            "scope":"Preserved actual-named-column algebra, observed transfer must receive separate actual physical closure later; sigmaGen is not assumed equal to source sigma"}


def validate_future_record(record,profile,contract,*,method_only=False):
    method_gate(method_only,record)
    validate_card_contract(contract)
    require(profile=="ZH_BBGG_FORCED_DECAYS" and record["units"]=={"momentum":"GEV","length":"MM"},"Wrong forced record profile/units")
    require(HASH.fullmatch(record["source_file_sha256"]) and HASH.fullmatch(record["source_event_sha256"]) and
            1<=integer(record["source_event_index"])<=integer(record["source_total_events"]),"Missing source identity/denominator")
    weight=validate_weights(record,record["source_lhe_profile"])
    graph=decay_ancestry(record)
    p=contract["physics"];parameters=record["source_model_parameters"]
    require(set(parameters)=={"MZ_gev","MH_gev","WZ_gev","WH_gev"} and
            all(decimal(parameters[k])==decimal(v) for k,v in (("MZ_gev",p["masses_gev"]["Z"]),("MH_gev",p["masses_gev"]["H"]),
                ("WZ_gev",p["widths_gev"]["Z"]),("WH_gev",p["widths_gev"]["H"]))),"Missing/wrong source resonance mass/width convention")
    nodes={n["id"]:n for n in record["particles"]}
    for species in ("Z","H"):
        resonance=nodes[record["resonance_ids"][species]]
        mass=float(decimal(resonance["mass_gev"]));target=float(decimal(p["masses_gev"][species]))
        require(close(mass,target) if species=="H" or record["source_lhe_profile"]=="ZH_STABLE" else
                abs(mass-target)<=float(p["generation_cuts"]["bwcutoff"])*float(p["widths_gev"]["Z"])+1e-6,"Wrong source resonance mass/window")
    return result(profile=profile,weight_check=weight,ancestry=graph,scope="Synthetic bounded graph/weight method; full HepMC/native physics receipts NOT_EXECUTED")


def future_reco_masses(row,*,method_only=False):
    method_gate(method_only,row)
    frozen=module("phase6f_frozen_native_mass",REPO/"simulation/rare_backgrounds/scripts/conditional_tags.py")
    jets=[j for j in frozen.sorted_objects(row["jets"]) if frozen.jet_eligible(j)]
    photons=[p for p in frozen.sorted_objects(row["photons"]) if frozen.photon_eligible(p)]
    require(all(type(j["btag"]) is int and j["btag"] in (0,1) for j in jets),"Invalid native bit0")
    for j in jets:frozen.flavor_category(j["flavor"])
    tagged=[j for j in jets if j["btag"]&1]
    gs=[frozen.p4(p,True) for p in photons[:2]];bs=[frozen.p4(j) for j in tagged[:2]]
    return result(m_gamma_gamma=frozen.combined_mass(gs) if len(gs)==2 else None,
                  m_bb=frozen.combined_mass(bs) if len(bs)==2 else None,
                  m_bb_gamma_gamma=frozen.combined_mass(gs+bs) if len(gs)==len(bs)==2 else None,
                  eligible_native_jets=len(jets),observed_native_bit0_tags=len(tagged),
                  photon_preselection=len(photons)>=2 and float(photons[0]["pt"])>35,
                  scope="Prepared native-persisted-object mass method, no new ROOT/native detector execution; separate H-decay truth association required")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile",choices=PROFILES,required=True)
    p.add_argument("--lhe",type=Path);p.add_argument("--record",type=Path)
    p.add_argument("--events",type=int,default=100)
    p.add_argument("--card-contract",type=Path,default=REPO/"simulation/zh_pilot/config/generator_contract.json")
    p.add_argument("--method-only",action="store_true",help="Explicit synthetic METHOD_ONLY scope; never physical acceptance")
    args=p.parse_args();validate_profile_config(load_json(CONFIG));method_gate(args.method_only)
    require(bool(args.lhe)^bool(args.record),"Choose exactly one labelled synthetic LHE or record fixture")
    contract=load_json(args.card_contract);validate_card_contract(contract)
    checked=validate_lhe(args.lhe,args.profile,args.events,contract,method_only=True) if args.lhe else validate_future_record(load_json(args.record),args.profile,contract,method_only=True)
    print(json.dumps(checked,indent=2,allow_nan=False))


if __name__=="__main__":
    try:main()
    except (OSError,ValueError,KeyError,TypeError,OverflowError,RecursionError) as error:
        print("FAIL: "+str(error),file=sys.stderr);raise SystemExit(1)
