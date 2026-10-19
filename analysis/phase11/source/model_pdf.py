"""Static Candidate A audit. Never imports or invokes a generator or PDF library."""
from __future__ import annotations
import ast
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re

EVIDENCE_CLASS = "HISTORICAL_SOURCE_AUDIT"
SOURCE_FILES = (
    "VERSION", "models/import_ufo.py", "models/sm/parameters.py",
    "models/sm/restrict_default.dat", "models/sm/restrict_no_b_mass.dat",
    "models/sm/restrict_c_mass.dat", "models/sm/particles.py",
    "models/sm/coupling_orders.py", "Template/LO/Source/PDF/pdf_list.txt",
    "Template/LO/Source/PDF/pdfwrap.f", "Template/LO/Source/alfas_functions.f",
    "Template/LO/Source/alfas_functions_lhapdf.f",
    "Template/Common/Source/PDF/Ctq6Pdf.f",
    "Template/Common/Source/PDF/pdf_lhapdf6.cc",
    "Template/Common/Source/PDF/NNPDFDriver.f",
    "Template/LO/lib/Pdfdata/cteq6l1.tbl",
    "input/mg5_configuration.txt",
)
WITNESSES = {
    "VERSION": ("version = 3.5.16",),
    "models/import_ufo.py": ("if restrict and os.path.exists", "restrict_default.dat"),
    "models/sm/restrict_default.dat": ("# MC", "# MB", "# aS"),
    "models/sm/restrict_no_b_mass.dat": ("# MC", "# MB"),
    "models/sm/restrict_c_mass.dat": ("# MC", "# MB"),
    "models/sm/parameters.py": ("MC = Parameter", "MB = Parameter", "value = 1.27", "value = 4.7"),
    "models/sm/coupling_orders.py": ("QCD = CouplingOrder", "QED = CouplingOrder", "hierarchy ="),
    "Template/LO/Source/PDF/pdf_list.txt": ("CTEQ5F4", "CTEQ6L1", "NNPDF23LO"),
    "Template/LO/Source/PDF/pdfwrap.f": ("nloop=2", "cteq6l1", "asmz=0.130d0", "nloop=1", "cteq5f4"),
    "Template/LO/Source/alfas_functions.f": (
        "PARAMETER(NF5=5,NF4=4,NF3=3)", "DATA CMASS,BMASS/", "Q  .LT. BMASS",
        "Q  .LT. CMASS", "CALL NEWTON1(T,asmz,AS_OUT,NLOOP,NF5)"),
    "Template/LO/Source/alfas_functions_lhapdf.f": ("wrapper to the lhapdf alphaS", "ALPHAS=alphasPDF(Q)"),
    "Template/Common/Source/PDF/pdf_lhapdf6.cc": ("AlphaS_OrderQCD", "alphaspdfm_", "alphasQ(Q)"),
    "Template/Common/Source/PDF/Ctq6Pdf.f": ("Q=4.5 GeV", "Nfl = Nint(Fl)",),
    "Template/LO/lib/Pdfdata/cteq6l1.tbl": ("Ordr, Nfl", "1.    5.", "NfMx"),
}
PRIMARY_SOURCES = [
    {"url": "https://www.lhapdf.org/config.html", "scope": "PDF/member metadata, alpha_s orders and flavour-threshold fallback semantics"},
    {"url": "https://www.lhapdf.org/pdfsets", "scope": "public availability catalogue is distinct from installed member payloads"},
]

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()

def source_record(path, tokens=()):
    p = Path(path)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    witnesses = [{"line": i, "text": line} for i, line in enumerate(lines, 1)
                 if any(token.lower() in line.lower() for token in tokens)]
    return {"path": str(p), "resolved_path": str(p.resolve()), "bytes": p.stat().st_size,
            "sha256": sha256(p), "witnesses": witnesses}

def parse_slha_blocks(text):
    """Parse numeric one-index BLOCK records without importing UFO or MG5."""
    answer = {}
    block = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        if tokens[0].upper() == "BLOCK":
            block = tokens[1].upper()
            answer.setdefault(block, {})
        elif tokens[0].upper() == "DECAY":
            block = None
        elif block and len(tokens) >= 2:
            try:
                key = int(tokens[0])
                value = Decimal(tokens[1].replace("D", "E").replace("d", "e"))
            except (ValueError, ArithmeticError):
                continue
            if not value.is_finite():
                raise ValueError("NONFINITE_SLHA_PARAMETER")
            answer[block][key] = value
    return answer

