# Phase 5B generation-filter and truth-pair review

**DOCUMENTED_SOURCE = IDENTIFIED; EXACT_e4045_FILTER = UNKNOWN;
GENERATOR_FILTER_APPLICABILITY = UNKNOWN.** The official source describes
DSID 302521 as direct diphoton production with a generated 100-160 GeV mass
filter. This documentation does not establish the exact filter implementation,
its pair/origin definition, or reconstructed mass-window coverage. This
additive 2026-10-12 review uses preserved official snapshots and the newly
root-ledger-acquired job response described below. This source-review subtask
makes no network request, ROOT event read, distribution, fit or normalization.

The Phase 5 baseline is `e131de92897b75185981ec2c5ce1c722e9ada6c3`, PR #8.
The original failed storage receipt and earlier scientific blockers remain
historical evidence. Physical 302521 results must be supplied by the separate
bounded acquisition and native-schema gates; no schema or entry result is
inferred from the other three MC samples.

## What is documented and what remains unverified

The preserved fresh [CERN record 93922](https://opendata.cern.ch/record/93922)
and its [API](https://opendata.cern.ch/api/records/93922) identify the exact
release member:

```text
ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
size = 110755804 bytes
published checksum = adler32:b43248ea
```

The 2026-10-12 preserved API response SHA-256 is
`750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c`.
That hash identifies response bytes, not a ROOT checksum or a frozen generator
configuration. Record membership and filename do not reveal a nominal weight
index, full processing tags, generator-filter pair, or input aggregation.

The preserved official
[v1.0.0 metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0)
provides this classification:

| Field | Later table value | Scope |
| --- | --- | --- |
| DSID / generation tag | 302521 / e4045 | Documented label, not complete production provenance |
| Process | QCD direct diphoton production | Documented process classification |
| Generator | Pythia8 v8.186 + EvtGen v1.2.0 | Documented generation description |
| Photon filter | At least two photons with pT >20 GeV | Description; exact object/status/pair logic unverified |
| Mass filter | **100 < m_gamma-gamma <160 GeV** | Description with strict bounds; exact filter algorithm unverified |
| Sigma / filter efficiency / k-factor | 18.282 pb / 0.44191 / 1 | Candidate metadata, not approved physical normalization |

Its generation-job link is
[MC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py](https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/mc15joboptions/-/tree/master/share/DSID302xxx/MC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py).
The link uses mutable `master`. No cached exact e4045-matched job, included
filter implementation, generation log or AMI/input-production mapping was
found in the initial preserved-source review. The newly witnessed current
job is recorded in the additive section below. **The exact photon eligibility, pair choice, treatment
of additional photons, prompt/shower/decay origins, filter ordering, units,
and boundary implementation remain UNKNOWN.** Its recorded immutable commit
still needs separate evidence of applicability to e4045.

## Three different selections must remain distinct

| Layer | Available description | What it does not establish |
| --- | --- | --- |
| Generation | Later table: photon pT >20 GeV and 100<m_gamma-gamma<160 GeV | Exact e4045 filter objects, pair or production efficiency |
| Public release skim | Record 93922: at least two photons each pT>=25 GeV | Exact converter/configuration, trigger conditions or complete production accounting |
| Later v1.0.0 skim code | `photon_pt >20`, then at least two such photons | Equivalence to the FEB2025 release description |
| Existing reconstruction study | Exact `study-preselection-v1` cuts, including reconstructed 105<=m_gg<=160 GeV | Official ATLAS diphoton/HH selection or generator-level support |

The public [v1.0.0 release](https://zenodo.org/records/15791092) is dated
2025-07-02, after the files' FEB2025 name tag. The 20/25 GeV skim discrepancy
therefore remains explicit; the later source is not silently substituted for
the actual release producer.

The preserved study ranks photons before acceptance, requires leading pT>35
and subleading pT>25 GeV, both |eta|<2.37 excluding the open crack
1.37<|eta|<1.52, and accepts mass endpoints 105 and 160 GeV. The two highest-pT
inclusive jets each require pT>25 GeV and |eta|<2.5. Tight photon flags remain
optional diagnostics; no official diphoton trigger or b-tag working point is
applied. These definitions and prior counts are unchanged.

## Truth mapping and generator-pair limitations

The preserved later
[converter](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
retrieves the xAOD container named `TruthPhotons`. Its
[TruthInfo source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FTruthInfo.cxx/raw?ref=v1.0.0)
retains photons with pT>=10 GeV and writes photon count, pT, eta and phi,
converting pT by 0.001. It does not write a photon status, origin, barcode,
mother, generator-filter decision or filter-pair identifier. Its truth-jet
collection is `AntiKt4TruthDressedWZJets`, with a pT>=20 GeV retention threshold;
these jet directions are not a generator-filter photon-pair definition.

The native schemas of 343981/346214/423103 show supplied truth directions, but
their presence and units do not prove 302521's actual schema. A new physical
inventory must verify the latter. Even if 302521 supplies the same branches,
the two highest-pT retained truth photons would define a **study pair**; it
would not by itself recover the e4045 generation-filter pair. Same-event
geometric matching is also insufficient to establish prompt origin or filter
identity. No generator-pair mass or migration result is fabricated here.

A defensible filter-migration study would need the exact filter implementation
and its eligible truth/pair definition, evidence that the saved truth data
retain those objects and associations, validated units and same-event identity,
and explicit treatment of missing/additional photons. If only supplied truth
directions are available, a future study can label a highest-pT truth-pair
comparison as a provisional reconstruction diagnostic, with its own defined
population. It must not call that quantity the verified generation-filter mass,
filter efficiency, full acceptance or prompt-diphoton purity.

## Supported phase space and boundaries

The documented generated window overlaps the study's reconstructed 105-160
GeV interval, but generated and reconstructed mass are different variables.
Detector response, retained objects and pair changes can cause migration;
none is measured by the source description. The strict documented generated
160 GeV edge and inclusive reconstructed 160 GeV endpoint particularly do not
justify extrapolation, a zero-migration assumption or an edge correction.
The sample cannot establish the unfiltered continuum or full reconstructed
support outside its documented generation window.

The preserved DATA sideband definition [105,120) union [130,160] lies within
the study domain, but its upper edge is near the documented generation limit.
Raw DATA sideband counts do not validate MC support or a transfer factor.
The real central window is not an independent holdout if used to tune a model.
No background dominance or physical closure is inferred.

The alternate 302520 description has 55<m_gamma-gamma<100 GeV and no finite
documented generated overlap with 105-160 GeV. Possible migration requires
measurement; this slice cannot be substituted as a generic target-window
continuum. 364352 is a different Sherpa continuum alternative with documented
90-175 GeV support; alternatives cannot be added to 302521 without verified
overlap/combination conventions. The existing 423103 DP70_140 sample is a
photon-pT slice, not a mass interval or complete diphoton/fake model.

## Preserved source integrity and next evidence

All source hashes below were rechecked against the preserved local bytes.
They are locally computed evidence hashes, not official published strong
digests or fresh successful downloads during Phase 5B.

| Preserved official source | Version / local SHA-256 |
| --- | --- |
| `extras/metadata.csv` | v1.0.0; `7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225` |
| `scripts/skimOpenDataNtuples.py` | v1.0.0; `798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8` |
| `Root/PhysLiteToOpenData.cxx` | v1.0.0; `d17dd6e26f8217bfd967dd4007cbbe1df6e8f742a8a8ee0b3fec6dfd863d0093` |
| `Root/TruthInfo.cxx` | v1.0.0; `792543c179d42efa2c10588b5175bd7150c1b9e30cfa2fd7e6e7358d7dd89317` |

The supporting [Phase 5 DSID manifest](../metadata/phase5_dsid_manifest.csv),
[source audit](phase5_mc_source_audit.md) and
[new weight provenance review](phase5b_weight_provenance.md) retain the separate
record/table/native scopes. Any new source request must use the root agent's
bounded ledger; this subtask made none. The exact job API JSON route already
suggested for optional retrieval is a metadata-only request with a 64 KiB
body cap, so an accessible response can provide content plus commit/blob IDs.
It is an access suggestion, not verified exact e4045 evidence. Official
ATLAS/Open Data production provenance may still be needed to map the immutable
job and dependencies to the released file.

**Current conclusion:** documented process/filter source is identified;
exact-production filter semantics and physical applicability are UNKNOWN.
The current bounded acquisition/native schema/reconstruction outcome must be
recorded separately when executed. Successful engineering, a file checksum,
or a supplied-truth study pair cannot independently upgrade filter applicability.

## Additive witnessed generation-job source

After the initial preserved-source review, the root agent's bounded Windows
GitLab request retrieved the exact job file API JSON: **2,401 response-body
bytes**, preserved at
`.local/phase5b_windows_sources_20261012/job302521_master.json`. The response
SHA-256 is
`f675347ddc6bd4dd17c5cfa51353af036c9ee29c5b0e8dd0cec1debbe7ae6060`.
Local base64 decoding produced **1,422 bytes**, SHA-256
`781c937e48b0c4a345952fa0ee856e8b59206d44aed3bb2954c226d39eb6b145`,
exactly matching the response's `content_sha256`. No network request or
generation execution was made by this reviewer.

The response identifies repository commit
`2ae5d187a6036647276a28f7e62b9779edea76dc`, file last-commit
`586c7ddeb4f4e6856888ecea663187a9fdaf35e0`, and blob
`9cae92a8f15d26aab84cd11003de15030fb0f56e`. The inspected content therefore has
a [frozen repository reference](https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/mc15joboptions/-/blob/2ae5d187a6036647276a28f7e62b9779edea76dc/share/DSID302xxx/MC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py).
It was retrieved through `master` at that reported commit; **mapping this
specific source and its dependencies to the e4045 production remains UNKNOWN**.
Its SHA validates decoded content, not the production history of the ROOT file.

The witnessed source explicitly configures:

| Generator/filter setting | Literal configured value |
| --- | --- |
| `PromptPhoton:ffbar2gammagamma` | on |
| `PromptPhoton:gg2gammagamma` | on |
| `PhaseSpace:pTHatMin` | 18 |
| `PhaseSpace:mHatMin` | 100. |
| `PhaseSpace:mHatMax` | 160. |
| `DirectPhotonFilter.Ptcut` | 20000. |
| `DirectPhotonFilter.Etacut` | 2.7 |
| `DirectPhotonFilter.NPhotons` | 2 |

It includes `MC15JobOptions/Pythia8_A14_NNPDF23LO_EvtGen_Common.py` and
instantiates `DirectPhotonFilter` through `GeneratorFiltersConf` if necessary.
The included common configuration and the exact production-version filter
implementation have not been witnessed at this checkpoint. Consequently,
the numeric Ptcut's unit, exact greater-than/equality treatment, count equality
versus minimum count, status/barcode/origin eligibility, and ancestor logic
must be established from the applicable implementation; property names alone
do not supply them.

The actual mass-related commands in this job are **generator PhaseSpace mHat
settings**. There is no explicit `DirectPhotonFilter` photon-pair mass predicate
configured in the inspected file. The text description calls the sample
100<Mgg<160, but that label must not be treated as proof that the two highest-pT
saved `TruthPhotons`, the geometrically matched truth pair, or reconstructed
pair must satisfy that interval. In particular, the supplied-truth collection
and its postprocessing threshold are not proven identical to the generator's
phase-space variable or filter population. No observed truth-pair or
reconstructed out-of-window event is classified as a generator-filter failure
solely from that comparison.

This new source clarifies the configured generation structure and photon
filter properties. It does **not** validate the exact e4045 implementation,
filter efficiency 0.44191, reconstructed coverage, prompt purity or migration
acceptance. The existing UNKNOWN filter-applicability verdict is preserved.
Any dependency/manual request remains metadata-only, capped and charged in
the root agent's new ledger; no unmetered source or ROOT access is introduced.

## Current bounded-access outcome

The separately executed access attempts ended **CONTINUUM_ACCESS =
BLOCKED_NETWORK**. The root-owned metadata-only XRootD open/stat probe timed
out after its 15-second limit; its preserved receipt is
`.local/phase5b_xrootd_metadata_20261012/audit.json`. The receipt records zero
ROOT payload bytes, **5,302,259 Phase 5 charged bytes** and **83,436,281
cumulative charged bytes**, carrying forward the unchanged historical
receipt and all prior diagnostic operation charges. Consumed metadata bodies
and reserved operation charges are accounting quantities; XRootD/control
wire traffic is not measured and no end-to-end TLS claim is made for the
public `root://` protocol.

No physical 302521 file, native schema, entry count, truth pair or filter-edge
observation is available in this run. Those gates are **NOT_EVALUATED**, not
failed physics tests. The witnessed job source improves documentation only;
exact-generation applicability, prompt purity and reconstructed coverage
remain UNKNOWN. Existing DATA and three-MC evidence are preserved.
