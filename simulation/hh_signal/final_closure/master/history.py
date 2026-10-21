"""One exact historical CI exception, never a general input-drift override."""
import hashlib
from .contract import need
CAMPAIGN='.github/workflows/hh_signal_campaign.yml'
FROZEN='16dbaab14cc82b5b05aae04742e6f1fc9dd1d6b9b2afd88de9d98fcf1e7a6747'
PR38='91ce6880e9c2307b2d0d7eddb6696152df305e6e90083668895559a0a165b9fd'
SUFFIX=" && github.head_ref != 'codex/phase7i-master-unattended' && github.ref_name != 'codex/phase7i-master-unattended'"
def reviewed_workflow_delta(path,raw,expected):
 need(path==CAMPAIGN and expected==FROZEN,'FROZEN_INPUT_DRIFT_NOT_WORKFLOW_EXCEPTION')
 text=raw.decode('utf-8')
 if SUFFIX in text:
  need(text.count(SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY');text=text.replace(SUFFIX,'')
 need(hashlib.sha256(text.encode()).hexdigest()==PR38,'UNREVIEWED_WORKFLOW_CONTENT_CHANGE')
 return {'sha256':hashlib.sha256(raw).hexdigest(),'frozen_sha256':expected,
  'compatibility_scope':'EXACT_PR38_CI_BYTES_PLUS_ONE_MASTER_BRANCH_EXCLUSION; SCIENTIFIC_INPUTS_UNCHANGED'}
