"""One exact historical CI exception, never a general input-drift override."""
import hashlib
from .contract import need
CAMPAIGN='.github/workflows/hh_signal_campaign.yml'
FROZEN='16dbaab14cc82b5b05aae04742e6f1fc9dd1d6b9b2afd88de9d98fcf1e7a6747'
PR38='91ce6880e9c2307b2d0d7eddb6696152df305e6e90083668895559a0a165b9fd'
SUFFIX=" && github.head_ref != 'codex/phase7i-master-unattended' && github.ref_name != 'codex/phase7i-master-unattended'"
REPAIR_SUFFIX=" && github.head_ref != 'codex/phase7i-g1-association-bound-repair' && github.ref_name != 'codex/phase7i-g1-association-bound-repair'"
ENGINEERING_SUFFIX=" && github.head_ref != 'codex/phase7i-g1-g7-engineering' && github.ref_name != 'codex/phase7i-g1-g7-engineering'"
COUNTER_SUFFIX=" && github.head_ref != 'codex/g1-guest-v2-counter-parser-repair' && github.ref_name != 'codex/g1-guest-v2-counter-parser-repair'"

G2_SUFFIX=" && github.head_ref != 'codex/phase7i-g2-actual-capability' && github.ref_name != 'codex/phase7i-g2-actual-capability'"

DIAGNOSTIC_SUFFIX=" && github.head_ref != 'codex/phase7i-g2-effective-diagnostic' && github.ref_name != 'codex/phase7i-g2-effective-diagnostic'"

TOOL_BINDING_SUFFIX=" && github.head_ref != 'codex/phase7i-g2-tool-identity-binding' && github.ref_name != 'codex/phase7i-g2-tool-identity-binding'"

MANAGER_SECURITY_SUFFIX=" && github.head_ref != 'codex/phase7i-g2-manager-scope-security' && github.ref_name != 'codex/phase7i-g2-manager-scope-security'"

def reviewed_workflow_delta(path,raw,expected):
 need(path==CAMPAIGN and expected==FROZEN,'FROZEN_INPUT_DRIFT_NOT_WORKFLOW_EXCEPTION')
 text=raw.decode('utf-8')
 if MANAGER_SECURITY_SUFFIX in text:
  need(text.count(MANAGER_SECURITY_SUFFIX)==1 and text.count(TOOL_BINDING_SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(MANAGER_SECURITY_SUFFIX,'')
 if TOOL_BINDING_SUFFIX in text:
  need(text.count(TOOL_BINDING_SUFFIX)==1 and text.count(DIAGNOSTIC_SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(TOOL_BINDING_SUFFIX,'')
 if DIAGNOSTIC_SUFFIX in text:
  need(text.count(DIAGNOSTIC_SUFFIX)==1 and text.count(G2_SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(DIAGNOSTIC_SUFFIX,'')
 if G2_SUFFIX in text:
  need(text.count(G2_SUFFIX)==1 and text.count(COUNTER_SUFFIX)==1 and text.count(ENGINEERING_SUFFIX)==1 and text.count(REPAIR_SUFFIX)==1 and text.count(SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(G2_SUFFIX,'')
 if COUNTER_SUFFIX in text:
  need(text.count(COUNTER_SUFFIX)==1 and text.count(ENGINEERING_SUFFIX)==1 and text.count(REPAIR_SUFFIX)==1 and text.count(SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(COUNTER_SUFFIX,'')
 if ENGINEERING_SUFFIX in text:
  need(text.count(ENGINEERING_SUFFIX)==1 and text.count(REPAIR_SUFFIX)==1 and text.count(SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(ENGINEERING_SUFFIX,'')
 if REPAIR_SUFFIX in text:
  need(text.count(REPAIR_SUFFIX)==1 and text.count(SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY')
  text=text.replace(REPAIR_SUFFIX,'')
 if SUFFIX in text:
  need(text.count(SUFFIX)==1,'WORKFLOW_ROUTING_AMBIGUITY');text=text.replace(SUFFIX,'')
 need(hashlib.sha256(text.encode()).hexdigest()==PR38,'UNREVIEWED_WORKFLOW_CONTENT_CHANGE')
 return {'sha256':hashlib.sha256(raw).hexdigest(),'frozen_sha256':expected,
  'compatibility_scope':'EXACT_PR38_CI_BYTES_PLUS_FIXED_MASTER_G1_REPAIR_G1_G7_AND_COUNTER_REPAIR_AND_G2_BRANCH_EXCLUSIONS; SCIENTIFIC_INPUTS_UNCHANGED'}
