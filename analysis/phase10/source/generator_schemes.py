"""Offline checks for Phase10 source-review artifacts; never dispatches generators."""
from __future__ import annotations

import math
import re
from pathlib import Path

BASE_REVISION = "ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a"
VERDICTS = {"SUPPORTED_CANDIDATE", "METHOD_ONLY", "UNVERIFIED", "INAPPLICABLE"}
REQUIRED_SCHEME_FIELDS = (
    "id", "scheme", "physics_definition", "software_support", "source_evidence",
    "expected_advantages", "known_weaknesses", "required_validation",
    "unresolved_assumptions", "scientific_verdict", "flavour_scheme",
    "initial_heavy_flavour", "final_heavy_flavour", "shower_gsplit",
    "photon_ir_isolation", "scale_pdf_alpha_s", "weight_conventions",
    "matching_jet_multiplicities", "flavour_jet_ir_definition",
)
REQUIRED_BLOCKERS = {
    "EXACT_PROCESS_MATCHING_NOT_VALIDATED", "PDF_ALPHA_S_NOT_FROZEN",
    "PHOTON_IR_ISOLATION_NOT_FROZEN", "FLAVOUR_JET_DEFINITION_NOT_FROZEN",
    "EXACT_SOURCE_APPROVAL_ABSENT", "FINITE_RESOURCE_ENVELOPE_NOT_APPROVED",
    "PRODUCTION_ENFORCEMENT_NOT_REVIEWED",
}
COUNTER_KEYS = (
    "new_me_calls", "new_integrals", "new_hard_events", "new_pythia_events",
    "new_delphes_events",
)
PENDING_PARAMETER_KEYS = (
    "xqcut_gev", "qcut_gev", "merging_tms_gev", "fxfx_qcut_me_gev",
)


def validate_scheme_review(review: dict) -> list[str]:
    """Return structural/scientific errors; an unvalidated matrix is valid evidence."""
    errors = []
    if review.get("base_revision") != BASE_REVISION:
        errors.append("BASE_REVISION_MISMATCH")
    if review.get("evidence_class") != "PUBLIC_SOURCE_AUDIT":
        errors.append("SCHEME_EVIDENCE_CLASS_MISMATCH")
    schemes = review.get("schemes", [])
    if not isinstance(schemes, list) or len(schemes) < 3:
        return errors + ["MISSING_SCHEME_COMPARISON"]
    identifiers = set()
    references = {x.get("id") for x in review.get("references", [])}
    for scheme in schemes:
        sid = scheme.get("id")
        if sid in identifiers:
            errors.append("DUPLICATE_SCHEME_ID")
        identifiers.add(sid)
        for field in REQUIRED_SCHEME_FIELDS:
            if field not in scheme or scheme[field] in ("", [], None):
                errors.append(f"{sid}:MISSING_{field}")
        if scheme.get("scientific_verdict") not in VERDICTS:
            errors.append(f"{sid}:INVALID_VERDICT")
        if not set(scheme.get("source_evidence", [])).issubset(references):
            errors.append(f"{sid}:UNKNOWN_SOURCE")
        # Merely finding a generic interface cannot certify the exact process.
        if scheme.get("exact_process_validated") is not False:
            errors.append(f"{sid}:UNSUPPORTED_EXACT_PROCESS_VALIDATION")
        if scheme.get("scientific_verdict") == "SUPPORTED_CANDIDATE":
            errors.append(f"{sid}:CANDIDATE_SUPPORT_NOT_ESTABLISHED_IN_THIS_REVIEW")
    if review.get("matching_prescription_status") != "NO_VALIDATED_MATCHING_PRESCRIPTION_YET":
        errors.append("UNSUPPORTED_MATCHING_PRESCRIPTION")
    if review.get("recommended_matching_candidate") is not None:
        errors.append("UNSUPPORTED_MATCHING_RECOMMENDATION")
    if review.get("external_independent_human_approval") is not None:
        errors.append("HUMAN_APPROVAL_NOT_OBSERVED")
    if not review.get("local_source_audit"):
        errors.append("MISSING_LOCAL_SOURCE_AUDIT")
    for src in review.get("local_source_audit", []):
        if not re.fullmatch(r"[0-9a-f]{64}", str(src.get("sha256", ""))):
            errors.append("INVALID_LOCAL_SOURCE_HASH")
    return errors


def inactive_card_errors(text: str, filename: str) -> list[str]:
    """The entire proposal must be comments, including process syntax examples."""
    if not filename.endswith(".inactive.txt"):
        return ["ACTIVE_CARD_EXTENSION"]
    if "FUTURE_UNEXECUTED_PROPOSAL" not in text or "DO_NOT_EXECUTE" not in text:
        return ["CARD_INACTIVE_LABEL_MISSING"]
    if any(line.strip() and not line.lstrip().startswith(("#", "!"))
           for line in text.splitlines()):
        return ["ACTIVE_CARD_CONTENT"]
    return []


