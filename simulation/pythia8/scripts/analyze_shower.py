#!/usr/bin/env python3
"""Independently audit genuine raw Pythia diagnostics against immutable LHE and HepMC3 QA."""
from pathlib import Path
import json,math,hashlib,collections
import sys

repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'simulation/pythia8/scripts'))
from validate_lhe_stream import iter_lhe_events
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()
def flavour(pdg,q):
    pdg=abs(pdg)
    return pdg<1000000000 and q in ((pdg//10)%10,(pdg//100)%10,(pdg//1000)%10)
def photon_label(particles,index,roots):
    seen=set();stack=[index];hard=set();produced=False;decay=False;shower=False
    while stack:
        child=stack.pop()
        if child<=0 or child not in particles or child in seen:continue
        seen.add(child);p=particles[child]
        if child in roots:hard.add(child)
        if p['pdg_id']==22 and 41<=abs(p['status'])<60:shower=True
        for mother in p['mothers']:
            if mother<=0 or mother not in particles:continue
            m=particles[mother]
            is_produced=mother>2 and m['is_hadron'] and not 11<=abs(m['status'])<=19
            if is_produced:
                produced=True
                if p['pdg_id']==22 and 91<=abs(p['status'])<=94:decay=True
            stack.append(mother)
    if decay and shower:label='HADRON_DECAY_AND_SHOWER_ANCESTRY_AMBIGUOUS'
    elif decay:label='HADRON_DECAY_PHOTON_OR_DESCENDANT'
    elif produced and shower:label='SHOWER_WITH_PRODUCED_HADRON_ANCESTOR'
    elif produced:label='HADRON_ANCESTOR_AMBIGUOUS'
    elif index in roots:label='HARD_PROCESS_PHOTON'
    elif hard:label='HARD_PHOTON_ANCESTOR'
    elif shower:label='SHOWER_WITHOUT_HADRON_ANCESTOR'
    else:label='AMBIGUOUS'
    return label,hard
def audit(run):
    m=json.loads((run/'run_manifest.json').read_text());s=m['counters'];physical=m['physical_validation']
    assert m['status']=='PASS' and s['N_shower_failed']==0
    bins=[0,0.1,0.2,0.5,1,2,5,10,20,50,100,200,500,1000]
    pt_hist=collections.Counter();photon_origin=collections.Counter();photon_hist=collections.Counter()
    b_hist=collections.Counter();c_hist=collections.Counter();terminal_b=collections.Counter();terminal_c=collections.Counter()
    counts=collections.Counter();processed=0;max_hard_photon_shift=0.0
    hard_incoming=collections.Counter();hard_outgoing=collections.Counter();heavy_shower=collections.Counter();pair_candidates=collections.Counter()
    original=Path(m['source_file'])
    if not original.is_absolute():original=repo/original
    assert digest(original)==m['source_file_sha256']
    source_iter=(json.loads(row) for row in (run/'source_events.jsonl').open())
    original_iter=iter_lhe_events(original)
    for line in (run/'particle_diagnostics.jsonl').open():
        row=json.loads(line);source=next(source_iter);original_event=next(original_iter);processed+=1
        assert row['source_event_index']==source['source_event_index']==processed
        assert original_event['source_event_index']==processed and original_event['source_event_content_hash']==source['source_event_content_hash']
        assert original_event['nominal_generator_weight']==source['nominal_generator_weight']
        expected_particles=[]
        for raw in original_event['rows'][1:]:
            expected_particles.append({'pdg_id':int(raw[0]),'status':int(raw[1]),'mothers':[int(raw[2]),int(raw[3])],
              'colors':[int(raw[4]),int(raw[5])],'p4_and_mass_gev':[float(v.replace('D','E').replace('d','e')) for v in raw[6:11]]})
        assert source['particles']==expected_particles,'source sidecar differs from actual immutable LHE'
        particles={p['pythia_index']:p for p in row['particles']}
        assert set(particles)==set(range(1,len(particles)+1))
        outgoing={i:set() for i in particles};indegree={i:0 for i in particles}
        for i,p in particles.items():
            for mother in set(p['mothers'])-{0}:
                assert mother in particles,'dangling raw Pythia mother reference'
                outgoing[mother].add(i);indegree[i]+=1
        ready=collections.deque(i for i,n in indegree.items() if n==0);visited=0
        while ready:
            parent=ready.popleft();visited+=1
            for child in outgoing[parent]:
                indegree[child]-=1
                if indegree[child]==0:ready.append(child)
        assert visited==len(particles),'cycle in raw Pythia mother graph'
        recomputed={
          'isr_parton_record_entries':sum((p['pdg_id']==21 or abs(p['pdg_id'])<=6) and 41<=abs(p['status'])<50 for p in particles.values()),
          'fsr_parton_record_entries':sum((p['pdg_id']==21 or abs(p['pdg_id'])<=6) and 51<=abs(p['status'])<60 for p in particles.values()),
          'hadron_record_entries':sum(p['is_hadron'] for p in particles.values()),
          'decay_record_entries':sum(91<=abs(p['status'])<100 for p in particles.values())}
        assert all(row[k]==v for k,v in recomputed.items()),'status-defined shower/fragmentation/decay counter mismatch'
        for p in source['particles']:
            (hard_incoming if p['status']==-1 else hard_outgoing)[p['pdg_id']]+=1
        gluon_children=collections.defaultdict(set)
        for p in particles.values():
            if abs(p['pdg_id']) in {4,5} and 41<=abs(p['status'])<60:
                heavy_shower[p['pdg_id']]+=1
                for mother in p['mothers']:
                    if mother and particles[mother]['pdg_id']==21:gluon_children[mother].add(p['pdg_id'])
        for children in gluon_children.values():
            for q in [4,5]:
                if {q,-q}<=children:pair_candidates[q]+=1
        for p in particles.values():
            assert all(i==0 or i in particles for i in p['mothers']+p['daughters']),'dangling raw Pythia graph reference'
            assert p['pythia_index'] not in p['mothers']+p['daughters'],'raw Pythia self-link'
            for q,key in [(5,'terminal_b_hadron'),(4,'terminal_c_hadron')]:
                is_terminal=p['is_hadron'] and flavour(p['pdg_id'],q) and not any(
                  particles[i]['is_hadron'] and flavour(particles[i]['pdg_id'],q) for i in p['daughters'] if i>0)
                assert bool(p[key])==bool(is_terminal),'terminal heavy-hadron flag inconsistent with actual descendants'
        assert sum(p['terminal_b_hadron'] for p in particles.values())==row['terminal_b_hadron_count']
        assert sum(p['terminal_c_hadron'] for p in particles.values())==row['terminal_c_hadron_count']
        roots={i for i,p in particles.items() if p['pdg_id']==22 and abs(p['status'])==23}
        assert len(roots)==2 and roots==set(row['hard_photon_roots'])
        original_photons=[p['p4_and_mass_gev'][:4] for p in source['particles'] if p['pdg_id']==22 and p['status']==1]
        assert len(original_photons)==2
        mapped=[particles[i]['p4_gev'] for i in sorted(roots)]
        permutations=[(original_photons[0],original_photons[1]),(original_photons[1],original_photons[0])]
        # Minimal unordered p4 difference is a diagnostic, not a claimed
        # particle-barcode mapping or a requirement of unchanged kinematics.
        shift=min(max(abs(a-b) for op,pp in zip(order,mapped) for a,b in zip(op,pp)) for order in permutations)
        max_hard_photon_shift=max(max_hard_photon_shift,shift)
        final=[p for p in particles.values() if p['is_final']]
        assert len(final)==row['final_particle_count']
        charge=sum(p['charge_times_three'] for p in final)
        assert charge==6,('global full proton charge',processed,charge)
        photons=charged=neutral=neutrinos=light_stable=0
        for p in final:
            assert all(math.isfinite(v) for v in p['p4_gev'])
            if p['charge_times_three']:charged+=1
            else:neutral+=1
            if abs(p['pdg_id']) in {12,14,16}:neutrinos+=1
            else:
                pt=math.hypot(*p['p4_gev'][:2]);which=max(i for i,bound in enumerate(bins) if pt>=bound)
                pt_hist[str(bins[which])]+=1;counts['visible_particles']+=1
            if p['is_hadron'] and not flavour(p['pdg_id'],4) and not flavour(p['pdg_id'],5):light_stable+=1
            if p['pdg_id']==22:
                photons+=1;label,hard=photon_label(particles,p['pythia_index'],roots)
                assert label==p['photon_origin_diagnostic'] and hard==set(p['hard_photon_ancestors']),('photon origin',processed,p['pythia_index'])
                photon_origin[label]+=1
        assert charged==row['charged_final_count'] and photons==row['photon_final_count']
        counts.update(final=len(final),charged=charged,neutral=neutral,neutrinos=neutrinos,stable_light_hadrons=light_stable)
        b=sum(p['is_hadron'] and flavour(p['pdg_id'],5) for p in particles.values())
        c=sum(p['is_hadron'] and flavour(p['pdg_id'],4) for p in particles.values())
        b_hist[b]+=1;c_hist[c]+=1;photon_hist[photons]+=1
        terminal_b[row['terminal_b_hadron_count']]+=1;terminal_c[row['terminal_c_hadron_count']]+=1
        counts.update(allrecord_b=b,allrecord_c=c,isr_parton_records=row['isr_parton_record_entries'],
                      fsr_parton_records=row['fsr_parton_record_entries'],hadrons=row['hadron_record_entries'],decays=row['decay_record_entries'])
    assert processed==s['N_written']==physical['N_readback']
    assert math.isclose(counts['final'],physical['mean_final_multiplicity']*processed,rel_tol=0,abs_tol=1e-8)
    assert math.isclose(counts['charged'],physical['mean_charged_final_multiplicity']*processed,rel_tol=0,abs_tol=1e-8)
    assert {str(k):v for k,v in b_hist.items()}==physical['all_record_b_hadron_multiplicity_histogram']
    assert {str(k):v for k,v in c_hist.items()}==physical['all_record_c_hadron_multiplicity_histogram']
    assert counts['isr_parton_records']>0 and counts['fsr_parton_records']>0 and counts['hadrons']>0 and counts['decays']>0
    assert physical['stable_colored_particle_count']==0
    result={'status':'PASS','sample':m['source_sample_id'],'events':processed,'source_sha256':m['source_file_sha256'],
      'output_decompressed_sha256':m['files']['shower.hepmc3']['sha256'],
      'diagnostics_sha256':digest(run/'particle_diagnostics.jsonl'),'source_events_sha256':digest(run/'source_events.jsonl'),
      'raw_pythia_charge_and_multiplicity_crosscheck':'PASS vs independent HepMC3 stable records',
      'inclusive_heavy_hadron_crosscheck':'PASS: raw PDG quark digits vs independent installed ParticleData; B_c can appear in both',
      'photon_origin_crosscheck':'PASS: independent graph traversal excludes beams, includes hard self roots and preserves ambiguity',
      'counts':dict(counts),'means_per_event':{k:v/processed for k,v in counts.items()},
      'photon_origin_counts':dict(photon_origin),'photon_multiplicity_histogram':dict(photon_hist),
      'source_incoming_pdg_record_counts':dict(hard_incoming),'source_outgoing_pdg_record_counts':dict(hard_outgoing),
      'heavy_shower_pdg_record_counts_status_41_to_59':dict(heavy_shower),
      'gluon_parent_heavy_pair_ancestry_candidates':dict(pair_candidates),
      'heavy_pair_note':'Unique raw gluon-parent entries with both signed heavy-quark children in shower statuses41..59; ancestry diagnostic, not an exclusive splitting rate or mapping every hadron to hard flavour',
      'raw_mother_graph_acyclic':'PASS','status_defined_development_counts':'PASS independently recomputed from every raw record',
      'allrecord_b_hadron_histogram':dict(b_hist),'allrecord_c_hadron_histogram':dict(c_hist),
      'terminal_b_hadron_histogram':dict(terminal_b),'terminal_c_hadron_histogram':dict(terminal_c),
      'stable_visible_pt_histogram':{'unit':'GeV','bins_lower_edges':bins,'last_bin':'1000 GeV and above','counts':dict(pt_hist),'inputs':'all stable particles except neutrinos12/14/16; no detector reconstruction'},
      'max_unordered_lhe_to_pythia_hard_photon_p4_component_difference_gev':max_hard_photon_shift,
      'hard_momentum_note':'Original LHE p4 remain immutable in source sidecar; Pythia heavy-mass restoration/recoil may change hard-record momenta; no unchanged-kinematics or barcode equivalence claimed',
      'processing_seconds':s['elapsed_seconds'],'full_cli_seconds':m['elapsed_seconds'],
      'peak_rss_bytes':m['peak_rss_bytes'],'ascii_bytes':m['files']['shower.hepmc3']['bytes'],
      'gzip_bytes':m['files']['shower.hepmc3.gz']['bytes'],'ascii_bytes_per_event':m['files']['shower.hepmc3']['bytes']/processed,
      'gzip_bytes_per_event':m['files']['shower.hepmc3.gz']['bytes']/processed}
    return result
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();result=audit(args.run);args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({key:result[key] for key in ['status','sample','events','photon_origin_counts','means_per_event','max_unordered_lhe_to_pythia_hard_photon_p4_component_difference_gev']},indent=2))
