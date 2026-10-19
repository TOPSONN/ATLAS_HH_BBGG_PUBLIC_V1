"""Phase10 scientific policy. Method success cannot supply missing physical inputs."""
from copy import deepcopy
import re
STATUSES={
 'HEAVY_FLAVOUR_ORIGIN':'VALIDATED_WITH_LIMITS',
 'HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY':'UNVERIFIED',
 'PHOTON_FAKE_RATE':'UNKNOWN',
 'MATCHED_SIGNAL_NORMALIZATION':'BLOCKED_PHASE7I',
 'PHYSICAL_TOTAL_BACKGROUND':'BLOCKED',
 'PHYSICAL_SIGNIFICANCE':'NOT_EVALUATED',
 'PHYSICAL_CLs':'NOT_EVALUATED',
 'PHYSICAL_KAPPA_INTERVAL':'NOT_EVALUATED'}
COUNTERS=('NEW_ME_CALLS','NEW_INTEGRALS','NEW_HARD_EVENTS','NEW_PYTHIA_EVENTS','NEW_DELPHES_EVENTS')
ROLES={'source_review':'ACTUAL_EXISTING_DATA_READBACK','heavy_flavour':'ACTUAL_EXISTING_DATA_READBACK','photon':'ACTUAL_EXISTING_DATA_READBACK','sideband':'SYNTHETIC_METHOD_ONLY','precision':'HISTORICAL_SOURCE_AUDIT','pilot':'FUTURE_UNEXECUTED_PROPOSAL'}
CLASSES={'ACTUAL_EXISTING_DATA_READBACK','HISTORICAL_SOURCE_AUDIT','PUBLIC_SOURCE_AUDIT','SYNTHETIC_METHOD_ONLY','FUTURE_UNEXECUTED_PROPOSAL'}

def demand(ok,reason):
 if not ok:raise ValueError(reason)

def validate(matrix):
 demand(matrix.get('evidence_class') in CLASSES,'INVALID_EVIDENCE_CLASS')
 for key,value in STATUSES.items():demand(matrix.get(key)==value,'MISSING_OR_PROMOTED_PHYSICAL_GATE:'+key)
 for key in COUNTERS:demand(type(matrix.get(key)) is int and matrix[key]==0,'PHYSICAL_PRODUCTION_FORBIDDEN:'+key)
 demand(matrix.get('PHYSICAL_PILOT_EXECUTED') is False,'PILOT_FORBIDDEN')
 demand(matrix.get('FIGURE_PUBLICATION_AUTHORIZED') is False,'FIGURE_APPROVAL_MISSING')
 demand(matrix.get('physical_background_sum_pb') is None,'PHYSICAL_SUM_FORBIDDEN')
 demand(matrix.get('physical_fake_probability') is None,'FAKE_RATE_UNVALIDATED')
 nuis=matrix.get('physical_nuisances')
 demand(isinstance(nuis,dict) and nuis.get('values') is None and nuis.get('covariance') is None and nuis.get('status')=='UNKNOWN_NOT_ZERO','UNKNOWN_NUISANCE_REPLACED_BY_ZERO')
 demand(matrix.get('external_human_approval') is False,'FABRICATED_HUMAN_APPROVAL')
 demand(matrix.get('synthetic_used_in_physical_results') is False,'SYNTHETIC_PHYSICS_IMPORT')
 for key in ('source_review','heavy_flavour','photon','sideband','precision','pilot'):
  item=matrix.get('evidence',{}).get(key)
  demand(isinstance(item,dict) and item.get('evidence_class')==ROLES[key] and re.fullmatch('[0-9a-f]{64}',str(item.get('sha256'))) is not None,'MISSING_BOUND_EVIDENCE:'+key)
 return True

def assemble(evidence):
 m={'schema_version':1,'task':'PHASE10_BACKGROUND_MODEL_FEASIBILITY_V1','evidence_class':'HISTORICAL_SOURCE_AUDIT',**deepcopy(STATUSES),**{k:0 for k in COUNTERS},'PHYSICAL_PILOT_EXECUTED':False,'FIGURE_PUBLICATION_AUTHORIZED':False,'physical_background_sum_pb':None,'physical_fake_probability':None,'physical_nuisances':{'status':'UNKNOWN_NOT_ZERO','values':None,'covariance':None},'external_human_approval':False,'synthetic_used_in_physical_results':False,'evidence':deepcopy(evidence),'reason':'Existing-event diagnostics and synthetic closure do not validate generator exclusivity, fake calibration, signal normalization or physical inference.'}
 validate(m);return m