def validate_pilot_contract(contract: dict, review: dict, root: Path | None = None) -> dict:
    """Validate an explicitly noninstantiable proposal, never authorize production."""
    errors = validate_scheme_review(review)
    if contract.get("base_revision") != BASE_REVISION:
        errors.append("BASE_REVISION_MISMATCH")
    if contract.get("evidence_class") != "FUTURE_UNEXECUTED_PROPOSAL":
        errors.append("PILOT_EVIDENCE_CLASS_MISMATCH")
    if contract.get("status") != "PREPARED_INACTIVE_BLOCKED":
        errors.append("ACTIVE_PILOT_STATUS")
    if contract.get("instantiable") is not False or contract.get("execution_authorized") is not False:
        errors.append("PHYSICAL_PRODUCTION_FORBIDDEN")
    if contract.get("physical_pilot_executed") is not False:
        errors.append("FABRICATED_PILOT_EXECUTION")
    if contract.get("dispatcher") is not None:
        errors.append("GENERATOR_DISPATCHER_FORBIDDEN")
    counters = contract.get("actual_new_production", {})
    if set(counters) != set(COUNTER_KEYS) or any(type(counters.get(k)) is not int or counters[k] != 0
                                              for k in COUNTER_KEYS):
        errors.append("NONZERO_OR_MISSING_PHYSICAL_COUNTERS")
    if contract.get("exact_source_approval_receipt") is not None:
        errors.append("EXACT_SOURCE_APPROVAL_NOT_OBSERVED")
    if contract.get("independent_human_review_receipt") is not None:
        errors.append("HUMAN_APPROVAL_NOT_OBSERVED")
    blockers = set(contract.get("blockers", []))
    if not REQUIRED_BLOCKERS.issubset(blockers):
        errors.append("MISSING_PHYSICAL_BLOCKERS")
    matching = contract.get("matching", {})
    if matching.get("validated") is not False:
        errors.append("INVALID_MATCHING_ASSUMPTION")
    if any(matching.get(k) is not None for k in PENDING_PARAMETER_KEYS):
        errors.append("UNVALIDATED_NUMERIC_MERGING_SCALE")
    if matching.get("selected_scheme") is not None:
        errors.append("UNVALIDATED_SELECTED_MATCHING_SCHEME")
    scan = matching.get("future_scan_protocol", {})
    if scan.get("numeric_scale_grid_gev") is not None or scan.get("approval_required") is not True:
        errors.append("SCAN_REQUIRES_SEPARATE_EXACT_SOURCE_APPROVAL")
    for field in ("pdf", "alpha_s", "photon_cuts", "photon_isolation", "hard_scale",
                  "mass_flavour_scheme", "shower", "weight_contract"):
        if contract.get(field, {}).get("frozen") is not False:
            errors.append(f"UNVERIFIED_FROZEN_{field.upper()}")
    envelope = contract.get("resource_planning", {})
    if envelope.get("approved") is not False or envelope.get("actual_pilot_measurement") is not False:
        errors.append("RESOURCE_APPROVAL_NOT_OBSERVED")
    ceilings = envelope.get("illustrative_ceiling", {})
    for field in ("cpu_threads", "wall_seconds", "ram_bytes", "disk_bytes", "total_new_hard_events",
                  "max_scan_points", "max_me_evaluations", "max_integration_cycles",
                  "max_event_trials"):
        value = ceilings.get(field)
        if type(value) is not int or value <= 0 or not math.isfinite(value):
            errors.append(f"NONFINITE_RESOURCE_{field.upper()}")
    if envelope.get("enforcement_reviewed") is not False:
        errors.append("RESOURCE_ENFORCEMENT_NOT_REVIEWED")
    if contract.get("output_scope", {}).get("physical_total_background") != "BLOCKED":
        errors.append("PHYSICAL_TOTAL_BACKGROUND_NOT_BLOCKED")
    if contract.get("output_scope", {}).get("future_output_directory") is not None:
        errors.append("UNAPPROVED_FUTURE_OUTPUT_DIRECTORY")
    if contract.get("precision_objectives", {}).get("guaranteed_precision") is not False:
        errors.append("UNSUPPORTED_PRECISION_GUARANTEE")
    cards = contract.get("inactive_cards", [])
    if not cards:
        errors.append("MISSING_INACTIVE_CARDS")
    for card in cards:
        path = card.get("path", "")
        if not path.startswith("analysis/phase10/config/cards/"):
            errors.append("CARD_OUTSIDE_PHASE10")
            continue
        if not path.endswith(".inactive.txt"):
            errors.append("ACTIVE_CARD_EXTENSION")
            continue
        if root is not None:
            resolved = (root / path).resolve()
            if not resolved.is_relative_to(root.resolve()):
                errors.append("CARD_PATH_ESCAPE")
            elif not resolved.is_file():
                errors.append("MISSING_INACTIVE_CARD")
            else:
                errors.extend(inactive_card_errors(resolved.read_text(), path))
    return {
        "schema_version": 1,
        "valid_inactive_contract": not errors,
        "errors": sorted(set(errors)),
        "scientific_status": "NO_VALIDATED_MATCHING_PRESCRIPTION_YET",
        "execution_authorized": False,
        "instantiable": False,
        "blocking_conditions": sorted(blockers),
        "scope": "OFFLINE_SOURCE_CONTRACT_VALIDATION_ONLY",
    }
