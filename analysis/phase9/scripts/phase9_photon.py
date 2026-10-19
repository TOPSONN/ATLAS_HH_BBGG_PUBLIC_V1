"""Existing-graph photon-origin diagnostics; never a photon-fake calibration.

Only photon-copy chains are followed to the first non-photon parents. Following
all ancestors would wrongly classify every proton-collision photon as hadronic.
Reco association is a conservative exclusive cone diagnostic, not a detector
response or a calibrated fake probability. No event generator is imported.
"""
from __future__ import annotations
import math
from collections import Counter

CLASSES = ("PROMPT_HARD_PROCESS", "SHOWER_RADIATION", "HADRON_DECAY",
           "ELECTRON_ASSOCIATED", "UNCLASSIFIED")
RADIUS = 0.2

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def is_hadron(pid):
    """PDG meson/baryon digits; excludes elementary, diquark, nucleus, BSM IDs."""
    n = abs(int(pid))
    if n < 100 or n >= 1_000_000_000:
        return False
    q1, q2, q3, spin = (n // 1000) % 10, (n // 100) % 10, (n // 10) % 10, n % 10
    return (1 <= q2 <= 6 and 1 <= q3 <= 6 and spin > 0
            and (q1 == 0 or 1 <= q1 <= 6))

def p4_close(a, b):
    return len(a) == len(b) == 4 and all(math.isfinite(float(x)) and math.isfinite(float(y))
        and math.isclose(float(x), float(y), rel_tol=1e-8, abs_tol=1e-7) for x, y in zip(a, b))

def hard_photon_binding(particles, lhe_event):
    """Unique outgoing LHE photon to native graph 23/22/1 identity; no ordinals.

    Finite tolerance covers LHE decimal serialization only. Multiplicities and
    absent/ambiguous matches are retained. Independent graph lineages later
    require a unique same-PDG photon-copy path, never the full proton ancestry.
    """
    hard = [p for p in lhe_event["particles"] if p["pdg_id"] == 22 and p["status"] == 1]
    rows = []
    for p in hard:
        # Imported hard photons retain Pythia hard-process status 23 (or 22).
        # A stable hard photon without a copy may be written with status 1.
        hits = [pid for pid, q in particles.items() if q["pdg_id"] == 22
                and q["status"] in (1, 22, 23) and p4_close(p["p4_gev"], q["p4_gev"])]
        rows.append({"lhe_index": p["index"], "candidate_ids": sorted(hits),
                     "status": "UNIQUE" if len(hits) == 1 else "AMBIGUOUS" if hits else "NO_MATCH"})
    multiplicity = Counter(pid for r in rows for pid in r["candidate_ids"] if r["status"] == "UNIQUE")
    for r in rows:
        if r["status"] == "UNIQUE" and multiplicity[r["candidate_ids"][0]] != 1:
            r["status"] = "AMBIGUOUS"
    return rows

def photon_origin(particles, pid, bound_hard_ids):
    require(pid in particles and particles[pid]["pdg_id"] == 22, "photon identity unavailable")
    seen, active, first_nonphotons, copy_ids, births = set(), set(), set(), set(), set()
    def visit(key):
        require(key in particles, "dangling photon ancestry")
        require(key not in active, "cyclic photon ancestry")
        if key in seen:
            return
        active.add(key)
        q = particles[key]
        copy_ids.add(key)
        photon_mothers = []
        for m in q["mothers"]:
            require(m in particles, "dangling photon mother")
            if particles[m]["pdg_id"] == 22:
                photon_mothers.append(m)
            else:
                first_nonphotons.add(m)
        if not photon_mothers:
            births.add(key)
        for m in photon_mothers:
            visit(m)
        active.remove(key)
        seen.add(key)
    visit(pid)
    parent_pids = sorted(set(particles[m]["pdg_id"] for m in first_nonphotons))
    hard_ids = sorted(copy_ids & set(bound_hard_ids))
    hadron = any(particles[m].get("is_hadron", is_hadron(particles[m]["pdg_id"])) for m in first_nonphotons)
    electron = any(abs(p) == 11 for p in parent_pids)
    radiation = any(particles[b].get("original_pythia_status") is not None and 41 <= abs(particles[b]["original_pythia_status"]) <= 59 for b in births)
    reason = "NO_JUSTIFIED_EXCLUSIVE_ORIGIN"
    label = "UNCLASSIFIED"
    if (hadron and (electron or hard_ids)) or (electron and hard_ids):
        reason = "CONFLICTING_COPY_CHAIN_ORIGINS"
    elif hadron:
        label, reason = "HADRON_DECAY", "FIRST_NONPHOTON_PARENT_IS_HADRON"
    elif electron:
        label, reason = "ELECTRON_ASSOCIATED", "FIRST_NONPHOTON_PARENT_IS_ELECTRON"
    elif hard_ids:
        label, reason = "PROMPT_HARD_PROCESS", "VERIFIED_HARD_ROOT_ON_PHOTON_COPY_CHAIN"
    elif radiation and any(abs(p) in (1, 2, 3, 4, 5, 6, 13, 15, 21, 24) for p in parent_pids):
        label, reason = "SHOWER_RADIATION", "STATUS_41_59_BIRTH_AND_EMITTER_PARENT"
    return {"origin": label, "reason": reason, "truth_particle_id": pid,
            "copy_chain_ids": sorted(copy_ids), "first_nonphoton_parent_ids": sorted(first_nonphotons),
            "first_nonphoton_parent_pdg_ids": parent_pids, "bound_hard_photon_ids": hard_ids,
            "birth_hepmc_statuses": sorted(set(particles[b]["status"] for b in births)),
            "birth_original_pythia_statuses": sorted(set(particles[b]["original_pythia_status"] for b in births if particles[b].get("original_pythia_status") is not None))}

def eta_phi(p):
    x, y, z, e = map(float, p["p4_gev"])
    require(all(math.isfinite(v) for v in (x, y, z, e)), "nonfinite truth four-vector")
    pt = math.hypot(x, y)
    return pt, math.asinh(z / pt) if pt else math.copysign(math.inf, z), math.atan2(y, x)

def delta_r(reco, truth):
    _, eta, phi = eta_phi(truth)
    return math.hypot(float(reco["eta"]) - eta,
                      math.remainder(float(reco["phi"]) - phi, 2 * math.pi))

def truth_fiducial(p):
    pt, eta, _ = eta_phi(p)
    return pt > 25 and abs(eta) < 2.37 and not 1.37 < abs(eta) < 1.52

def reco_selected(p):
    if "selected" in p:
        require(isinstance(p["selected"], bool), "native selected flag is not boolean")
        return p["selected"]
    eta = abs(float(p["eta"]))
    return float(p["pt"]) > 25 and eta < 2.37 and not 1.37 < eta < 1.52

def classify_photons(graph, reco_event, lhe_event):
    """Return all reco-photon labels plus stable-truth aggregate diagnostics.

    Called once per already-identity-validated event by the shared graph driver.
    No geometric match is called a jet->photon or electron->photon fake rate.
    """
    particles = graph["particles"]
    if particles and isinstance(next(iter(particles)), str):
        particles = {int(k): v for k, v in particles.items()}
    require(len(particles) <= 100000, "unbounded graph")
    attrs = graph.get("attributes", {})
    source_hash = lhe_event.get("source_event_sha256")
    if attrs.get("source_event_content_hash") is not None:
        require(attrs["source_event_content_hash"] == source_hash, "LHE/HepMC photon source identity mismatch")
    binding = hard_photon_binding(particles, lhe_event)
    bound_ids = set(graph.get("hard_photon_roots", []))
    require(not bound_ids or graph.get("hard_photon_roots_status") == "VERIFIED_SOURCE_LEDGER_OR_DECAY_LINEAGE", "unverified hard photon roots")
    require(all(pid in particles and particles[pid]["pdg_id"] == 22 for pid in bound_ids), "invalid hard photon root")
    photons = {pid: p for pid, p in particles.items() if p["pdg_id"] == 22 and p["status"] == 1}
    electrons = {pid: p for pid, p in particles.items() if abs(p["pdg_id"]) == 11 and p["status"] == 1}
    origins = {pid: photon_origin(particles, pid, bound_ids) for pid in photons}
    reco = reco_event["photons"]
    require(len({p["index"] for p in reco}) == len(reco), "duplicate native photon index")
    for p in reco:
        require(all(math.isfinite(float(p[k])) for k in ("pt", "eta", "phi")), "nonfinite native photon")
        require(float(p["pt"]) >= 0, "negative native photon pt")
    pc = {p["index"]: [pid for pid, q in photons.items() if delta_r(p, q) < RADIUS] for p in reco}
    ec = {p["index"]: [pid for pid, q in electrons.items() if delta_r(p, q) < RADIUS] for p in reco}
    reused_p = Counter(pid for ids in pc.values() for pid in ids)
    reused_e = Counter(pid for ids in ec.values() for pid in ids)
    rows = []
    for p in reco:
        index = p["index"]
        ph, el = pc[index], ec[index]
        row = {"native_photon_index": index, "pt": p["pt"], "eta": p["eta"], "phi": p["phi"],
               "selected": reco_selected(p),
               "origin": "UNCLASSIFIED", "reason": "NO_STABLE_PHOTON_OR_ELECTRON_IN_CONE",
               "photon_candidate_ids": sorted(ph), "electron_candidate_ids": sorted(el),
               "matched_truth_id": None, "delta_r": None}
        if len(ph) == 1 and reused_p[ph[0]] == 1 and not el:
            q = origins[ph[0]]
            row.update(origin=q["origin"], reason=q["reason"], matched_truth_id=ph[0],
                       delta_r=delta_r(p, photons[ph[0]]), truth_origin=q)
        elif not ph and len(el) == 1 and reused_e[el[0]] == 1:
            row.update(origin="ELECTRON_ASSOCIATED", reason="EXCLUSIVE_STABLE_ELECTRON_CONE_ASSOCIATION",
                       matched_truth_id=el[0], delta_r=delta_r(p, electrons[el[0]]))
        elif ph or el:
            row["reason"] = "AMBIGUOUS_OR_NONEXCLUSIVE_GEOMETRIC_ASSOCIATION"
        rows.append(row)
    truth_counts = {k: sum(r["origin"] == k for r in origins.values()) for k in CLASSES}
    truth_fiducial_counts = {k: sum(r["origin"] == k and truth_fiducial(photons[pid]) for pid, r in origins.items()) for k in CLASSES}
    return {"test_scope": "ACTUAL_EXISTING_DATA_READBACK", "source_event_sha256": source_hash,
            "origin_definition": "PHOTON_COPY_FIRST_NONPHOTON_PARENT_V1", "matching_definition": "EXCLUSIVE_CONE_DR_LT_0P2_NO_ELECTRON_CONFLICT",
            "fake_rate_status": "BLOCKED_CALIBRATION_UNAVAILABLE", "calibrated_fake_probability": None,
            "born_photons": len(binding), "hard_photon_binding": binding, "hard_photon_binding_scope": "SERIALIZATION_DIAGNOSTIC_ONLY_NOT_IDENTITY", "verified_hard_photon_roots": sorted(bound_ids),
            "stable_truth_photon_counts": truth_counts, "fiducial_truth_photon_counts": truth_fiducial_counts,
            "native_reco_photon_counts": {k: sum(r["origin"] == k for r in rows) for k in CLASSES},
            "selected_reco_photon_counts": {k: sum(r["origin"] == k and r["selected"] for r in rows) for k in CLASSES},
            "reco_photons": rows, "electrons_available": reco_event.get("electrons_available", False)}

def require_fake_calibration(calibration):
    require(isinstance(calibration, dict), "BLOCKED_CALIBRATION_UNAVAILABLE")
    require(calibration.get("status") == "VALIDATED_COMPATIBLE_DATA_CALIBRATION",
            "BLOCKED_CALIBRATION_UNAVAILABLE")
    for key in ("source_version", "data_period", "energy_tev", "object_definition", "transfer_factor_semantics", "applicability", "uncertainties", "license"):
        require(calibration.get(key) is not None, "BLOCKED_CALIBRATION_UNAVAILABLE:" + key)
    return calibration

def event_flags(result):
    """Event indicators; full-cohort N denominator belongs to driver statistics."""
    return {"HAS_SELECTED_RECO_" + k: result["selected_reco_photon_counts"][k] > 0 for k in CLASSES}

def object_counts(result):
    """Object counts do not represent independent event counts or fake rates."""
    return {prefix + "_" + k: result[field][k]
            for prefix, field in (("STABLE_TRUTH", "stable_truth_photon_counts"),
                                  ("FIDUCIAL_TRUTH", "fiducial_truth_photon_counts"),
                                  ("NATIVE_RECO", "native_reco_photon_counts"),
                                  ("SELECTED_RECO", "selected_reco_photon_counts"))
            for k in CLASSES}
