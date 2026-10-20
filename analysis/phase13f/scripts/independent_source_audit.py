#!/usr/bin/env python3
"""Independent stdlib-only AST/Git audit; does not import envelope/worker code.
This is an independently implemented source check, not external human review.
"""
import argparse,ast,hashlib,json,subprocess
from pathlib import Path
BASE='aa6eb8c9abdcc4d177af2e84296180624faf835a'
EXPECTED_CASES=['normal']+[a+'_'+b for a in ('preflight','child','receipt','postflight') for b in ('cpu','ram','wall','disk','abnormal')]+['aggregate_cpu','orphan','controller_loss','pids','source_write','cgroup_write','namespace_escape','stdout_overflow','disk_inodes','legacy_missing_approval']
def demand(ok,reason):
 if not ok:raise ValueError(reason)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def inspect(repo,evidence=None):
 repo=Path(repo);profile=json.loads((repo/'analysis/phase13f/config/full_job_profile.json').read_text());checks=[]
 def check(ok,label):demand(ok,label);checks.append(label)
 spec={'aggregate_CPU_seconds':4,'aggregate_wall_seconds':13,'unit_start_seconds':2,'unit_run_seconds':10,'unit_stop_seconds':0.1,'cpu_quota_percent':30,'cpu_quota_period_usec':10000,'CPU_watchdog_stop_usec':2500000,'aggregate_memory_bytes':536870912,'swap_bytes':0,'per_process_address_space_bytes':536870912,'per_process_CPU_seconds':2,'tmpfs_bytes':8388608,'tmpfs_inodes':1024,'per_regular_file_bytes':65536,'host_log_files':2,'host_metadata_bytes':65536,'host_metadata_files':4,'aggregate_disk_bytes':9437184,'max_tasks':8,'full_parser_execution_authorized':False,'MG5_invocations':0,'new_ME_calls':0,'new_integrals':0,'new_events':0}
 for k,v in spec.items():check(profile.get(k)==v and type(profile.get(k)) is type(v),'EXACT_PROFILE_'+k)
 # A conservative coupled CPU bound includes start/runtime/stop and one full
 # quota period; observed kernel timer/cleanup latency is separately reported.
 nominal=(2+10+.1)*.30+.003
 check(nominal<4,'QUOTA_PLUS_WALL_CPU_RESERVE')
 disk=8388608+2*65536+4*65536+64
 check(disk<9437184,'TMPFS_PLUS_FIXED_EXPORT_DISK_RESERVE')
 sources=sorted((repo/'analysis/phase13f/source').glob('*.py'))+sorted((repo/'analysis/phase13f/scripts').glob('*.py'))
 for path in sources:
  tree=ast.parse(path.read_text());check(path.stat().st_size<=65536,'SOURCE_SIZE_'+path.name)
  for node in ast.walk(tree):
   if isinstance(node,(ast.Import,ast.ImportFrom)):
    names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
    check(not any(n.startswith(('madgraph','models','pythia','Delphes')) for n in names),'NO_PHYSICS_IMPORT_'+path.name+'_'+str(node.lineno))
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):check(node.func.id not in ('eval','exec','compile'),'NO_DYNAMIC_EXEC_'+path.name+'_'+str(node.lineno))
 text=(repo/'analysis/phase13f/source/envelope.py').read_text();worker=(repo/'analysis/phase13f/source/workflow.py').read_text()
 for token in ('ProtectSystem=strict','ProtectHome=read-only','ProtectControlGroups=yes','PrivateUsers=yes','PrivateNetwork=yes','PrivateIPC=yes','RestrictNamespaces=yes','NoNewPrivileges=yes','CapabilityBoundingSet=','OOMPolicy=kill','CPUQuota=30%','CPUQuotaPeriodSec=10ms','RuntimeMaxSec=10s','TimeoutStartSec=2s','TimeoutStopSec=100ms','KillMode=control-group','KillSignal=SIGKILL','LimitCPU=2','LimitAS=536870912','LimitFSIZE=65536','TasksMax=8','MemorySwapMax=0','size=8388608,nr_inodes=1024,nodev,nosuid,noexec'):
  check(token in text,'REQUIRED_PROPERTY_'+token)
 et=ast.parse(text);rf=next(n for n in et.body if isinstance(n,ast.FunctionDef) and n.name=='run_case')
 loops=[n for n in ast.walk(rf) if isinstance(n,ast.While) and n.body and isinstance(n.body[0],ast.Assign) and any(isinstance(t,ast.Name) and t.id=='last' for t in n.body[0].targets)]
 check(len(loops)==1 and any(isinstance(n,ast.If) and 'SubState' in ast.unparse(n.test) for n in loops[0].body),'OBSERVER_COMPLETION_BRANCH_REACHABLE')
 check('ReadWritePaths=' not in text,'NO_HOST_BIND_OVER_TMPFS')
 check('StandardOutput=file:' in text and 'StandardError=file:' in text,'BOUNDED_REGULAR_EXPORTS_NOT_JOURNAL')
 check("'cgroup.kill').write_text('1')" in text or "(cgroup/'cgroup.kill').write_text('1')" in text,'WHOLE_CGROUP_KILL')
 check("facts['memory.oom.group']=='1'" in worker and "facts['work_capacity_bytes']" not in worker,'EFFECTIVE_LIMIT_PREDICATE_REQUIRES_GROUP_OOM')
 check("capacity==8388608" in worker and "facts['repository_readonly']" in worker and "facts['cgroup_readonly']" in worker,'EFFECTIVE_MOUNT_AND_CPU_RAM_CHECKS')
 legacy=['analysis/phase13/source/parser_contract.py','analysis/phase13/source/native_guard.py','analysis/phase13/scripts/run_parser_review.py','analysis/phase13/scripts/parser_child.py']
 for name in legacy:
  frozen=subprocess.check_output(['git','-C',str(repo),'show',BASE+':'+name]);check(frozen==(repo/name).read_bytes(),'LEGACY_BYTE_IDENTITY_'+name)
 changed=subprocess.check_output(['git','-C',str(repo),'diff','--name-only',BASE,'--','analysis/phase11','analysis/phase12','analysis/phase13','simulation'],text=True)
 check(not changed.strip(),'HISTORICAL_PHASES_AND_SIMULATION_UNCHANGED')
 frozen_ci=subprocess.check_output(['git','-C',str(repo),'show',BASE+':.github/workflows/phase13-source.yml'])
 current_ci=(repo/'.github/workflows/phase13-source.yml').read_bytes()
 old_ci=b'        run: python3 -B analysis/phase13/scripts/check_publication.py --repo .\n'
 new_ci=b'        run: |\n          if [ -f metadata/phase13f_source_manifest.json ]; then\n            python3 -B analysis/phase13f/scripts/check_publication.py --repo .\n          else\n            python3 -B analysis/phase13/scripts/check_publication.py --repo .\n          fi\n'
 check(frozen_ci.count(old_ci)==1 and current_ci==frozen_ci.replace(old_ci,new_ci),'LEGACY_CI_ONLY_EXACT_PUBLICATION_ROUTING_DIFF')
 check(b'discover -s analysis/phase13/tests' in current_ci and b'discover -s analysis/phase12/tests' in current_ci and b'discover -s analysis/phase11/tests' in current_ci,'LEGACY_OFFLINE_TEST_STEPS_RETAINED')
 evidence_result=None
 if evidence is not None:
  data=json.loads((Path(evidence)/'suite_summary.json').read_text());check(data['failure'] is None,'ACTUAL_SUITE_NO_FAILURE');check([r['case'] for r in data['results']]==EXPECTED_CASES,'ALL_31_CASES_ACTUALLY_PRESENT');check(all(r['status']=='PASS_EXPECTED_RESULT' for r in data['results']),'ACTUAL_RESULT_CASES_PASS')
  for case in EXPECTED_CASES:
   row=json.loads((Path(evidence)/case/'result.json').read_text());check(not row['residual_processes_after_cleanup'],'NO_RESIDUAL_'+case)
   for k in ('MG5_invocations','new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events'):check(row[k]==0 and type(row[k]) is int,'NO_PHYSICS_'+case+'_'+k)
   if case=='normal':check(row['resource_stop'] is None,'POSITIVE_CANNOT_HIDE_A_RESOURCE_STOP')
  evidence_result={'suite_summary_sha256':sha(Path(evidence)/'suite_summary.json'),'required_cases':len(EXPECTED_CASES)}
 return {'schema_version':1,'evidence_class':'PUBLIC_SOURCE_AUDIT','status':'PASS_INDEPENDENT_IMPLEMENTATION_SOURCE_AND_BYTE_AUDIT','method':'stdlib AST, literal independent policy specification, Git blob bytes; no imports of producer code','external_human_or_separate_agent_review':'NOT_PERFORMED_NOT_CLAIMED','checks_passed':len(checks),'checks':checks,'source_identities':[{'path':p.relative_to(repo).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sources],'CPU_quota_wall_nominal_bound_seconds':nominal,'declared_CPU_ceiling_seconds':4,'disk_allocation_bound_bytes':disk,'disk_ceiling_bytes':9437184,'actual_evidence':evidence_result,'physics_authorized':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--evidence',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=inspect(a.repo,a.evidence);raw=(json.dumps(result,indent=2)+'\n').encode();demand(len(raw)<65536,'AUDIT_OUTPUT_BOUND')
 with a.output.open('xb') as f:f.write(raw)
 print(json.dumps({'status':result['status'],'checks':result['checks_passed']}))
