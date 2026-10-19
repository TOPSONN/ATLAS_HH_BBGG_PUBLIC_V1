#!/usr/bin/env python3
"""Read-only frozen-input audit. Never imports or dispatches a generator/native runtime."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, math, re, sys
from pathlib import Path

IDS = ("S01_B100", "S01_C1000", "B01", "B02", "B03", "B04", "B05", "B06")
VERSION = "PHASE8_HISTORICAL_FROZEN_B80_V1"
BASE = "b80e16775bf141e45f4048c7197a8a99befaed51"
HEX = re.compile(r"[0-9a-f]{64}\Z")
ROLES = ("root", "input_index", "truth_index", "card", "lhe", "hepmc", "historical_reco")

class AuditError(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise AuditError(reason)

def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def resolve_path(value, repository, home):
    require(isinstance(value, str), "path must be a string")
    roots = {"REPOSITORY/": Path(repository).resolve(), "LOCAL_HOME/": Path(home).resolve()}
    for prefix, root in roots.items():
        if value.startswith(prefix):
            relative = value[len(prefix):]
            require(relative and not Path(relative).is_absolute() and ".." not in Path(relative).parts, "unsafe logical path")
            result = (root / relative).resolve()
            require(result.is_relative_to(root), "logical path escaped approved root")
            return result
    raise AuditError("unknown portable path alias")

def finite(token):
    try:
        value = float(token)
    except (ValueError, OverflowError) as error:
        raise AuditError("invalid source-index number") from error
    require(math.isfinite(value), "nonfinite source-index number")
    return value

def audit_index(path, expected_entries, original_count):
    """Independent strict line parser for reviewed ATLAS_DELPHES_INPUT_V1."""
    rows, ordinals, numbers, sources = [], set(), set(), set()
    count_particles = 0
    with Path(path).open(encoding="utf-8") as stream:
        require(stream.readline().strip() == "ATLAS_DELPHES_INPUT_V1", "BLOCKED_SCHEMA: input index magic")
        for line in stream:
            require(line.strip(), "unexpected blank input-index record")
            cells = line.split()
            require(len(cells) == 11 and cells[0] == "E", "malformed E input-index row")
            try:
                ordinal, number, source = int(cells[1]), int(cells[2]), int(cells[4])
                N, np, nw = int(cells[8]), int(cells[9]), int(cells[10])
            except ValueError as error:
                raise AuditError("invalid integer input-index field") from error
            require(ordinal == len(rows) + 1 and source == ordinal, "BLOCKED_EVENT_IDENTITY: missing/reordered source ordinal")
            require(ordinal not in ordinals and number not in numbers and source not in sources, "BLOCKED_EVENT_IDENTITY: duplicate source/event key")
            require(HEX.fullmatch(cells[3]) and HEX.fullmatch(cells[5]), "invalid event source hash")
            require(N == original_count and 0 < np <= 100000 and 0 < nw <= 256, "wrong/bounded original denominator or collection size")
            contribution, raw = finite(cells[6]), finite(cells[7])
            require(math.isclose(contribution, raw / N, rel_tol=1e-12, abs_tol=1e-15), "source contribution denominator mismatch")
            weights = stream.readline().split()
            require(len(weights) == nw + 1 and weights[0] == "W", "missing/truncated W row")
            weights = [finite(v) for v in weights[1:]]
            require(weights[0] == contribution, "source nominal-vector weight mismatch")
            particle_ids = set()
            for _ in range(np):
                particle = stream.readline().split()
                require(len(particle) == 14 and particle[0] == "P", "missing/truncated P row")
                try:
                    ident = int(particle[1]); int(particle[2]); int(particle[3]); int(particle[9])
                except ValueError as error:
                    raise AuditError("invalid particle integer field") from error
                require(ident not in particle_ids, "duplicate particle ID within source event")
                particle_ids.add(ident)
                for column in (4, 5, 6, 7, 8, 10, 11, 12, 13):
                    finite(particle[column])
            ordinals.add(ordinal); numbers.add(number); sources.add(source)
            count_particles += np
            rows.append({"ordinal": ordinal, "native_event_number": number, "source_event_index": source,
                         "source_event_sha256": cells[5], "hepmc_event_sha256": cells[3],
                         "raw_weight_pb": raw, "source_contribution_pb": contribution})
    require(len(rows) == expected_entries, "BLOCKED_EVENT_IDENTITY: truncated/prefix index differs from declared expected entries")
    return {"status": "PASS_SOURCE_INDEX_IDENTITY_PENDING_NATIVE_ROOT", "actual_index_events": len(rows),
            "N_original": original_count, "duplicate_keys": 0, "missing_ordinals": 0,
            "finite_particle_records": count_particles, "event_identity_digest": hashlib.sha256(canonical(rows)).hexdigest(),
            "first_identity": rows[0] if rows else None, "last_identity": rows[-1] if rows else None}, rows

def audit_lhe(path, expected_entries, index_rows):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        text = stream.read(64 * 1024 * 1024 + 1)
    require(len(text) <= 64 * 1024 * 1024, "LHE bounded-input limit")
    events = re.findall(r"<event(?:\s[^>]*)?>\s*(.*?)</event>", text, re.S)
    require(len(events) == expected_entries, "LHE original source count differs")
    require("</LesHouchesEvents>" in text, "LHE missing final document close")
    weights = []
    for ordinal, event in enumerate(events, 1):
        header = event.splitlines()[0].split()
        require(len(header) >= 6, "malformed LHE event header")
        weight = finite(header[2]); weights.append(weight)
        require(math.isclose(weight, index_rows[ordinal - 1]["raw_weight_pb"], rel_tol=1e-12, abs_tol=1e-15), "LHE/source-index raw weight mismatch")
    seed = re.findall(r"(?m)^\s*(\d+)\s*=\s*iseed\b", text)
    return {"status": "PASS_ACTUAL_EXISTING_LHE_COUNT_AND_RAW_WEIGHT_IDENTITY", "events": len(events),
            "embedded_iseed": int(seed[0]) if len(seed) == 1 else None,
            "sum_raw_XWGTUP_pb": math.fsum(weights), "source_contribution_sum_pb": math.fsum(v["source_contribution_pb"] for v in index_rows),
            "scope": "LHE source and frozen index identity; no native ROOT read implied"}

def check_file(role, path, expected):
    require(HEX.fullmatch(expected), "invalid expected SHA256")
    require(path.is_file(), "BLOCKED_MISSING_DATA: " + role)
    actual = digest(path)
    require(actual == expected, "BLOCKED_HASH_MISMATCH: " + role)
    return {"role": role, "path": str(path), "sha256": actual, "bytes": path.stat().st_size, "status": "PASS_EXACT_BYTES"}

def audit_manifest(manifest, repository, home):
    require(manifest.get("sample_version") == VERSION and manifest.get("base_revision") == BASE, "wrong sample version or frozen revision")
    datasets = manifest.get("datasets")
    require(isinstance(datasets, list) and tuple(d["dataset_id"] for d in datasets) == IDS, "unknown, duplicate or reordered dataset")
    records, local, identity = [], json.loads(json.dumps(manifest)), []
    for d, target in zip(datasets, local["datasets"]):
        require(d.get("is_full") is True and d["expected_entries"] == d["N_original"] and d["N_original"] in (100, 1000), "full/prefix declaration invalid")
        require(d["truth_format"] in ("signal", "continuum", "new_background"), "unsupported truth object version")
        require(len(d["expected_cutflow"]) == 5 and d["expected_cutflow"][0] == d["N_original"], "bad historical cutflow denominator")
        files = []
        roles = ROLES + tuple(r for r in ("ancestry", "source_hepmc_gz") if r + "_path" in d)
        for role in roles:
            path = resolve_path(d[role + "_path"], repository, home)
            files.append(check_file(role, path, d[role + "_sha256"]))
            target[role + "_path"] = str(path)
        for card in d.get("generator_cards", []):
            files.append(check_file("generator_card:" + card["role"], resolve_path(card["path"], repository, home), card["sha256"]))
        index, rows = audit_index(target["input_index_path"], d["expected_entries"], d["N_original"])
        lhe = audit_lhe(target["lhe_path"], d["N_original"], rows)
        require(lhe["embedded_iseed"] == d["actual_effective_seed"], "source seed differs from audited effective seed")
        card_text = Path(target["card_path"]).read_text()
        start = card_text.find("module BTagging BTagging {")
        require(start >= 0, "missing native BTagging module")
        end = card_text.find("\n}", start)
        require(end >= 0, "unterminated BTagging module")
        tag_digest = hashlib.sha256(card_text[start:end + 2].encode()).hexdigest()
        require(tag_digest == manifest["btag_model"]["module_sha256"], "native btag formula/bit0 contract changed")
        identity.append({"dataset_id": d["dataset_id"], **index, "LHE": lhe, "btag_module_sha256": tag_digest})
        records.extend({"dataset_id": d["dataset_id"], **f} for f in files)
        target["verification_status"] = "SOURCE_HASH_PASS_PENDING_NATIVE_READ"
        target["actual_TTree_entries"] = None
    kappa = manifest["kappa_rows"]
    records.append({"dataset_id": "S01_C1000_KAPPA", **check_file("event_reweights", resolve_path(kappa["path"], repository, home), kappa["sha256"])})
    local["kappa_rows"]["path"] = str(resolve_path(kappa["path"], repository, home))
    return {"schema_version": 1, "status": "SOURCE_HASH_PASS_PENDING_NATIVE_READ", "evidence_class": "HISTORICAL_EVIDENCE_AUDIT", "files_verified": len(records), "file_bytes": sum(f["bytes"] for f in records), "files": records,
            "native_ROOT_readback": "PENDING_SEPARATE_CPP_ANALYSIS", "new_ME_calls": 0, "new_events": 0}, local, identity

def verify_snapshot(snapshot):
    changes = []
    for item in snapshot["files"]:
        path = Path(item["path"])
        if not path.is_file() or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            changes.append({"dataset_id": item["dataset_id"], "role": item["role"], "reason": "SOURCE_CHANGED"})
    require(not changes, "source preservation check failed")
    return {"schema_version": 1, "status": "PASS_ALL_BOUND_INPUT_BYTES_UNCHANGED", "files_verified": len(snapshot["files"]), "new_ME_calls": 0, "new_events": 0}

def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "config/datasets.json")
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-snapshot", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.verify_snapshot:
            require(not args.output.exists(), "existing output overwrite refused")
            value = verify_snapshot(json.loads(args.verify_snapshot.read_text()))
            write_new(args.output, value)
            print(json.dumps({k: v for k, v in value.items() if k != "files"}))
            return 0
        names = ("phase8a_source_audit.json", "phase8_local_manifest.json", "phase8a_event_identity_audit.json", "phase8_input_preservation_before.json")
        require(all(not (args.output / name).exists() for name in names), "existing audit output overwrite refused")
        manifest = json.loads(args.config.read_text())
        audit, local, identity = audit_manifest(manifest, args.repository, args.home)
        args.output.mkdir(parents=True, exist_ok=True)
        for name, value in zip(names, (audit, local, {"evidence_class": "HISTORICAL_EVIDENCE_AUDIT", "status": "PASS_FROZEN_SOURCE_INDEX_PENDING_NATIVE_ROOT", "datasets": identity}, audit)):
            write_new(args.output / name, value)
        print(json.dumps({k: v for k, v in audit.items() if k != "files"}))
        return 0
    except (AuditError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "BLOCKED_INPUT_AUDIT", "reason": str(error), "new_ME_calls": 0, "new_events": 0}), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
