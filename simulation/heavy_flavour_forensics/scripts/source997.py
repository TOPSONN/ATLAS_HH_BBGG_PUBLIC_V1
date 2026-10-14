#!/usr/bin/env python3
"""Read-only, exact existing light-jjgg source997 forensics. No simulation."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict, deque
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
SOURCE_INDEX = 997
SOURCE_HASH = "322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8"
EVENT_HASH = "157928b854ffa4be208b4460338afea8d857446a595a56016c7e8cb994fec31f"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def selected_row(path, key="source_event_index", value=SOURCE_INDEX):
    with Path(path).open("rb") as stream:
        found = None
        for raw in stream:
            require(len(raw) <= 2*1024**2, "oversized original diagnostic row")
            row = json.loads(raw)
            if row.get(key) == value:
                require(found is None, "duplicate exact source identity")
                found = (row, hashlib.sha256(raw).hexdigest())
        require(found is not None, "source997 row missing")
        return found


def parse_hepmc(raw):
    """Parse real ASCII graph IDs/vertices; never use Pythia ordinal equality."""
    particles, vertices, attrs = {}, {}, {}
    lines = raw.decode("utf-8").splitlines()
    event_fields = lines[0].split()
    require(event_fields[0] == "E", "missing exact event header")
    for line in lines[1:]:
        fields = line.split()
        if fields[0] == "P":
            pid, parent, pdg = map(int, fields[1:4])
            require(pid not in particles, "duplicate HepMC particle")
            particles[pid] = {"id":pid, "pdg_id":pdg, "status":int(fields[9]),
                              "p4_gev":list(map(float,fields[4:8])), "mass_gev":float(fields[8]),
                              "serialized_parent":parent, "mothers":[], "daughters":[]}
        elif fields[0] == "V":
            match = re.fullmatch(r"V (-?\d+) ([+-]?\d+) \[([^]]*)\](?: @ (\S+) (\S+) (\S+) (\S+))?", line)
            require(match is not None, "unsupported exact vertex syntax")
            key = "explicit:"+match[1]
            require(key not in vertices, "duplicate HepMC vertex")
            vertices[key] = {"key":key,"status":int(match[2]),
                             "incoming":[int(v) for v in match[3].split(",")],"outgoing":[],
                             "serialized_position_mm":list(map(float,match.groups()[3:])) if match[4] is not None else None,
                             "position_scope":"original ASCII explicit position; absent position is not invented"}
        elif fields[0] == "A":
            owner, name, value = line.split(" ",3)[1:]
            if owner == "0":
                attrs[name] = value
    for pid, particle in particles.items():
        parent = particle["serialized_parent"]
        key = "explicit:"+str(parent) if parent < 0 else "implicit:"+str(parent) if parent > 0 else None
        particle["production_vertex"] = key
        particle["end_vertex"] = None
        if parent > 0:
            vertices.setdefault(key,{"key":key,"status":0,"incoming":[parent],"outgoing":[],
                                     "serialized_position_mm":None,"position_scope":"implicit vertex position not written; native Delphes reader initializes zero"})
        if key is not None:
            require(key in vertices, "dangling production vertex")
            vertices[key]["outgoing"].append(pid)
    for key, vertex in vertices.items():
        require(vertex["outgoing"], "empty/dangling vertex")
        for pid in vertex["incoming"]:
            require(pid in particles and particles[pid]["end_vertex"] is None, "missing/duplicate end vertex")
            particles[pid]["end_vertex"] = key
            particles[pid]["daughters"].extend(vertex["outgoing"])
        for pid in vertex["outgoing"]:
            particles[pid]["mothers"].extend(vertex["incoming"])
    require(len(particles)==int(event_fields[3]) and len(vertices)==int(event_fields[2]), "graph header count mismatch")
    return {"event_number":int(event_fields[1]),"particles":particles,"vertices":vertices,"attributes":attrs,
            "exact_event_sha256":hashlib.sha256(raw).hexdigest()}


def pythia_graph(particles):
    require(all(row.get("id",row["pythia_index"])==row["pythia_index"] for row in particles),"inconsistent Pythia index alias")
    graph = {row["pythia_index"]:dict(row,id=row["pythia_index"]) for row in particles}
    require(len(graph)==len(particles), "duplicate Pythia index")
    return graph


def ancestors(graph, particle_id):
    require(particle_id in graph, "unknown exact particle ID")
    colors, visited, pending = {}, set(), [(particle_id,False)]
    while pending:
        pid, exiting = pending.pop()
        if pid == 0:
            continue
        require(pid in graph, "dangling ancestry")
        if exiting:
            colors[pid]=2
            continue
        require(colors.get(pid)!=1,"cyclic ancestry")
        if colors.get(pid)==2:
            continue
        colors[pid]=1
        if pid!=particle_id: visited.add(pid)
        pending.append((pid,True))
        pending.extend((mother,False) for mother in reversed(graph[pid]["mothers"]))
    return sorted(visited)


def audit_graph(graph):
    missing, nonreciprocal, duplicates, edges = [], [], [], 0
    indegree, children = {}, defaultdict(list)
    for pid, row in graph.items():
        mothers = [m for m in row["mothers"] if m != 0]
        if len(mothers)!=len(set(mothers)) or len(row["daughters"])!=len(set(row["daughters"])):
            duplicates.append(pid)
        indegree[pid] = len(mothers)
        for mother in mothers:
            edges += 1
            if mother not in graph:
                missing.append([mother,pid])
            else:
                children[mother].append(pid)
                if pid not in graph[mother]["daughters"]:
                    nonreciprocal.append([mother,pid])
        for daughter in row["daughters"]:
            if daughter not in graph or pid not in graph[daughter]["mothers"]:
                nonreciprocal.append([pid,daughter])
    roots = sorted(pid for pid,n in indegree.items() if n==0)
    queue, count = deque(roots), 0
    while queue:
        pid = queue.popleft(); count += 1
        for daughter in children[pid]:
            indegree[daughter] -= 1
            if indegree[daughter] == 0:
                queue.append(daughter)
    return {"status":"PASS" if not missing and not nonreciprocal and not duplicates and count==len(graph) else "FAIL",
            "nodes":len(graph),"mother_edges":edges,"roots":roots,"kahn_visited":count,
            "missing_edges":missing,"nonreciprocal_edges":nonreciprocal,"duplicate_edge_particle_ids":duplicates}


def hepmc_status(row, graph):
    status = row["status"]
    if status > 0: return 1
    if status == -12: return 4
    if row["is_hadron"] or abs(row["pdg_id"]) in (13,15):
        daughters = row["daughters"]
        if daughters:
            first = graph[daughters[0]]
            if first["pdg_id"] != row["pdg_id"] and 90 < abs(first["status"]) < 95:
                return 2
    return -status if -200 <= status <= -11 else 0


def particle_key(row, status):
    return (row["pdg_id"], status, *(float(v).hex() for v in row["p4_gev"]),float(row["mass_gev"]).hex())


def match_pythia_hepmc(pygraph, hgraph):
    candidates = defaultdict(list)
    for hid,row in hgraph.items():
        candidates[particle_key(row,row["status"])].append(hid)
    pykeys=Counter(particle_key(row,hepmc_status(row,pygraph)) for row in pygraph.values())
    result = {}
    for pid,row in pygraph.items():
        key=particle_key(row,hepmc_status(row,pygraph))
        matches = candidates[key]
        result[pid] = {"status":"UNIQUE_TUPLE_MATCH" if len(matches)==1 and pykeys[key]==1 else "UNKNOWN_AMBIGUOUS" if matches else "UNKNOWN_NO_MATCH",
                       "pythia_tuple_multiplicity":pykeys[key],"hepmc_tuple_multiplicity":len(matches),
                       "hepmc_ids":matches,"definition":"exact PDG/converted-status/binary64 p4/generated-mass tuple; no ordinal assumption"}
    unique = {pid:row["hepmc_ids"][0] for pid,row in result.items() if row["status"]=="UNIQUE_TUPLE_MATCH"}
    differences = []
    for pid,hid in unique.items():
        parents = pygraph[pid]["mothers"]
        if all(m==0 or m in unique for m in parents):
            expected = sorted(unique[m] for m in parents if m!=0)
            if expected != sorted(hgraph[hid]["mothers"]):
                differences.append({"pythia_index":pid,"hepmc_id":hid,"expected_mothers":expected,"actual_mothers":hgraph[hid]["mothers"]})
    return {"particles":result,"unique_matches":len(unique),"ambiguous_or_missing":len(result)-len(unique),
            "unique_mapping_is_injective":len(set(unique.values()))==len(unique),"mother_edge_differences":differences}


def eta_phi(vector):
    x,y,z,_ = vector
    pt = math.hypot(x,y)
    return pt, math.asinh(z/pt) if pt else math.copysign(math.inf,z), math.atan2(y,x)


def delta_r(jet, particle):
    _,eta,phi = eta_phi(particle["p4_gev"])
    return math.hypot(float(jet["eta"])-eta, math.remainder(float(jet["phi"])-phi,2*math.pi))


def associated_label(candidates):
    priority = max((0 if abs(row["pdg_id"])==21 else abs(row["pdg_id"]) for row in candidates),default=-1)
    return 0 if priority < 0 else 21 if priority==0 else priority


def unique_diagnostic_matching(objects, jets, id_field="pythia_index", radius=.4):
    """Small source997-only global one-to-one geometric cross-check.

    Maximize cardinality then minimize total DeltaR. Exact equal optimums are
    explicitly UNKNOWN; this never replaces native any-cone association.
    """
    require(len(objects)<=4 and len(jets)<=8,"bounded source997 matching study exceeded")
    require(not isinstance(radius,bool) and math.isfinite(float(radius)) and float(radius)>0,"invalid diagnostic matching radius")
    ids=[row[id_field] for row in objects]
    require(len(ids)==len(set(ids)),"duplicate diagnostic object identity")
    jet_ids=[row["index"] for row in jets]
    require(all(isinstance(i,int) and not isinstance(i,bool) and i>=0 for i in jet_ids) and len(jet_ids)==len(set(jet_ids)),
            "invalid/duplicate native jet identity")
    edges={i:[(j,delta_r(jet,row)) for j,jet in enumerate(jets) if delta_r(jet,row)<radius]
           for i,row in enumerate(objects)}
    best, solutions=None, []
    def visit(index, used, pairs):
        nonlocal best, solutions
        if index==len(objects):
            score=(-len(pairs),math.fsum(distance for _,_,distance in pairs))
            if best is None or score<best: best,solutions=score,[list(pairs)]
            elif score==best: solutions.append(list(pairs))
            return
        visit(index+1,used,pairs)
        for j,distance in edges[index]:
            if j not in used: visit(index+1,used|{j},pairs+[(index,j,distance)])
    visit(0,set(),[])
    encoded=[[{"object_id":ids[i],"native_jet_index":jets[j]["index"],"delta_r":distance} for i,j,distance in solution]
             for solution in solutions]
    return {"status":"UNIQUE_OPTIMUM" if len(solutions)==1 else "UNKNOWN_AMBIGUOUS_OPTIMUM",
            "cardinality":-best[0],"total_delta_r":best[1],"pairs":encoded[0] if len(solutions)==1 else None,
            "possible_equal_optimums":encoded if len(solutions)>1 else [],
            "definition":f"maximum cardinality then minimum summed binary64 DeltaR; strictR{radius}; one object/jet once; diagnostic only; multiple physical hadrons per jet remain allowed"}


def native_flavour(jet, hgraph):
    candidates, boundary = [], []
    for hid,row in hgraph.items():
        pdg = abs(row["pdg_id"]); pt,eta,_ = eta_phi(row["p4_gev"])
        if pdg not in (1,2,3,4,5,21) or row["status"] in (1,-1) or pt<=1 or abs(eta)>2.5:
            continue
        distance = delta_r(jet,row)
        value = dict(row, delta_r=distance)
        if distance < .4-2e-6: candidates.append(value)
        elif distance <= .4+2e-6: boundary.append(value)
    labels = {associated_label(candidates)}
    for row in boundary:
        labels |= {associated_label(candidates+[row])}
    return {"definite_candidates":candidates,"angular_boundary_candidates":boundary,
            "attainable_labels":sorted(labels),"matches_native":jet["flavor"] in labels,
            "scope":"pinned native Delphes parton-array/status/acceptance/max-PDG rule; preserved Float_t-axis angular envelope2e-6; not a new working point"}


def native_root_snapshot(payload):
    import ROOT
    require(ROOT.gROOT.GetVersion()=="6.40.04" and ROOT.gSystem.Load(payload["library"])>=0,"wrong native ROOT/dictionaries")
    require(sha(payload["root_file"])==payload["root_sha256"],"ROOT bytes changed before event997 readback")
    file = ROOT.TFile.Open(payload["root_file"],"READ")
    require(file and not file.IsZombie() and not file.TestBit(ROOT.TFile.kRecovered),"invalid ROOT")
    tree = file.Get("Delphes")
    require(tree and tree.GetEntries()==1000 and tree.GetEntry(SOURCE_INDEX-1)>0,"missing exact full1000 ROOT entry996")
    require(tree.Event.GetEntriesFast()==1 and int(tree.Event.At(0).Number)==SOURCE_INDEX,"ROOT event identity mismatch")
    objects = {}
    for branch in ("Jet","Photon"):
        values=[]
        for index,obj in enumerate(getattr(tree,branch)):
            values.append({"index":index,"pt":float(obj.PT),"eta":float(obj.Eta),"phi":float(obj.Phi),
                           "mass":float(obj.Mass) if branch=="Jet" else 0.,
                           "flavor":int(obj.Flavor) if branch=="Jet" else 0,"btag":int(obj.BTag) if branch=="Jet" else 0})
        objects[branch.lower()+"s"] = sorted(values,key=lambda row:(-row["pt"],row["index"]))
    f32=lambda v:struct.unpack("f",struct.pack("f",v))[0]
    original=[]
    for row in payload["hepmc_particles"]:
        vertex=payload["hepmc_vertices"].get(row["production_vertex"],{})
        position=vertex.get("serialized_position_mm") or [0.,0.,0.,0.]
        original.append((row["pdg_id"],row["status"],*(f32(v) for v in row["p4_gev"]),f32(row["mass_gev"]),
                         *(f32(v) for v in position[:3]),f32(position[3]*1e-3/2.99792458e8)))
    original.sort()
    actual = sorted((int(p.PID),int(p.Status),float(p.Px),float(p.Py),float(p.Pz),float(p.E),float(p.Mass),
                     float(p.X),float(p.Y),float(p.Z),float(p.T)) for p in tree.Particle)
    require(actual==original,"native source997 Particle multiset differs from exact HepMC p4/PID/status/mass/XYZmm/Tseconds")
    result={"status":"PASS","root_version":ROOT.gROOT.GetVersion(),"tree_entries":1000,"entry_zero_based":996,
            "event_number_one_based":int(tree.Event.At(0).Number),"native_event_weight_float":float(tree.Event.At(0).Weight),
            "particle_count":len(actual),"particle_source_tuple_multiset":"PASS; Float_t p4/PID/status/mass/XYZmm/Tseconds; native unrecorded vertex positions zero by reader source, not physical Pythia-coordinate inference; no barcode/order equivalence",**objects}
    file.Close()
    require(sha(payload["root_file"])==payload["root_sha256"],"ROOT bytes changed during event997 readback")
    return result


def build(installation, delphes_run, output):
    code_paths=(Path(__file__).resolve(),REPO/"simulation/rare_backgrounds/scripts/conditional_tags.py",
                REPO/"simulation/delphes/scripts/run_delphes.py",REPO/"simulation/pythia8/scripts/validate_hepmc3.py",
                REPO/"simulation/pythia8/scripts/validate_lhe_stream.py")
    preflight_snapshots={path:sha(path) for path in (*code_paths,installation.resolve())}
    sys.path.insert(0,str(REPO/"simulation/delphes/scripts"))
    sys.path.insert(0,str(REPO/"simulation/rare_backgrounds/scripts"))
    import run_delphes as baseline
    import conditional_tags as tags
    config=json_load(installation)
    env,_,_,_=baseline.verify_installation(config)
    source_input=Path(config["phase6b_runs"]["jjgg"])/"shower.hepmc3.gz"
    context=baseline.source_context(source_input,"jjgg",config)
    dm=json_load(delphes_run/"run_manifest.json")
    binding_path=REPO/"simulation/rare_backgrounds/evidence/pilot/jjgg_binding.json"
    binding=json_load(binding_path)
    require(dm["status"]=="PASS" and dm["events_requested"]==1000 and dm["source_mg5_sha256"]==binding["source_mg5_sha256"],"wrong existing Delphes source")
    protected={context["source"]:binding["source_mg5_sha256"],source_input:context["input_sha256"],context["manifest_path"]:dm["source_run_manifest_sha256"],binding_path:sha(binding_path)}
    for name,path in context["files"].items(): protected[path]=context["manifest"]["files"][name]["sha256"]
    for name,descriptor in dm["files"].items(): protected[delphes_run/name]=descriptor["sha256"]
    protected[delphes_run/"run_manifest.json"]=sha(delphes_run/"run_manifest.json")
    pilot_path=REPO/"simulation/rare_backgrounds/evidence/pilot/jjgg.jsonl"
    protected[pilot_path]=binding["reco_sha256"]
    mg_path=REPO/"reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/sample_manifest.json"
    protected[mg_path]=sha(mg_path)
    protected.update(preflight_snapshots)
    require(all(sha(path)==digest for path,digest in protected.items()),"original source/card/run bytes changed")
    ledger,ledger_hash=selected_row(context["files"]["event_ledger.jsonl"])
    diagnostic,diagnostic_hash=selected_row(context["files"]["particle_diagnostics.jsonl"])
    source,source_row_hash=selected_row(context["files"]["source_events.jsonl"])
    pilot,pilot_row_hash=selected_row(pilot_path)
    lhe=next(row for row in baseline.hepmc.iter_lhe_events(context["source"]) if row["source_event_index"]==SOURCE_INDEX)
    require(lhe["source_event_content_hash"]==source["source_event_content_hash"]==ledger["source_event_content_hash"]==pilot["source_event_hash"]==SOURCE_HASH,"LHE/ledger/pilot exact source997 hash mismatch")
    header=None; exact_raw=None
    for kind,raw in baseline.hepmc.iter_ascii(source_input):
        if kind=="header": header=baseline.hepmc.parse_header(raw)
        elif kind=="event" and int(raw.splitlines()[0].split()[1])==SOURCE_INDEX:
            exact_raw=raw; break
    require(exact_raw is not None,"HepMC event997 missing")
    checked=baseline.hepmc.parse_event(exact_raw,header)
    hg=parse_hepmc(exact_raw); pg=pythia_graph(diagnostic["particles"])
    require(hg["exact_event_sha256"]==ledger["output_event_hash"]==pilot["input_hepmc_event_hash"]==EVENT_HASH,"exact HepMC event997 checksum mismatch")
    require(checked["identity"]["source_event_content_hash"]==SOURCE_HASH and checked["identity"]["source_event_index"]=="997", "HepMC identity attributes mismatch")
    require(ledger["source_event_index"]==ledger["output_event_index"]==diagnostic["source_event_index"]==diagnostic["output_event_index"]==997,"one-based source identity not proven")
    require(ledger["processing_status"]=="WRITTEN" and ledger["source_total_events"]==1000,"wrong source processing/denominator")
    require(Decimal(pilot["source_contribution_pb"])==Decimal(str(source["nominal_generator_weight"]))/1000,"original exact source weight mismatch")
    require(not output.exists(),"output exists; choose a new forensic directory")
    output.mkdir(parents=True)
    payload={"root_file":str(delphes_run/"detector.root"),"library":str(Path(config["delphes_prefix"])/"lib/libDelphes.so"),
             "root_sha256":binding["root_sha256"],"hepmc_particles":list(hg["particles"].values()),"hepmc_vertices":hg["vertices"]}
    child=subprocess.run([str(Path(config["root_prefix"])/"bin/python"),"-B",str(Path(__file__).resolve()),"--native-readback"],
                         input=json.dumps(payload),text=True,capture_output=True,env=env,timeout=120,check=True)
    root=json.loads(child.stdout.strip().splitlines()[-1])
    (output/"native_readback.log").write_text(child.stderr,encoding="utf-8")
    for name in ("jets","photons"):
        require([{key:row[key] for key in root[name][0]} for row in pilot[name]]==root[name],"ROOT/pilot persisted "+name+" fields differ")
    jets=[j for j in root["jets"] if j["pt"]>25 and abs(j["eta"])<2.5]
    mapping=match_pythia_hepmc(pg,hg["particles"])
    pair_births=[{"mother":pid,"daughters":row["daughters"]} for pid,row in pg.items() if row["pdg_id"]==21 and abs(row["status"])==51
                 and sorted(pg[d]["pdg_id"] for d in row["daughters"])==[-5,5]]
    require(audit_graph(pg)["status"]==audit_graph(hg["particles"])["status"]=="PASS","inconsistent original ancestry graph")
    relevant={pid for pid,row in pg.items() if abs(row["pdg_id"]) in (4,5) or row["terminal_b_hadron"] or row["terminal_c_hadron"]}
    origin_nodes=sorted(relevant | set().union(*(set(ancestors(pg,pid)) for pid in relevant)))
    associated_hadrons=defaultdict(list)
    hadron_ambiguities=[]
    for pid,row in pg.items():
        if not (row["terminal_b_hadron"] or row["terminal_c_hadron"]): continue
        row=dict(row,perturbative_bottom_birth_ancestor_candidates=sorted(set(ancestors(pg,pid))&{19,20}),
                 sole_bottom_line_attribution="UNKNOWN; multi-mother string ancestry and geometric matching do not prove a sole bottom endpoint")
        distances=sorted((delta_r(j,row),j["index"]) for j in jets)
        if distances and distances[0][0] < .4:
            if len(distances)>1 and abs(distances[0][0]-distances[1][0])<=1e-12:
                hadron_ambiguities.append(pid)
            else: associated_hadrons[distances[0][1]].append(dict(row,delta_r=distances[0][0]))
    hard=[dict(p4_gev=row["p4_and_mass_gev"][:4],mass_gev=row["p4_and_mass_gev"][4],pdg_id=row["pdg_id"],status=row["status"],source_particle_index=i)
          for i,row in enumerate(source["particles"],1) if row["status"]==1 and abs(row["pdg_id"]) in (1,2,3,4,5,21)]
    annotated=[]
    for jet in jets:
        native=native_flavour(jet,hg["particles"])
        hard_matches=[dict(row,delta_r=delta_r(jet,row)) for row in hard if delta_r(jet,row)<=.4]
        shower_matches=[dict(row,delta_r=delta_r(jet,row)) for row in pg.values() if abs(row["pdg_id"]) in (1,2,3,4,5,21)
                        and 41<=abs(row["status"])<=59 and delta_r(jet,row)<=.4]
        hadrons=associated_hadrons[jet["index"]]
        hadron_label=5 if any(h["terminal_b_hadron"] for h in hadrons) else 4 if any(h["terminal_c_hadron"] for h in hadrons) else 0
        annotated.append({**jet,"btag_bit0":jet["btag"]&1,"baseline_probability_persisted_pt":str(tags.tag_probability(jet["flavor"],jet["pt"])),
                          "native_flavour_reproduction":native,"hard_parton_diagnostic":{"label":associated_label(hard_matches),"candidates":hard_matches},
                          "shower_parton_diagnostic":{"label":associated_label(shower_matches),"candidates":shower_matches},
                          "heavy_hadron_diagnostic":{"label":hadron_label,"candidates":hadrons,"matching":"terminal heavy hadrons each assigned once to nearest eligible jet, strictR0.4; tiesUNKNOWN; inclusive B_c flags"}})
    require(all(j["native_flavour_reproduction"]["matches_native"] for j in annotated),"native flavour semantics disagreement")
    probabilities=[tags.tag_probability(j["flavor"],j["pt"]) for j in jets]
    pairs=[]
    photons=sorted([p for p in root["photons"] if tags.photon_eligible(p)],key=lambda p:(-p["pt"],p["index"]))
    for a,b,probability in tags.leading_pair_probabilities(probabilities):
        vectors=[tags.p4(jets[a]),tags.p4(jets[b])]
        pairs.append({"leading_tagged_positions":[a,b],"native_jet_indices":[jets[a]["index"],jets[b]["index"]],
                      "probability":str(probability),"m_bb_gev":tags.combined_mass(vectors),
                      "m_bb_gamma_gamma_gev":tags.combined_mass(vectors+[tags.p4(p,True) for p in photons[:2]]) if len(photons)>=2 else None,
                      "later_tagged_jets":"unrestricted; no conditioning on recorded tagged pair"})
    mg=next(row for row in json_load(mg_path)["samples"] if row["compressed_file_sha256"]==binding["source_mg5_sha256"])
    def source_key(path):
        if path==installation.resolve(): return "local_installation_config_sha256"
        if path.is_relative_to(REPO/"simulation") and path.suffix==".py": return "code/"+path.relative_to(REPO).as_posix()
        if path==context["source"]: return "mg5/original_source_lhe"
        if path==mg_path: return "mg5/sample_manifest.json"
        if path.is_relative_to(delphes_run): return "delphes/"+path.relative_to(delphes_run).as_posix()
        if path.is_relative_to(context["manifest_path"].parent): return "pythia/"+path.relative_to(context["manifest_path"].parent).as_posix()
        return "pilot/"+path.name
    critical=(7,13,17,19,20)
    critical_mapping=all(mapping["particles"][pid]["status"]=="UNIQUE_TUPLE_MATCH" for pid in critical)
    result={"schema_version":1,"status":"PASS","process":"jjgg","source_event_index":997,
            "index_convention":"one-based LHE/ledger/HepMC Event.Number/pilot; zero-based ROOT entry996",
            "source_event_sha256":SOURCE_HASH,"hepmc_event_sha256":EVENT_HASH,
            "generator_seed":mg["random_seed"],"shower_seed":ledger["pythia_seed"],"delphes_seed":dm["detector_seed"],
            "nominal_generator_weight_pb":str(source["nominal_generator_weight"]),"source_contribution_pb":pilot["source_contribution_pb"],"normalization_denominator":1000,
            "original_pythia_ledger":ledger,"hepmc_event_weights_pb":checked["weights"],
            "source_row_hashes":{"ledger":ledger_hash,"pythia_diagnostics":diagnostic_hash,"original_hard_snapshot":source_row_hash,"pilot":pilot_row_hash},
            "input_file_sha256":{source_key(path):digest for path,digest in protected.items()},
            "root_readback":root,"original_hard_event":source,"pythia_graph":list(pg.values()),"hepmc_graph":hg,
            "pythia_graph_audit":audit_graph(pg),"hepmc_graph_audit":audit_graph(hg["particles"]),"pythia_hepmc_mapping":mapping,
            "heavy_origin_ancestry_nodes":origin_nodes,"direct_fsr_g_to_bb_births":pair_births,
            "origin_verdict":"DIRECT_FSR_G_TO_B_BBAR_CONFIRMED" if pair_births==[{"mother":17,"daughters":[19,20]}] and critical_mapping and mapping["unique_mapping_is_injective"] and not mapping["mother_edge_differences"] else "UNKNOWN",
            "origin_limit":"explicit original branching/status graph; recoil/status44/62/71 copies are not repeated pair production; multi-mother hadronization does not establish sole parton attribution; no naive intermediate split-vertex p4 closure imposed",
            "pythia_production_positions":"NOT_STORED_IN_ORIGINAL_DIAGNOSTICS; HepMC exact serialized production vertices recorded separately, no inferred Pythia coordinates",
            "eligible_jets":annotated,"terminal_hadron_matching_ambiguities":hadron_ambiguities,"possible_leading_tagged_pairs":pairs,
            "diagnostic_one_to_one_matches":{
                "original_hard_partons":unique_diagnostic_matching(hard,jets,"source_particle_index"),
                "perturbative_bottom_births":unique_diagnostic_matching([pg[19],pg[20]],jets),
                "terminal_b_hadrons":unique_diagnostic_matching([row for row in pg.values() if row["terminal_b_hadron"]],jets),
                "terminal_c_hadrons":unique_diagnostic_matching([row for row in pg.values() if row["terminal_c_hadron"]],jets)},
            "event_probability_ge2":str(tags.probability_at_least_two(probabilities)),"selection":{key:pilot[key] for key in ("N_jets","N_btags","m_gamma_gamma","m_jj","m_bb","cut_photons","cut_jets","cut_two_btags","cut_mgg")},
            "models":"original native Flavor unchanged; alternative hard/shower/hadron labels diagnostic only; persisted Float_t PT probability approximation retained",
            "new_physics_events_generated":0,"new_detector_processing":0,"source_script_sha256":protected[Path(__file__).resolve()]}
    require(all(sha(path)==digest for path,digest in protected.items()),"original bytes changed during forensic extraction")
    (output/"source997.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return result


def verify_evidence(path, manifest_path=None):
    """Portable derived-evidence replay; never opens ROOT or original samples."""
    path=Path(path)
    require(path.is_file() and path.stat().st_size<=2*1024**2,"missing/oversized bounded source997 evidence")
    evidence=json_load(path)
    if manifest_path is not None:
        manifest=json_load(manifest_path)
        require(sha(path)==manifest["evidence_sha256"] and path.stat().st_size==manifest["evidence_bytes"],"forensic evidence manifest hash/size mismatch")
        require(manifest["source_script_sha256"]==evidence["source_script_sha256"]==sha(__file__),"forensic replay source identity mismatch")
    require(evidence["status"]=="PASS" and evidence["source_event_index"]==997,
            "source997 evidence not PASS/exact identity")
    require(evidence["source_event_sha256"]==SOURCE_HASH and evidence["hepmc_event_sha256"]==EVENT_HASH,"known exact source/event hash mismatch")
    pg=pythia_graph(evidence["pythia_graph"])
    hg={int(key):value for key,value in evidence["hepmc_graph"]["particles"].items()}
    vertices=evidence["hepmc_graph"]["vertices"]
    for key,vertex in vertices.items():
        incoming,outgoing=vertex["incoming"],vertex["outgoing"]
        require(key==vertex["key"] and incoming and outgoing and len(incoming)==len(set(incoming))
                and len(outgoing)==len(set(outgoing)),"inconsistent/duplicate original vertex identity")
        for pid in incoming:
            require(pid in hg and hg[pid]["end_vertex"]==key and sorted(hg[pid]["daughters"])==sorted(outgoing),"vertex/end-particle/daughter inconsistency")
        for pid in outgoing:
            require(pid in hg and hg[pid]["production_vertex"]==key and sorted(hg[pid]["mothers"])==sorted(incoming),"vertex/production-particle/mother inconsistency")
        position=vertex["serialized_position_mm"]
        require(position is None or (len(position)==4 and all(math.isfinite(float(v)) for v in position)),"invalid serialized production position")
    for pid,row in hg.items():
        require(row["id"]==pid,"inconsistent HepMC exact particle ID")
        require(row["production_vertex"] is None or row["production_vertex"] in vertices,"dangling recorded production endpoint")
        require(row["end_vertex"] is None or row["end_vertex"] in vertices,"dangling recorded end endpoint")
    for graph,stored in ((pg,evidence["pythia_graph_audit"]),(hg,evidence["hepmc_graph_audit"])):
        checked=audit_graph(graph)
        require(checked["status"]=="PASS" and checked==stored and checked["nodes"]==571 and checked["mother_edges"]==1149,
                "derived original graph audit/count mismatch")
    mapped=match_pythia_hepmc(pg,hg)
    stored=evidence["pythia_hepmc_mapping"]
    require(mapped["unique_matches"]==stored["unique_matches"]==571 and mapped["ambiguous_or_missing"]==0
            and mapped["unique_mapping_is_injective"] and not mapped["mother_edge_differences"],"derived exact tuple/edge mapping not bijective")
    require(mapped["particles"]=={int(key):value for key,value in stored["particles"].items()},"derived particle mapping changed")
    attrs=evidence["hepmc_graph"]["attributes"]
    ledger=evidence["original_pythia_ledger"]
    require(attrs["source_event_index"]==attrs["output_event_index"]=="997" and evidence["hepmc_graph"]["event_number"]==997
            and ledger["source_event_index"]==ledger["output_event_index"]==997,"one-based source/event identity mismatch")
    require(attrs["source_event_content_hash"]==ledger["source_event_content_hash"]==SOURCE_HASH and ledger["output_event_hash"]==EVENT_HASH,
            "original serialized source identity mismatch")
    require(attrs["source_file_sha256"]==evidence["input_file_sha256"]["mg5/original_source_lhe"],"original MG5 file ancestry mismatch")
    require([evidence[key] for key in ("generator_seed","shower_seed","delphes_seed")]==[20261022,610203,610303],"source997 seed identity mismatch")
    require(Decimal(evidence["nominal_generator_weight_pb"])/1000==Decimal(evidence["source_contribution_pb"])
            and evidence["normalization_denominator"]==1000,"exact full-source weight normalization changed")
    require(pg[17]["pdg_id"]==21 and pg[17]["status"]==-51 and pg[17]["mothers"]==[13] and pg[17]["daughters"]==[19,20]
            and pg[19]["pdg_id"]==5 and pg[20]["pdg_id"]==-5 and pg[19]["status"]==pg[20]["status"]==-51
            and pg[19]["mothers"]==pg[20]["mothers"]==[17],"actual direct perturbative birth changed")
    require(pg[7]["pdg_id"]==pg[13]["pdg_id"]==21 and pg[7]["status"]==-23 and pg[13]["status"]==-44
            and pg[13]["mothers"]==[7],"hard-gluon/recoil ancestry changed")
    require(evidence["origin_verdict"]=="DIRECT_FSR_G_TO_B_BBAR_CONFIRMED","origin verdict contradicts audited exact branch")
    require(evidence["root_readback"]["status"]=="PASS" and evidence["root_readback"]["entry_zero_based"]==996
            and evidence["root_readback"]["event_number_one_based"]==997
            and evidence["root_readback"]["tree_entries"]==1000 and evidence["root_readback"]["particle_count"]==571,
            "existing native ROOT evidence identity/count mismatch")
    sys.path.insert(0,str(REPO/"simulation/rare_backgrounds/scripts"))
    import conditional_tags as tags
    jets=evidence["eligible_jets"]
    original_jets=[j for j in evidence["root_readback"]["jets"] if tags.jet_eligible(j)]
    require([{key:j[key] for key in original_jets[0]} for j in jets]==original_jets,"eligible jets differ from exact native ROOT snapshot")
    photons=[row for row in evidence["root_readback"]["photons"] if tags.photon_eligible(row)]
    selected=tags.analyze_event({**evidence["selection"],"jets":evidence["root_readback"]["jets"],
                               "photons":evidence["root_readback"]["photons"],"source_contribution_pb":evidence["source_contribution_pb"],
                               "ordinal":997,"native_event_number":997,"source_event_index":997,
                               "source_event_hash":SOURCE_HASH,"input_hepmc_event_hash":EVENT_HASH},scenarios={"baseline":tags.SCENARIOS["baseline"]})
    require(selected["eligible_jets"]==5 and selected["observed_eligible_tags"]==1,"native source997 frozen selection/tag counts changed")
    require(len(photons)>=2 and math.isclose(tags.combined_mass([tags.p4(p,True) for p in photons[:2]]),
                                           evidence["selection"]["m_gamma_gamma"],rel_tol=2e-12,abs_tol=2e-8),
            "native photon snapshot/selected diphoton mass inconsistency")
    require([j["flavor"] for j in jets]==[5,2,21,21,5],"original native eligible labels changed")
    probabilities=[]
    for jet in jets:
        native=native_flavour(jet,hg)
        require(native["attainable_labels"]==jet["native_flavour_reproduction"]["attainable_labels"] and native["matches_native"],"native parton/cone semantics mismatch")
        require([p["id"] for p in native["definite_candidates"]]==[p["id"] for p in jet["native_flavour_reproduction"]["definite_candidates"]],"exact native parton candidate set changed")
        recorded=Decimal(jet["baseline_probability_persisted_pt"])
        computed=tags.tag_probability(jet["flavor"],jet["pt"])
        require(abs(computed-recorded)<=abs(recorded)*Decimal(str(64*sys.float_info.epsilon))+Decimal("1e-44"),"card probability differs beyond preserved Phase6D cross-host rounding envelope")
        probabilities.append(recorded)
    require(abs(tags.probability_at_least_two(probabilities)-Decimal(evidence["event_probability_ge2"]))<=Decimal("1e-44"),"direct Decimal two-tag tail changed")
    saved={(row["leading_tagged_positions"][0],row["leading_tagged_positions"][1]):row for row in evidence["possible_leading_tagged_pairs"]}
    for a,b,probability in tags.leading_pair_probabilities(probabilities):
        require((a,b) in saved and abs(probability-Decimal(saved[a,b]["probability"]))<=Decimal("1e-44"),"exact leading-pair decomposition changed")
        vectors=[tags.p4(jets[a]),tags.p4(jets[b])]
        for key,value in (("m_bb_gev",tags.combined_mass(vectors)),
                          ("m_bb_gamma_gamma_gev",tags.combined_mass(vectors+[tags.p4(p,True) for p in photons[:2]]))):
            require(math.isclose(saved[a,b][key],value,rel_tol=2e-12,abs_tol=2e-8),"derived pair mass differs beyond preserved Cartesian replay tolerance")
    require(len(saved)==10,"missing/duplicate source997 possible pair")
    return {"status":"PASS_OFFLINE_REPLAY","source_event_index":997,"evidence_sha256":sha(path),
            "graph_nodes":571,"graph_edges":1149,"exact_tuple_mapping":"571 unique, mapped mother edges identical",
            "event_probability_ge2":evidence["event_probability_ge2"],"possible_pairs":len(saved),
            "manifest_hash_binding":"PASS" if manifest_path is not None else "NOT_REQUESTED",
            "native_ROOT_execution":"NOT_EXECUTED_BY_OFFLINE_REPLAY; prior actual native evidence retained",
            "new_physics_events_generated":0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation",type=Path,default=REPO/".local/delphes_installation.json")
    parser.add_argument("--delphes-run",type=Path,default=Path.home()/"simulations/delphes_runs/stage_c_jjgg_1000")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--native-readback",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--verify-evidence",type=Path,help="offline derived graph/flavour/probability replay; no native readback")
    parser.add_argument("--manifest",type=Path,default=REPO/"metadata/phase6e_source997_manifest.json")
    args=parser.parse_args()
    if args.native_readback:
        print(json.dumps(native_root_snapshot(json.load(sys.stdin)),separators=(",",":"),allow_nan=False));return
    if args.verify_evidence:
        print(json.dumps(verify_evidence(args.verify_evidence,args.manifest),indent=2));return
    require(args.output is not None,"--output required")
    result=build(args.installation,args.delphes_run,args.output)
    print(json.dumps({"status":result["status"],"source_event_index":997,"origin":result["origin_verdict"],"eligible_flavours":[j["flavor"] for j in result["eligible_jets"]],"evidence_sha256":sha(args.output/"source997.json")},indent=2))


if __name__=="__main__":
    try: main()
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print("FAIL: "+str(error),file=sys.stderr);raise SystemExit(1)
