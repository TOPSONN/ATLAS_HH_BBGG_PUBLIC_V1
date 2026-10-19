#!/usr/bin/env python3
"""Fail-closed physical-readiness ledger; reuses Phase8 fit policy and never fits data."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

PHASE8_REVISION = '8ecd91106acb1dae065cde14f1d62867d10b073f'

REQUIRED_GATES = (
 'SIGNAL_MATCHED_NORMALIZATION','HEAVY_FLAVOUR_BACKGROUND_EXCLUSIVITY',
 'FAKE_PHOTON_ESTIMATION','SINGLE_HIGGS_MODELING','DETECTOR_CALIBRATION',
 'SYSTEMATIC_NUISANCE_VALUES','NUISANCE_CORRELATIONS','MC_BIN_STATISTICAL_SUPPORT',
 'SIGNED_EXPECTATION_MODEL_IF_APPLICABLE')


def demand(ok,reason):
    if not ok: raise ValueError(reason)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def csvrows(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))


def validate_readiness_gates(gates):
    """Missing is never inferred as PASS/zero; signed inputs need an explicit model."""
    demand(set(gates)==set(REQUIRED_GATES),'MISSING_OR_UNKNOWN_PHYSICAL_GATE')
    for name,gate in gates.items():
        demand(gate.get('status') in ('PASS_CURRENT_INPUTS_ONLY','BLOCKED','UNKNOWN'),'INVALID_GATE_STATUS:'+name)
        demand(isinstance(gate.get('reason'),str) and bool(gate['reason']),'MISSING_GATE_REASON:'+name)
        demand(isinstance(gate.get('evidence'),list) and bool(gate['evidence']),'MISSING_GATE_EVIDENCE:'+name)
        if gate['status']!='PASS_CURRENT_INPUTS_ONLY':
            demand(gate.get('physical_numerical_value') is None,'MISSING_INPUT_BECAME_ZERO_OR_TOY_VALUE:'+name)
    return [name for name,gate in gates.items() if gate['status']!='PASS_CURRENT_INPUTS_ONLY']


def assemble(review,signal_identity,nuisance_rows,negative_events,evidence):
    demand(review.get('status')=='PASS_INDEPENDENT_SCIENCE_REVIEW_WITH_PHYSICAL_BLOCKERS','INDEPENDENT_REVIEW_NOT_PASSED')
    demand(review.get('reviewed_source_revision')==PHASE8_REVISION,'INDEPENDENT_REVIEW_WRONG_SOURCE_REVISION')
    demand(signal_identity['B_effective_PDF']=='cteq6l1' and signal_identity['B_effective_running_loops']==1,'UNEXPECTED_B_EFFECTIVE_IDENTITY')
    demand(signal_identity['C_effective_PDF']=='NNPDF23_lo_as_0130_qed_mem0' and signal_identity['C_effective_running_loops']==2,'UNEXPECTED_C_EFFECTIVE_IDENTITY')
    demand(isinstance(negative_events,int) and not isinstance(negative_events,bool) and negative_events>=0,'INVALID_NEGATIVE_SOURCE_COUNT')
    demand(len(nuisance_rows)==22,'SYSTEMATICS_INVENTORY_NOT_22')
    demand(all(row.get('physical_value') in (None,'') and row.get('correlation_model') in (None,'') for row in nuisance_rows),'UNREVIEWED_PHYSICAL_NUISANCE_SUBSTITUTION')
    def gate(status,reason,refs,future):
        return dict(status=status,reason=reason,evidence=refs,physical_numerical_value=None,future_requirement=future)
    gates={
     'SIGNAL_MATCHED_NORMALIZATION':gate('BLOCKED','B100 and C1000 have different effective PDF/alpha_s running. C1000 is not the declared future CTEQ6L1 one-loop target; matched integration/convergence and its physical rate uncertainty remain unavailable.',['PHASE8_SOURCE/metadata/phase7e_audit.json'],'Separately authorized corrected matched integration, independently validated cross section/error, corrected event chain, immutable new source identities; do not rescale or replace historical events silently.'),
     'HEAVY_FLAVOUR_BACKGROUND_EXCLUSIVITY':gate('BLOCKED','B01/B02/B03 reconstructed phase-space sharing or ancestry labels do not establish perturbative ME/PS exclusivity.',['PHASE8_LOCAL/phase8_background_overlap_matrix.json'],'Matched/merged generation or a validated generator-level exclusive definition, with uncertainty and source-level closure.'),
     'FAKE_PHOTON_ESTIMATION':gate('BLOCKED','B06 contains one Born photon and zero final survivors; neither is a calibrated jet-to-photon fake estimate. Missing fake rate is null, not zero.',['PHASE8_LOCAL/phase8_fake_photon_readiness.json'],'Applicable public/data-derived fake transfer factor with object/period/energy/region definitions, composition, contamination, uncertainty, correlations and closure.'),
     'SINGLE_HIGGS_MODELING':gate('BLOCKED','ZH and ttH have correctly applied own MODEL_BR_ONLY factors; physical normalization, top-decay/spin assumptions and modeling uncertainties are not fully validated.',['PHASE8_LOCAL/phase8_weight_accounting.csv','PHASE8_LOCAL/phase8_background_overlap_matrix.json'],'Review process/decay/BR convention and single-Higgs normalization, topology, spin correlations, generator/PS systematics.'),
     'DETECTOR_CALIBRATION':gate('BLOCKED','Native Delphes bit0/kinematics closure validates this fast-simulation implementation; it does not supply official detector object efficiencies, scales, resolution, trigger or pileup calibrations.',['PHASE8_SOURCE/analysis/phase8/config/selection_v1.json','PHASE8_LOCAL/phase8_systematics_readiness.csv'],'Compatible detector/object calibrations and independently established selection applicability.'),
     'SYSTEMATIC_NUISANCE_VALUES':gate('UNKNOWN','All 22 physical nuisance values/constraints are unavailable; synthetic widths are method inputs only.',['PHASE8_LOCAL/phase8_systematics_readiness.csv'],'Traceable process/object/rate/shape physical values, units, constraints and validation.'),
     'NUISANCE_CORRELATIONS':gate('UNKNOWN','No validated physical nuisance correlation model across processes, objects, bins or data periods. Common-source kappa statistical covariance does not replace systematic correlations.',['PHASE8_LOCAL/phase8_systematics_readiness.csv','PHASE8_LOCAL/phase8_kappa_covariance.csv'],'Reviewed correlation matrix/model with provenance, PSD/constraint and likelihood closure checks.'),
     'MC_BIN_STATISTICAL_SUPPORT':gate('BLOCKED','B02 final 1/1000, B03/B06 final 0/1000 and empty/low-ESS bins prevent reliable finely binned physical templates; kappa 2.5/5 remain under-supported.',['PHASE8_LOCAL/phase8_cutflow_raw.csv','PHASE8_LOCAL/phase8_bin_quality.csv','PHASE8_LOCAL/phase8_kappa_summary.csv'],'Predeclared bins with sufficient independent proposal support, rare-event interval/planning diagnostics, validated finite-MC likelihood and independent source checks.'),
     'SIGNED_EXPECTATION_MODEL_IF_APPLICABLE':gate('BLOCKED' if negative_events else 'PASS_CURRENT_INPUTS_ONLY','Negative-weight inputs require an explicit generative signed-expectation treatment and valid nonnegative total rates; never clip bins.' if negative_events else 'The present raw source cohorts have0 negative-weight events. Phase8 rejects unsupported signed physical templates. This conditional check does not establish support for future signed inputs.',['PHASE8_LOCAL/phase8_cutflow_weighted.csv','PHASE8_SOURCE/analysis/phase8/src/Phase8Likelihood.cxx'],'If future negative contributions occur, validate a signed estimator/expectation model; reject unsupported rates, retain signs, and never replace negatives with zero.')}
    blockers=validate_readiness_gates(gates)
    return {'schema_version':1,'task':'PHASE9G_PHYSICAL_LIKELIHOOD_READINESS','base_Phase8_revision':PHASE8_REVISION,'evidence_class':'HISTORICAL_EVIDENCE_AUDIT','status':'BLOCKED_PHYSICAL_INFERENCE_REQUIRED_INPUTS_MISSING','gates':gates,'blocking_or_unknown_gates':blockers,'negative_source_events':negative_events,'missing_gate_is_zero':False,'synthetic_fit_can_unlock_physical_inference':False,'likelihood_framework':'REUSE_VALIDATED_PHASE8_ROOT_ROOFIT_ROOSTATS; no new physical fit','method_fits':'SYNTHETIC_METHOD_ONLY','PHYSICAL_TOTAL_BACKGROUND':'BLOCKED','PHYSICAL_SIGNIFICANCE':'NOT_EVALUATED','PHYSICAL_CLs':'NOT_EVALUATED','PHYSICAL_KAPPA_INTERVAL':'NOT_EVALUATED','physical_nuisance_values':None,'physical_nuisance_correlations':None,'new_ME_calls':0,'new_integrals':0,'new_events':0,'Phase7I_dependency':'TRACKED_ONLY_NO_BUILD_OR_RESTART; future corrected matched integration and event chain require separate authorization','evidence':evidence}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--phase8-results',required=True,type=Path);p.add_argument('--review',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    demand(not a.output.exists(),'READINESS_OUTPUT_MUST_BE_FRESH')
    evidence={}
    sources={'PHASE8_SOURCE/metadata/phase7e_audit.json':a.source/'metadata/phase7e_audit.json','PHASE8_SOURCE/analysis/phase8/config/selection_v1.json':a.source/'analysis/phase8/config/selection_v1.json','PHASE8_SOURCE/analysis/phase8/src/Phase8Likelihood.cxx':a.source/'analysis/phase8/src/Phase8Likelihood.cxx'}
    for n in ('phase8_background_overlap_matrix.json','phase8_fake_photon_readiness.json','phase8_weight_accounting.csv','phase8_systematics_readiness.csv','phase8_kappa_covariance.csv','phase8_cutflow_raw.csv','phase8_bin_quality.csv','phase8_kappa_summary.csv','phase8_cutflow_weighted.csv'):
        sources['PHASE8_LOCAL/'+n]=a.phase8_results/n
    for logical,path in sources.items(): evidence[logical]={'sha256':sha(path),'bytes':path.stat().st_size}
    result=assemble(load(a.review),load(a.source/'metadata/phase7e_audit.json'),csvrows(a.phase8_results/'phase8_systematics_readiness.csv'),sum(int(row['N_negative']) for row in csvrows(a.phase8_results/'phase8_cutflow_weighted.csv') if row['stage']=='INPUT'),evidence)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');print(json.dumps({'status':result['status'],'missing_gates':len(result['blocking_or_unknown_gates'])}));return 0

if __name__=='__main__':raise SystemExit(main())