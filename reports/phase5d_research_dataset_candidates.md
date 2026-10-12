# Phase 5D research dataset candidates

Project: ATLAS_HH_BBGG_PUBLIC_V1. Review date: 2026-10-12.

**CONDITIONAL: exact DATA, prompt-continuum, photon+jets and single-Higgs
research members are identified, but a native DATA plus continuum pilot
remains a separate gate. No research ROOT member has been acquired or
opened. No applicable HH signal is verified.** This report distinguishes an
exact published file identity from an executable, calibrated physics input.

The companion [dataset manifest](../metadata/phase5d_dataset_manifest.csv)
records physical candidates and explicitly labelled unresolved roles. An
unresolved role is not a candidate download and is not filled with a broad
collection name or an unrelated small file. Source scope and native-file
status are separate columns. No selected, generated or post-skim weight sum
is applied as a normalization denominator.

## Evidence and scope

The public [research umbrella 80020](https://opendata.cern.ch/record/80020)
links 2015 DATA 80000, 2016 DATA 80001, electroweak nominal 80010, exotic
signals 80011, Higgs nominal/variation 80012/80013, QCD nominal/variation
80014/80015, SUSY 80016 and top nominal/variation 80017/80018. Its description
documents 13 TeV pp, Athena Release 22 reprocessing and the MC20a campaign.
The filename scope `mc20_13TeV` agrees with that description. This does not
identify a particular member's full generator/simulation/reconstruction/
derivation tag chain.

The retained Phase 0 JSON and HTML responses were acquired on 2026-10-09.
Phase 5D retrieved the nominal QCD record 80014 JSON, DATA record 80000 HTML
and bounded file page, and exotic record 80011 JSON on 2026-10-12; their raw
hashes were checked during this review. Historical
metadata identity is **VERIFIED for those bytes**; current storage access,
native member contents and full production applicability remain unverified.
The Phase 5C document refresh failed before HTTP bodies and did not invalidate
or refresh those historical snapshots. The local hashes below are provenance
hashes of responses, not official checksums of ROOT payloads.

The [MC metadata table](https://opendata.atlas.cern/docs/data/for_research/metadata)
provides DSID, physics short and documented generator strings. A unique exact
physics-short join to a file-index description identifies the candidate's
documented DSID. This is a **PARTIAL production identity**, pending native
`mcChannelNumber`, production metadata and the matching weight-name and
normalization conventions. The integer `38191914` in a DAOD member name is
not DSID 343981; derivation dataset identifiers must not be parsed as physics
DSIDs. All five retained Higgs member entries have `tags: {}`.

## Exact single-Higgs members

These five entries are exact published physical members of
[nominal Higgs record 80012](https://opendata.cern.ch/record/80012), not a list
of approved downloads. The cached index lists one member for each process
below. That published member count does not by itself establish completeness
of upstream generator inputs or the applicability of a global signed sumW.

| Documented DSID and role | Exact published member filename | Bytes | Published Adler-32 |
| --- | --- | ---: | --- |
| 343981, ggF H→γγ | `mc20_13TeV:DAOD_PHYSLITE.38191914._000036.pool.root.1` | 1,929,286,284 | `4444ddc1` |
| 346214, VBF H→γγ | `mc20_13TeV:DAOD_PHYSLITE.38191539._000052.pool.root.1` | 785,967,187 | `70fd7bae` |
| 345061, gg→ZH, H→γγ, Z inclusive | `mc20_13TeV:DAOD_PHYSLITE.38191676._000005.pool.root.1` | 492,258,331 | `d0fb6b03` |
| 346525, ttH, H→γγ | `mc20_13TeV:DAOD_PHYSLITE.38191599._000036.pool.root.1` | 2,065,056,109 | `a737db60` |
| 346188, tHjb four-flavour, H→γγ | `mc20_13TeV:DAOD_PHYSLITE.38191891._000001.pool.root.1` | 551,121,421 | `925a1045` |

Their exact public ROOT URIs are in the manifest. URI publication is not a
successful stat, payload acquisition, checksum verification or native read.
The published Adler-32 values are input expectations only; no ROOT SHA-256
or locally verified Adler-32 exists for these candidates.

The metadata-table generator descriptions are, respectively:

- ggF and ggZH: `Powheg(v2_r3133)+Pythia8(v8.212)+EvtGen(v1.2.0)`.
- VBF: `Powheg+Pythia8+EvtGen`; numerical generator versions are not specified
  in that row.
- ttH: `Powheg+Pythia8(v.235)+EvtGen(v.1.6.0)`, retained as documented rather
  than repaired or promoted to an exact production version.
- tHjb: `aMcAtNlo+Pythia8.230+EvtGen`.

Those strings do not prove the exact versions of the physical MC20a member.
The record and documentation join must be completed with production tags and
sample-specific metadata before efficiency or normalization is attempted.

All five processes contain one Higgs boson. They can become relevant
single-Higgs backgrounds or resonance-method samples in a separately scoped
bbγγ-like study. **None is HH signal.** The ggZH member is the smallest of
these identified H→γγ members, but its Z-associated topology is a distinct
physics process; size is not a reason to substitute it for ggF, VBF, prompt
continuum or HH. `gamstargam` members in this index are a different decay
channel and are not used as smaller H→γγ substitutes.

Every identified H→γγ member exceeds the existing 128 MiB Phase 5 request
budget and the 256 MiB cumulative budget. Their combined payload lower bound
is 5,823,689,332 bytes. This is five selected members, not all Higgs simulation
and not an estimated calibrated analysis footprint. Output, working copies,
AnalysisBase and calibration data would be additional. The individual sizes,
rather than the full 80020 aggregate, define a future exact-file request.

## DATA, prompt continuum and γ+jets roles

The umbrella and official
[research coverage page](https://opendata.atlas.cern/docs/data/for_research/pp_data)
establish the 2015/2016 collision collection roles. The Phase 0 full 80000/80001
responses exceeded its 4 MiB metadata guard and were not retained. A collection
ID alone supplies neither an exact member filename/checksum nor accepted
runs/LBs or trigger-effective luminosity. The historical 3.2/33 fb⁻¹ release
exposures must not be assigned to one future member or a bounded row range.

Phase 5D inspected the public file-box JavaScript linked by record 80000 and
followed its explicit, read-only metadata endpoint
[first grouped file page](https://opendata.cern.ch/record/80000/filepage/1?group=1).
The successful 150,761-byte JSON contains the first **five of 131 run indices**
and 236 physical members. Each retained run's member count and summed byte
size agrees with its index metadata. This establishes exact candidates
without repeating the full API request or requesting any ROOT payload.

| Research collision DATA candidate | Exact published member | Bytes | Published Adler-32 |
| --- | --- | ---: | --- |
| Record 80000, 2015 13 TeV pp, documented run 266919 | `data15_13TeV:DAOD_PHYSLITE.37001628._000001.pool.root.1` | 7,394,251 | `1e0e3038` |

This is the smallest published member **on the inspected first page**, not
the globally smallest DATA file. Its run index contains 48 files totalling
16,285,111,040 bytes. A small file is a possible bounded schema/object-access
pilot, with no guarantee of enough photons, jets or selected events. The
run is documented by the index name; native run/LB values, GRL membership,
trigger and exposure remain NOT_EVALUATED. Its published `tags: {}` does not
supply the full reconstruction/derivation tags. The uninspected 2016 exact
member remains an explicitly unresolved role.

The newly retrieved [nominal QCD record 80014](https://opendata.cern.ch/record/80014)
contains 27 process indices and 2,097 physical files. It identifies a research
continuum route different from the educational Pythia 302521 route. The exact
physics-short join to the retained official research metadata gives Sherpa
DSID 364352 for diphotons and 364542/364543 for photon+jets slices.

| Documented DSID and exact process | Exact published pilot member filename | Bytes | Published Adler-32 | Members in the same process index |
| --- | --- | ---: | --- | ---: |
| 364352, `Sherpa_224_NNPDF30NNLO_Diphoton_myy_90_175` | `mc20_13TeV:DAOD_PHYSLITE.38191666._000047.pool.root.1` | 1,807,847,758 | `58533a66` | 19 |
| 364542, `Sherpa_222_NNPDF30NNLO_SinglePhoton_pty_35_70` | `mc20_13TeV:DAOD_PHYSLITE.37322576._000009.pool.root.1` | 87,201,141 | `346325ac` | 65 |
| 364543, `Sherpa_222_NNPDF30NNLO_SinglePhoton_pty_70_140` | `mc20_13TeV:DAOD_PHYSLITE.37322584._000156.pool.root.1` | 476,512,859 | `fca46c9e` | 146 |
| 700442, `Sh_2211_gamma2jets_pTy140_Min_N_TChannel` | `mc20_13TeV:DAOD_PHYSLITE.37110988._000012.pool.root.1` | 1,113,094,034 | `6c409368` | 1 |

For a future native-schema pilot, the selected member is the smallest exact
member **within each already identified process**, with filename as a
deterministic tie-breaker. This is a storage planning choice, not an event
selection, unbiased sample, full process model or approved acquisition.
The underlying complete per-process member list was inspected to verify
these counts and minima. A file index key's integer suffix is an ordinal,
not its DSID or the number of members.

The official table describes 364352 as Sherpa(v2.2.4), γγ+0,1 jets at NLO and
2,3 jets at LO with 90<mγγ<175; 364542/364543 as Sherpa(v2.2.2), γ+1,2 jets
at NLO and 3,4 jets at LO in the stated photon-pT slices. It describes
700442 as Sherpa(v.2.2.11p4), electroweak γ+2,3 jets at LO with pTγ>140.
Those process definitions are documentation, not native truth/filter checks.
The electroweak process must not replace inclusive QCD photon+jets. Adjacent
diphoton mass slices and photon-pT slices may contribute to a reconstructed
window; no completeness or overlap claim follows from one candidate member.

The 364542 member is smaller than 128 MiB and is potentially useful for a
photon truth/flavour and tool-access pilot. **It is not prompt diphoton
continuum and cannot replace 364352 to manufacture background closure.**
All new research downloads still require separate explicit authorization,
including this smaller member. The 364352 native-pilot payload alone is
1,807,847,758 bytes, before a DATA member, software or outputs; it exceeds
the current transfer budgets.

No Pythia 302521 or 423103 physics-short member is present in the inspected
80014 index. This is scoped to this record, not global public availability.
The educational FEB2025 filenames, checksums and DSIDs are not reused as
research PHYSLITE identities. Exact e/s/r/p tags remain UNKNOWN: all selected
QCD physical entries expose `tags: {}`. No nominal vector index, signed
pre-skim denominator or input aggregation completeness is verified for a
single selected member. The documented metadata-table numbers are not used
for normalization.

No research DATA or prompt-continuum payload is downloaded in Phase 5D.
For the exact members above, DATA plus 364542 uses **94,595,392 bytes** of
input payload; DATA plus 364352 uses **1,815,242,009 bytes**. These are input
lower bounds, not a complete processing footprint or an approved acquisition.
Metadata, immutable copies, AnalysisBase/calibration payloads, outputs and
reserve add to those amounts. The smaller pair can assess a limited
schema/photon-origin/flavour question; the larger pair is needed for the
identified prompt-continuum component. Neither pair is a complete background
model or normalization sample. An unresolved file-size field, such as the
2016 DATA member, is UNKNOWN rather than zero.

## Potential HH signal

The preserved 80012 and 80013 indices contain 94 nominal and 55 variation
process-index descriptions. Their inspected physics names do not identify an
explicit matching Higgs-pair bbγγ signal. A case-insensitive `HH` substring
would misclassify `PhH7` generator abbreviations and hadronic tau decay names
such as `tautauhh`. Process interpretation, not substring counting, supports
this scoped observation.

The freshly retrieved
[exotic-signal collection 80011](https://opendata.cern.ch/record/80011)
contains 14 process-index names: Z′, W′, dark-matter and leptoquark examples;
none identifies matching HH→bbγγ. This extends the inspected scope without
claiming global absence. Matching nonresonant HH, resonant HH, coupling variations,
truth decay and sample-specific systematics are all UNKNOWN in the present
candidate evidence. No single-H member or unrelated exotic sample is
substituted. Failure to identify HH in the inspected sources is not a claim
that no public HH data exists anywhere. HH efficiency, signal extraction,
coupling interpretation and sensitivity remain STOP with the presently
identified inputs.

## Member-specific capability gates

The public
[PHYSLITE variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html)
documents a plausible route to capabilities missing from the inspected
educational flat ntuples. It does not certify their presence, type or
validity in any candidate member. The manifest marks the following as
**DOC_ONLY / NATIVE_NOT_EVALUATED** for MC, with truth not applicable to
collision DATA:

| Requirement | Documented research fields or mechanism | Exact missing physical evidence |
| --- | --- | --- |
| Photon origin and reco–truth association | `AnalysisPhotons.truthOrigin`, `truthType`, `TruthLink`, `truthParticleLink`; `TruthPhotons` PDG/status and ancestry links | Per-file presence, units, MCTC code version, valid target collections/ElementLinks and study-specific eligible truth definition. |
| Jet flavour and b-tag scores | `AnalysisJets.HadronConeExclTruthLabelID`, `btaggingLink`; `BTagging_AntiKt4EMPFlow.DL1dv01_pb/pc/pu` | Native labels/links/scores, exact jet collection, validated WP/CDI and efficiencies. DL1d fields do not establish the publication's GN2 selection. |
| Trigger | `AnalysisTrigMatch_HLT_g35_loose_g25_loose` documented | An object match is not an event pass decision, prescale, menu, livetime or efficiency correction; per-file decisions and applicable trigger tools are unresolved. |
| Exposure | `EventInfo.runNumber`, `lumiBlock` and data-quality fields documented | Applicable GRL, complete accepted run/LB set and trigger-effective luminosity, not event fractions. |
| Generator normalization | `EventInfo.mcChannelNumber`, `mcEventWeights` and metadata guidance | Native DSID, nominal index/names, exact signed pre-skim sumW, complete aggregation and sigma/filter/k/decay conventions. |
| Calibration and uncertainties | Stored calibrated PHYSLITE objects and AnalysisBase workflow documented | Exact release, public CP tools/configuration, calibrations and object/WP/trigger-specific variation coverage for each physical production. |

The [official limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp)
restrict reconstruction from missing low-level information and warn about
unreleased signals/systematics and fast-simulation electron/photon calibration.
Simulation flavour itself must be established per candidate; the limitations
are not permission to presume that a member uses full simulation or that
all corrections are valid. A research-format label cannot close these gates.

## Ranked next actions and authorization

1. **GO: preserve exact-file metadata and close applicability questions.**
   Physical names/bytes/checksums are bound for the identified DATA/MC
   candidates. Full production tags, supported runtime/configuration, GRL,
   weight/denominator and component-completeness evidence remain separate
   gates. No ROOT member acquisition is part of this documentation action.
2. **CONDITIONAL: a separately scoped DATA plus prompt-continuum native pilot.**
   Requires explicit user approval of the exact files, total transfer/storage
   budget and selected entry limits. Check payload identities before native
   schema, DSID, links, truth/flavour and trigger evidence. No new environment
   or container is implicitly approved.
3. **CONDITIONAL: an exact single-H member for a specified background or
   resonance diagnostic.** The physical process must match the proposed
   study. Requires separate exact-file budget and tooling approval; it does
   not replace continuum or HH.
4. **STOP: calibrated complete bbγγ background model or HH interpretation.**
   Complete samples/overlap, trigger/GRL, calibrations, weights/denominators,
   uncertainties and an applicable HH signal remain unclosed. The original
   GamGam results and Phase 5C retrospective folds are preserved.

## Rechecked historical source identities

| Official source | Retained raw path | Raw response SHA-256 |
| --- | --- | --- |
| [Umbrella API](https://opendata.cern.ch/api/records/atlas-80020) | `.local/phase0_sources/opendata_80020_json.json` | `42127360b8271f7f6ed26ab78b92eea8011b2229f6695f5f912bd643a7220912` |
| [Higgs nominal API](https://opendata.cern.ch/api/records/80012) | `.local/phase0_sources/opendata_80012.json` | `d9338d0fed6eb83feb29735855531390657caec73ee6f2ba4b7df8e693515fff` |
| [Higgs variations API](https://opendata.cern.ch/api/records/80013) | `.local/phase0_sources/opendata_80013.json` | `94f5b798fc36f6edff7cdf05186cf96dbbd196fc16db52e92b3fc5399eb7bb94` |
| [QCD nominal API, retrieved 2026-10-12](https://opendata.cern.ch/api/records/80014) | `.local/phase5d_sources_20261012/record80014.json` | `6a44431db897b5dff2cb872c5ae6c1e65e5ad76c654d436cfe4e634af521b1e0` |
| [2015 DATA page, retrieved 2026-10-12](https://opendata.cern.ch/record/80000) | `.local/phase5d_sources_20261012/record80000_page.html` | `9f77e4f6a04f7a197d907741c34f0aeaff107bf5b2a4595958db9893d3cacc97` |
| [2015 DATA first file page, retrieved 2026-10-12](https://opendata.cern.ch/record/80000/filepage/1?group=1) | `.local/phase5d_candidate_sources_20261012/data2015_index_page.json` | `078a36a5212d88b2b16ad705e7dd0a0ee48a8b2a5e13c6fb325188ea403dfb2b` |
| [Exotic API, retrieved 2026-10-12](https://opendata.cern.ch/api/records/80011) | `.local/phase5d_candidate_sources_20261012/record80011.json` | `3a5de86868f45da38d7bca4cfd226768205d340b6659bd01581ab0b4cc1a014a` |
| [MC metadata](https://opendata.atlas.cern/docs/data/for_research/metadata) | `.local/phase0_sources/research_mc_metadata.html` | `b24cebfeb808e8764df4fbfbc4864cc33ed8a3070f57a7317831505cfdb0c9cd` |
| [Variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html) | `.local/phase0_sources/physlite_pp_variables.html` | `4dfb10d27f5132f1dec370f3b9df4d0231af800b67a1a9a8227b86b7c3d42abb` |
| [Coverage](https://opendata.atlas.cern/docs/data/for_research/pp_data) | `.local/phase0_sources/research_pp.html` | `c5abce7331a9e58dcabd09a6b99b1cc9d106a7ca4bfc1fcef7f0476d5cb1eaff` |
| [Limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp) | `.local/phase0_sources/research_limitations_pp.response` | `8d888a6b77ac318b7ba2224b136d85d26e849a9fa250137c3b6d3c1f1670ab68` |

`VERIFIED`, `PARTIAL`, `UNKNOWN` and `ACCESS_UNVERIFIED` describe the stated
evidence dimension; none is a physical calibration or HH readiness verdict.
All local research ROOT payload-integrity checks, native schemas, entry observations and calibrated
analysis operations remain NOT_EVALUATED in this task.
