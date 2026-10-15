"""Independent portable checks of the actual bounded Phase7E evidence."""
import math
from .audit import *
from simulation.hh_signal.campaign.lhe import load_lhe

def alpha_nf5(q,loops):
    require(q>4.7 and loops in [1,2],'OUTSIDE_INDEPENDENT_ALPHA_SCOPE')
    a0=.13;b0=(23/3)/(2*math.pi);c=(116/3)/(4*math.pi*(23/3))
    if loops==1:return 1/(1/a0+b0*math.log(q/91.188))
    def f(a):return 1/a+c*math.log(a/(1+c*a))
    target=f(a0)+b0*math.log(q/91.188);lo=.001;hi=.5
    for _ in range(80):
        mid=(lo+hi)/2
        if f(mid)>target:lo=mid
        else:hi=mid
    return (lo+hi)/2

def validate():
    manifest=read(EVIDENCE/'manifest.json')
    require({p.relative_to(EVIDENCE).as_posix() for p in EVIDENCE.rglob('*') if p.is_file()}=={r['path'] for r in manifest['files']}|{'manifest.json'},'EVIDENCE_FILE_SET')
    for row in manifest['files']:
        path=Path(row['path'])
        require(not path.is_absolute() and '..' not in path.parts and (EVIDENCE/path).resolve().is_relative_to(EVIDENCE.resolve()) and sha(EVIDENCE/path)==row['sha256'] and
            (EVIDENCE/row['path']).stat().st_size==row['bytes'],'EVIDENCE_HASH')
    result=read(EVIDENCE/'source_audit.json')
    identity=read(EVIDENCE/'physics_source_identity.json')
    require(identity['process_commands_equal'] and identity['compared']==84 and identity['all_equal'] and
        all(r['B']==r['C'] and r['same'] for r in identity['frozen_Fortran_files']),'FROZEN_LOOP_SOURCE_IDENTITY')
    for phase,pdf,status in [('7b','cteq6l1','PASS'),('7c','nn23lo1','FAIL_EFFECTIVE_PDF_MISMATCH')]:
        p=result['phases'][phase];inc=include_values((EVIDENCE/(phase+'_native_include.inc')).read_text())
        require(inc['pdlabel']==pdf and p['PDF_consistency']['status']==status,'EFFECTIVE_PDF_REGRESSION')
        for channel,retained in p['native_survey_and_refine'].items():
            actual=log_diagnostics((EVIDENCE/(phase+'_'+channel+'_numeric.log')).read_text())
            require(all(actual[k]==retained[k] for k in actual),'NATIVE_NUMERIC_LOG_REGRESSION')
    alpha=read(EVIDENCE/'alpha_running_audit.json');residuals={}
    for phase,n,loops in [('7b',100,1),('7c',1000,2)]:
        source=load_lhe(REPO/'reference_samples/hh_signal/S01_ggf_hh_sm'/('phase7b_100' if n==100 else 'phase7c_1000')/f'reference_{n}.lhe.gz')
        path=REPO/'reference_samples/hh_signal/S01_ggf_hh_sm'/('phase7b_100' if n==100 else 'phase7c_1000')/f'reference_{n}.lhe.gz'
        require(sha(path)==result['phases'][phase]['source_LHE_sha256'],'ORIGINAL_LHE_BINDING')
        worst=max(abs(alpha_nf5(r['scale'],loops)-r['alpha_qcd'])/r['alpha_qcd'] for r in source['records'])
        # ALPS has seven significant native digits; scale is likewise rounded.
        require(worst<1e-6,'INDEPENDENT_ALPHA_RUNNING_ORDER_MISMATCH');residuals[phase]=worst
        measured=next(r for r in alpha['results'] if r['phase']==phase)
        require(measured['native_running_order_matching_all_retained_ALPS']==loops and measured['retained_source_events']==n,'NATIVE_ALPHA_PROOF_SCOPE')
    require(alpha['probe_source_sha256']==sha(HERE/'src/retained_alpha_probe.f90'),'NATIVE_PROBE_SOURCE_CHANGED')
    support=read(EVIDENCE/'kappa_support.json')
    # Recompute from all original ME rows and the preserved full1000 selection
    # mask, rather than treating previously printed ESS values as a test.
    selected=read(EVIDENCE/'selection_mask.json')
    require(len(selected['cut_mgg'])==1000,'FULL_SELECTION_MASK_COUNT')
    original=read(REPO/'metadata/phase7c_run_manifest.json')
    require(selected['source_reco_sha256']==original['stages']['full1000']['artifacts']['reco']['sha256'] and
        all(isinstance(v,bool) for v in selected['cut_mgg']) and sum(selected['cut_mgg'])==143,'ORIGINAL_SELECTION_MASK_BINDING')
    source=load_lhe(REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7c_1000/reference_1000.lhe.gz')
    calculated=weighted_support(REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv',
        {i+1:value for i,value in enumerate(selected['cut_mgg'])},source['records'])
    require(calculated==support,'INDEPENDENT_ALL_ROW_SUPPORT_RECOMPUTATION')
    for k,ess,final in [('2.5',36.6942995242142,16.07357051564675),('5',19.544222688333267,7.65012406875469)]:
        require(abs(support[k]['input_ESS']-ess)<1e-8 and abs(support[k]['final_ESS']-final)<1e-8 and
            support[k]['status']=='INCONCLUSIVE_REWEIGHTING','KAPPA_SUPPORT_REGRESSION')
    return {'status':'PASS_PORTABLE_AUDIT_REGRESSION_WITH_EXPECTED_SCIENTIFIC_FAILURES',
        'C_effective_PDF_gate':'FAIL','native_and_independent_alpha_running_match':residuals,
        'independent_integration_status':'NOT_AUTHORIZED','new_integrals':0,'new_physical_events':0}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
