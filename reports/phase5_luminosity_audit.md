# Phase 5 DATA luminosity and trigger audit

**DATA_LUMINOSITY = UNKNOWN; BOUNDED_DATA_LUMINOSITY = UNKNOWN;
ABSOLUTE_MC_NORMALIZATION = BLOCKED.** The current record and native branch
inventory identify the inspected DATA file but do not establish a luminosity
for the study's arbitrary event-index subset. No event-count fraction is
converted to luminosity. This additive audit, dated 2026-10-12, preserves
all historical counts and `study-preselection-v1` cuts.

## Identified input and exact exposure question

Fresh [CERN record 93915](https://opendata.cern.ch/record/93915) describes the
2015+2016 13 TeV educational beta GamGam DATA release, 16 files and 36,564,144
events. Its release DOI is
[10.7483/OPENDATA.ATLAS.GYRR.GRP3](https://doi.org/10.7483/OPENDATA.ATLAS.GYRR.GRP3).
The record states a two-photon skim with pT at least 25 GeV per photon. The
specific inspected file is:

| Identity | Value |
| --- | --- |
| Filename | `ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root` |
| Current published size | 17,541,818 bytes |
| Current published checksum | `adler32:037f48e7` |
| Version UUID | `f72b8f02-cc6d-4e9d-a261-d3bf6a859bd8` |
| Local input SHA-256 | `01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7` |
| Native tree / total entries | `analysis` / 63,195 |
| Historical study range | **[100,63195)**, 63,095 entries |
| Preserved C9 count | **1,689** |

The fresh [93915 API](https://opendata.cern.ch/api/records/93915) response
contains 15,864 bytes, SHA-256
`449cebdcffa9b6dfb527ec41519e671fee5e4d4292133f3bf88b99a22607ecb9`.
The input checksum and tree/range facts come from the preserved physical
schema and Phase 4 numerical-recovery evidence, not a new ROOT event reading
for this audit. Source metadata is saved in
`.local/phase5_sources_20261012/record93915.json`. The exact local DATA SHA-256
is not an official published strong digest.

## Five distinct luminosity scopes

| Scope | Required definition/evidence | Actual status |
| --- | --- | --- |
| A. Full 2015 Period D | Period's exact run/LB boundaries and calibrated delivered/recorded exposure convention | **UNKNOWN** for the inspected file; no applicable numerical value established |
| B. GRL-qualified Period D | Exact GRL version, accepted run/LB intervals, detector-quality definition, matching luminosity integration | **UNKNOWN** |
| C. Photon-trigger-effective exposure | Exact chains/menu by LB, prescales, live fraction, overlap of accepted chains, and relevant trigger acceptance | **UNKNOWN** |
| D. Exposure applicable to released skim | Complete production input list, accepted run/LBs, GRL/trigger conditions, processing completeness and skim semantics | **UNKNOWN** |
| E. Bounded entries [100,63195) | Evidence that retained indices form a defined luminosity-complete exposure, or a validated inclusion-probability model | **UNKNOWN**; no such evidence exists in the inspected inventory |

The preserved official
[educational dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
quotes approximately 36 fb^-1 for the combined 2015+2016 educational release.
That is a release-wide description, not a Period D, trigger-effective, skim,
or bounded-entry luminosity. It is not assigned here. A value of 308 fb^-1
likewise has no established applicability here and is not assigned.
Even a later verified full-period value would not automatically supply
scopes B-E. In particular, 63,095/63,195 and C9/C0 are event fractions,
not exposure factors. Excluding the first 100 file entries has no known
run/LB/livetime interpretation; file ordering need not sample exposure uniformly.

## Native inventory: what is and is not present

The complete preserved [physical branch inventory](../metadata/root_schema_manifest.csv)
contains **119 distinct present branches** for the SHA-pinned DATA input.
It has `runNumber` (UInt_t), `eventNumber` (ULong64_t), and `trigP` (Bool_t),
plus other aggregate trigger flags. A complete case-insensitive branch-name
scan finds no luminosity-block, luminosity, prescale, or livetime field.
This is an absence in this inspected flat ROOT schema, not a claim that
ATLAS has no such information elsewhere.

Run/event identifiers alone cannot reconstruct accepted LB ranges, prescales
or exposure. `trigP` is one event decision and cannot encode a per-LB
effective luminosity or a calibrated efficiency. The derived event cache
does not add these missing physical inputs. The existing selection neither
requires `trigP` nor applies a photon trigger correction; raw tight-ID and
tight-isolation flags also remain optional diagnostics.

## What the later versioned producer documents

The preserved official
[PhysLiteToOpenData v1.0.0 converter](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
sets its photon aggregate decision to the OR of:

| Later producer branch | Code's run selector | Chains |
| --- | --- | --- |
| `trigP`, 2015 | `RandomRunNumber <= 284500`; DATA assigns the actual run number to that field | `HLT_g120_loose`, `HLT_g200_etcut` |
| `trigP`, 2016 | Other side of that selector | `HLT_g140_loose`, `HLT_g300_etcut` |

The official dictionary calls `trigP` an aggregate **single-photon** decision.
This is not an established diphoton 35/25 GeV trigger decision. The chain
names are retained literally; their complete online thresholds, plateau,
prescale/livetime history and FEB2025 equivalence are not inferred from their
names or from an event flag. Nor does the code selector prove the exact
Period D run boundaries or the released file's full menu.

The later
[algorithm configuration](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=v1.0.0)
lists these GRL candidates:

```text
GoodRunsLists/data15_13TeV/20170619/data15_13TeV.periodAllYear_DetStatus-v89-pro21-02_Unknown_PHYS_StandardGRL_All_Good_25ns.xml
GoodRunsLists/data16_13TeV/20180129/data16_13TeV.periodAllYear_DetStatus-v89-pro21-01_DQDefects-00-02-04_PHYS_StandardGRL_All_Good_25ns.xml
```

It enables event cleaning but **comments out** the explicit `.userGRLFiles`
assignment. These listed filenames do not prove that either exact GRL was
used in the FEB2025 release. Defaults, actual configuration, and production
input provenance must be recovered before assigning GRL-qualified exposure.
The public [GRL documentation](https://opendata.atlas.cern/docs/documentation/data_collection/GRL_definition)
is a relevant reference; fresh access returned 403, so no uninspected GRL
content is promoted into evidence.

The preserved
[v1.0.0 skim script](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
opens `extras/lumitable_2015.csv` and `extras/lumitable_2016.csv` and adds the
column named ` LAr Corrected` for recognized input run/year keys. The
[versioned 2015 table URL](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Flumitable_2015.csv/raw?ref=v1.0.0)
and its repository-tree presence are identified, but this audit did **not**
retrieve its contents. The bounded fresh request failed at DNS lookup with
zero body bytes. A table's existence or source comment does not reveal its
units, GRL/trigger convention, Period D sum, or applicability to these files.
The skim source can skip inputs whose expected histogram directory is absent;
complete production input accounting is needed even if a luminosity table is
later recovered.

The [v1.0.0 release](https://zenodo.org/records/15791092) dates from 2025-07-02,
later than the input's FEB2025 tag. The record's 25 GeV skim also differs from
the later script's 20 GeV skim. Exact producer and lumi/GRL/trigger
equivalence therefore remain **UNKNOWN_EXACT_RELEASE**.

## Source versions, access limitations and reproducible checks

The later source snapshots below were acquired from official version-tagged
URLs on 2026-10-09 and preserved; these hashes identify local response bytes,
not fresh successful downloads or official published strong digests.

| Evidence | Locally computed SHA-256 |
| --- | --- |
| `Root/PhysLiteToOpenData.cxx`, v1.0.0 | `d17dd6e26f8217bfd967dd4007cbbe1df6e8f742a8a8ee0b3fec6dfd863d0093` |
| `python/PhysLiteToOpenDataAlgorithms.py`, v1.0.0 | `5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3` |
| `scripts/skimOpenDataNtuples.py`, v1.0.0 | `798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8` |
| Educational dictionary, preserved text | `09997d17b69c871fe46b79faca3c76d5827b99e2df907b403db2b1a7372d0096` |
| Native DATA schema CSV | `a4692e9abffaada1418647d552994938f040616fafe407d95fbf6e9dad947ffc` |
| Preserved selection config | `77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751` |

Fresh CERN APIs succeeded with TLS verification. Detailed ATLAS documentation
returned browser 403 errors; four bounded GitLab text requests failed during
host lookup. No TLS verification was disabled, no failed content was used as
a numerical luminosity, and no access error was treated as global public
absence. The source audit's metadata charge and receipt are recorded in the
[MC source audit](phase5_mc_source_audit.md). Failed attempts remain preserved.

The [luminosity evidence CSV](../metadata/phase5_luminosity_evidence.csv)
separates the five scopes, later implementation facts, and native inventory.
Empty numerical values mean unresolved exposure, not zero luminosity.
An independent inventory check uses no new ROOT event reads:

```powershell
$schema = Import-Csv metadata/root_schema_manifest.csv
$names = $schema | Where-Object present -EQ yes | Select-Object -ExpandProperty actual_branch -Unique
$names | Where-Object { $_ -match '(?i)(lumi|lumiblock|prescale|livetime)' }
Import-Csv metadata/phase5_luminosity_evidence.csv
```

## Evidence required to unblock absolute normalization

Recover the exact FEB2025 producer/configuration and full input run/LB list;
identify the applied GRL and calibrated run/LB luminosity source; establish
the actual photon trigger/stream selection, per-LB prescales and livetime with
chain-overlap treatment; demonstrate processing/skim completeness; and map
the inspected entry selection to a justified exposure or redesign the sample
to a defined complete run/LB population. The historical [100,63195) evidence
must remain preserved if a future study introduces a different population.

Until those inputs are established, only bounded raw distribution diagnostics
and independent synthetic normalization/shape/CR tests are supported. Missing
luminosity does not block MC provenance research or engineering tests; it does
block a luminosity-normalized absolute background prediction. No nominal
36 fb^-1 or 308 fb^-1, count-ratio rescaling, signal sensitivity, or real
physical closure claim is introduced.