def ufo_external_defaults(text):
    """AST read only: no evaluation/import of UFO assignments."""
    values = {}
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ("MC", "MB", "aS"):
                fields = {kw.arg: kw.value for kw in node.value.keywords}
                if fields.get("value") is not None and isinstance(fields["value"], ast.Constant):
                    values[target.id] = fields["value"].value
    return values

def parse_cteq_header(text):
    lines = text.splitlines()
    if len(lines) < 5 or "Nfl" not in lines[1]:
        raise ValueError("CTEQ_HEADER_UNRECOGNIZED")
    values = [float(x) for x in lines[2].split()]
    if len(values) != 9:
        raise ValueError("CTEQ_HEADER_FIELD_COUNT")
    dimensions = [int(x) for x in lines[4].split()]
    return {"order_loops": int(values[0]), "maximum_flavours": int(values[1]),
            "lambda5_GeV": values[2], "quark_mass_parameters_GeV": dict(zip(
                ("down", "up", "strange", "charm", "bottom", "top"), values[3:])),
            "maximum_pdf_parton_flavour": dimensions[2]}

def _finite_positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("INVALID_" + name)

def validate_pdf_metadata(metadata, expected_nf):
    """Strict future acceptance; no global/default substitution for absent evidence."""
    required = ("set_name", "member", "lhaid", "grid_sha256", "info_sha256", "flavour_pdg_ids", "flavour_scheme",
                "num_flavours", "order_qcd", "alpha_s_mz", "alpha_s_order_qcd",
                "alpha_s_flavour_scheme", "alpha_s_num_flavours", "alpha_s_thresholds_GeV",
                "alpha_s_reference_scale_GeV", "alpha_s_type")
    if not isinstance(metadata, dict):
        raise ValueError("PDF_METADATA_OBJECT_REQUIRED")
    for name in ("num_flavours", "alpha_s_num_flavours"):
        value = metadata.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value != expected_nf):
            raise ValueError("PDF_ALPHA_FLAVOUR_COUNT_MISMATCH")
    for name in ("flavour_scheme", "alpha_s_flavour_scheme"):
        if metadata.get(name) is not None and metadata[name] not in ("fixed", "variable"):
            raise ValueError("UNREVIEWED_PDF_OR_ALPHA_FLAVOUR_SCHEME")
    for name in ("order_qcd", "alpha_s_order_qcd"):
        value = metadata.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value != 0):
            raise ValueError("LO_COMPONENT_REQUIRES_EXPLICIT_LO_PDF_ALPHA_REVIEW")
    if metadata.get("alpha_s_mz") is not None:
        _finite_positive(metadata["alpha_s_mz"], "ALPHA_S_MZ")
    missing = [name for name in required if metadata.get(name) is None]
    if missing:
        return ["PDF_METADATA_MISSING:" + name for name in missing]
    if not isinstance(metadata["set_name"], str) or not metadata["set_name"].strip():
        raise ValueError("INVALID_PDF_SET_NAME")
    if metadata["num_flavours"] != expected_nf or metadata["alpha_s_num_flavours"] != expected_nf:
        raise ValueError("PDF_ALPHA_FLAVOUR_COUNT_MISMATCH")
    if metadata["order_qcd"] != 0 or metadata["alpha_s_order_qcd"] != 0:
        raise ValueError("LO_COMPONENT_REQUIRES_EXPLICIT_LO_PDF_ALPHA_REVIEW")
    if isinstance(metadata["member"], bool) or not isinstance(metadata["member"], int) or metadata["member"] < 0:
        raise ValueError("INVALID_PDF_MEMBER")
    if isinstance(metadata["lhaid"], bool) or not isinstance(metadata["lhaid"], int) or metadata["lhaid"] <= 0:
        raise ValueError("INVALID_LHAID")
    if not re.fullmatch(r"[0-9a-f]{64}", metadata["grid_sha256"]):
        raise ValueError("INVALID_PDF_SHA256")
    _finite_positive(metadata["alpha_s_mz"], "ALPHA_S_REFERENCE_VALUE")
    _finite_positive(metadata["alpha_s_reference_scale_GeV"], "ALPHA_S_REFERENCE_SCALE")
    if metadata["alpha_s_type"] not in ("analytic", "ipol", "ode"):
        raise ValueError("UNREVIEWED_ALPHA_S_TYPE")
    if not isinstance(metadata["info_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", metadata["info_sha256"]):
        raise ValueError("INVALID_PDF_INFO_SHA256")
    if sorted(metadata["flavour_pdg_ids"]) != [-4, -3, -2, -1, 1, 2, 3, 4, 21]:
        raise ValueError("FOUR_FLAVOUR_PAYLOAD_PARTON_ID_MISMATCH")
    thresholds = metadata["alpha_s_thresholds_GeV"]
    if not isinstance(thresholds, dict) or thresholds.get("charm") is None:
        raise ValueError("MISSING_CHARM_THRESHOLD")
    _finite_positive(thresholds["charm"], "CHARM_THRESHOLD")
    # Maximum four active flavours means no bottom activation; charm may have a threshold.
    if expected_nf == 4 and thresholds.get("bottom_activation") is not None:
        raise ValueError("MAXIMUM_4F_HAS_NO_BOTTOM_ACTIVATION")
    return []

def validate_candidate(candidate):
    if candidate.get("execution_enabled") is not False or candidate.get("physical_approval") != "NOT_AUTHORIZED":
        raise ValueError("INACTIVE_SOURCE_ONLY_REQUIRED")
    if candidate.get("model") != "sm" or candidate.get("restriction") != "restrict_default.dat":
        raise ValueError("UNREVIEWED_MODEL_RESTRICTION")
    if candidate.get("bottom_mass_GeV") != 4.7 or candidate.get("charm_mass_GeV") != 0:
        raise ValueError("MODEL_MASS_IDENTITY_MISMATCH")
    if sorted(candidate.get("initial_pdg_ids", [])) != [-4, -3, -2, -1, 1, 2, 3, 4, 21]:
        raise ValueError("NOT_EXPLICIT_P4_INITIAL_STATE")
    if candidate.get("process") != "p4 p4 > b b~ a a QCD=2 QED=2":
        raise ValueError("UNREVIEWED_PROCESS")
    if candidate.get("matching_scale_GeV") is not None:
        raise ValueError("NO_UNREVIEWED_MATCHING_SCALE")
    if candidate.get("inclusive_background_total") is not False:
        raise ValueError("ISOLATED_COMPONENT_NOT_TOTAL_BACKGROUND")
    issues = validate_pdf_metadata(candidate["pdf"], 4)
    for field in ("photon_ir", "generation_cuts", "shower_settings", "scale_definition"):
        if candidate.get(field) is None:
            issues.append("UNRESOLVED_" + field.upper())
    return issues

# Stable public name for the root pilot-schema review.
validate_candidate_a = validate_candidate

def inventory_directory(path, purpose, max_depth=2):
    """Exhaustive inside an explicit bounded search root; no filesystem-wide claim."""
    path = Path(path)
    answer = {"path": str(path), "resolved_path": str(path.resolve()), "purpose": purpose,
              "exists": path.exists(), "maximum_depth": max_depth, "files": [],
              "untraversed_symlink_directories": [], "depth_limit_directories": []}
    if not path.exists():
        return answer
    def fail_inventory(error):
        raise error
    for base, dirs, files in os.walk(path, followlinks=False, onerror=fail_inventory):
        depth = len(Path(base).relative_to(path).parts)
        for name in sorted(dirs):
            child = Path(base) / name
            if child.is_symlink():
                answer["untraversed_symlink_directories"].append({"relative_path": str(child.relative_to(path)), "link_target": os.readlink(child), "target_exists": child.exists()})
            elif depth >= max_depth:
                answer["depth_limit_directories"].append(str(child.relative_to(path)))
        if depth >= max_depth:
            dirs[:] = []
        for name in sorted(files):
            p = Path(base) / name
            if p.is_symlink() and not p.exists():
                answer["files"].append({"relative_path": str(p.relative_to(path)), "status": "BROKEN_SYMLINK", "link_target": os.readlink(p), "resolved_path": str(p.resolve()), "bytes": None, "sha256": None, "null_reason": "target absent; no payload bytes available"})
            else:
                answer["files"].append({"relative_path": str(p.relative_to(path)), "status": "FILE", "link_target": os.readlink(p) if p.is_symlink() else None, "bytes": p.stat().st_size, "sha256": sha256(p)})
    answer["files"].sort(key=lambda item: item["relative_path"])
    return answer

def audit(mg5, pythia, env_prefix, candidate):
    mg5, pythia, env_prefix = Path(mg5), Path(pythia), Path(env_prefix)
    if "version = 3.5.16" not in (mg5 / "VERSION").read_text():
        raise ValueError("EXACT_MG5_VERSION_REQUIRED")
    before = {name: sha256(mg5 / name) for name in SOURCE_FILES}
    source = [source_record(mg5 / name, WITNESSES.get(name, ())) for name in SOURCE_FILES]
    blocks = parse_slha_blocks((mg5 / "models/sm/restrict_default.dat").read_text())
    comparison = {}
    for restriction in ("default", "no_b_mass", "c_mass"):
        data = parse_slha_blocks((mg5 / ("models/sm/restrict_" + restriction + ".dat")).read_text())
        comparison[restriction] = {"MC_GeV": float(data["MASS"][4]), "MB_GeV": float(data["MASS"][5]),
                                  "model_card_aS": float(data["SMINPUTS"][3])}
    if float(blocks["MASS"][4]) != candidate["charm_mass_GeV"] or float(blocks["MASS"][5]) != candidate["bottom_mass_GeV"]:
        raise ValueError("CANDIDATE_EFFECTIVE_MASS_DIFFERS_FROM_INSTALLED_SOURCE")
    roots = [
        (mg5 / "Template/LO/lib/Pdfdata", "actual MG5 built-in grid payloads", 0),
        (mg5 / "vendor/SudGen", "SudGen auxiliary directory; not an independent MG5 4F backend", 0),
        (pythia / "share/Pythia8/pdfdata", "Pythia internal grids; not assumed MG5-compatible", 0),
        (env_prefix / "share/LHAPDF", "installed LHAPDF configured data root", 2),
        (Path.home() / ".local/share/LHAPDF", "user-local conventional LHAPDF root", 2),
        (Path.home() / ".local/share/lhapdf", "lowercase conventional LHAPDF root", 2),
        (Path.home() / ".lhapdf", "user conventional LHAPDF root", 2),
        (Path("/usr/local/share/LHAPDF"), "system conventional LHAPDF root", 2),
        (Path("/usr/share/LHAPDF"), "system conventional LHAPDF root", 2),
        (mg5 / "HEPTools/lhapdf6/share/LHAPDF", "MG5 HEPTools conventional data root", 2),
    ]
    env_paths = {}
    for key in ("LHAPDF_DATA_PATH", "LHAPATH"):
        value = os.environ.get(key)
        env_paths[key] = value
        if value:
            roots.extend((Path(item), "configured " + key, 2) for item in value.split(":") if item)
    inventories = [inventory_directory(*item) for item in roots]
    extras = []
    for p in (env_prefix / "bin/lhapdf-config", env_prefix / "share/LHAPDF/lhapdf.conf",
              env_prefix / "share/LHAPDF/pdfsets.index", env_prefix / "include/LHAPDF/Version.h"):
        if p.is_file():
            extras.append(source_record(p, ("prefix=", "VERSION", "6.5.6", "--datadir", "CT14lo_NF4",
                                               "NNPDF30_lo_as_0130_nf_4", "AlphaS", "MCharm", "MBottom")))
    grid = parse_cteq_header((mg5 / "Template/LO/lib/Pdfdata/cteq6l1.tbl").read_text())
    pdf_infos = [entry for inv in inventories for entry in inv["files"] if entry["relative_path"].endswith(".info")]
    blockers = validate_candidate(candidate)
    if pdf_infos:
        blockers.append("UNREVIEWED_INSTALLED_LHAPDF_INFO_PRESENT")
    absent_cteq5f4 = not (mg5 / "Template/LO/lib/Pdfdata/cteq5f4.tbl").exists()
    if not absent_cteq5f4:
        blockers.append("NEW_CTEQ5F4_PAYLOAD_REQUIRES_INDEPENDENT_REVIEW")
    public_reference_path = Path(__file__).resolve().parents[1] / "config/public_pdf_metadata_reference.json"
    public_reference = json.loads(public_reference_path.read_text())
    if public_reference.get("evidence_class") != "PUBLIC_SOURCE_AUDIT" or public_reference.get("grid_downloaded") is not False:
        raise ValueError("PUBLIC_METADATA_SCOPE_CORRUPTED")
    public_reference["local_audit_record_sha256"] = sha256(public_reference_path)
    after = {name: sha256(mg5 / name) for name in SOURCE_FILES}
    if before != after:
        raise ValueError("INSTALLED_SOURCE_CHANGED_DURING_AUDIT")
    return {
        "schema_version": 1, "evidence_class": EVIDENCE_CLASS,
        "scope": "STATIC_TEXT_AND_GRID_IDENTITY_ONLY_NO_GENERATOR_IMPORT_OR_EXECUTION",
        "status": "BLOCKED_PHASE11_PDF_OR_ALPHA_S", "candidate": candidate,
        "model_restrictions": comparison,
        "unrestricted_ufo_parameter_defaults": ufo_external_defaults((mg5 / "models/sm/parameters.py").read_text()),
        "model_card_aS_is_selected_pdf_alpha_s": False,
        "pdf_inventories": inventories, "pdf_search_environment": env_paths,
        "inventory_scope_limit": "Explicit configured/conventional roots only; not a proof about every filesystem path or unconfigured archive",
        "compatible_installed_4f_pdf": None, "compatible_4f_pdf_member": None,
        "compatible_4f_lhaid": None, "compatible_4f_grid_sha256": None,
        "catalogued_cteq5f4": {"grid_filename": "cteq5f4.tbl", "grid_present_in_mg5_backend": not absent_cteq5f4,
                              "catalog_alpha_s_mz": 0.112, "catalog_running_loops": 2,
                              "selected": False, "backend_branch_active": False, "reason": "catalogue entry is not installed payload; cteq5f4 pdfwrap branch is commented out; NLO alpha source is not silently accepted for proposed LO definition"},
        "catalogued_future_4f_candidates": ["CT14lo_NF4", "NNPDF30_lo_as_0130_nf_4"],
        "future_4f_candidates_selected_or_downloaded": False,
        "builtin_cteq6l1_diagnostic_not_substitution": {
            "pdf_header": grid, "backend_alpha_s_mz": 0.130, "backend_running_loops": 1,
            "backend_alpha_s_threshold_defaults_GeV": {"charm": 1.42, "bottom": 4.7},
            "backend_alpha_s_maximum_flavours": 5,
            "threshold_identity": "NOT_IDENTICAL_PDF_1P3_4P5_VS_BACKEND_DEFAULT_1P42_4P7",
            "future_generated_effective_threshold_binding": None,
            "interpretation": "PDF evolution mass parameters, model pole masses and alpha_s matching thresholds are distinct; nonidentity is a review item, not alone a universal inconsistency theorem",
            "used_for_candidate_a": False},
        "future_lhapdf_alpha_binding": {"source_supported_interface": "ALPHAS(Q) -> alphasPDF(Q) -> active_member.alphasQ(Q)", "actual_4f_member_bound": False, "library_or_generator_executed": False},
        "precise_missing_requirement": (
            "Reviewed installed LO maximum-Nf=4/no-bottom proton PDF member payload plus .info/member metadata and SHA256, "
            "LHAID/member identity, alpha_s reference value AND reference scale/one-loop maximum-four-flavour evolution and threshold policy, "
            "a proven MG5 backend binding; no bottom-PDF activation; independent review of mass/scale/IR compatibility"),
        "blockers": blockers, "source_identity": source, "dependency_identity": extras,
        "primary_documentation": PRIMARY_SOURCES, "public_source_metadata_reference": public_reference, "source_hashes_unchanged": before == after,
        "new_MG5_parser_calls": 0, "new_ME_calls": 0, "new_integrals": 0, "new_hard_events": 0,
        "new_pythia_events": 0, "new_delphes_events": 0, "physical_pilot_executed": False,
        "independent_human_review": False,
    }
