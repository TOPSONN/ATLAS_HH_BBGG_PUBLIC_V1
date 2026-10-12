# Phase 5 MC source and generation audit

**CONTINUUM_SOURCE_IDENTIFIED: DSID 302521.** Its current CERN release identity
is verified. The user has approved acquisition of this single file under a new
128 MiB Phase 5 allocation and the preserved 256 MiB cumulative ceiling.
The bounded acquisition attempt ended **BLOCKED_ACCESS**, with no ROOT payload;
the 302521 native schema is **NOT_EVALUATED**. Source identity does not validate a signed normalization denominator,
calibration, complete background mixture, or an absolute DATA/MC prediction.

This additive audit is dated 2026-10-12 and starts from Phase 4 head
`704045c6c18c313114e3ab41019e46c70beb086b`. The original failed Phase 4 result
and its subsequent numerical recovery remain separate historical evidence.
The [Phase 4 recovery decision](phase4_numerical_recovery_decision.md),
[numerical gates](../metadata/phase4_numerical_gate_results.json), and
[weight readiness update](phase4_weight_readiness_update.md) remain preserved.
No old DATA selection, cutflow, MC weights, scale factors, or report is changed
by this source audit. ROOT 6.40.04 / C++20 remains the engineering baseline.

## Current release identity and bounded access

The current [official GamGam MC record 93922](https://opendata.cern.ch/record/93922)
describes the 2015+2016 13 TeV educational beta release, 373 files, and
12,120,657 events. Its stated GamGam skim requires at least two photons with
pT at least 25 GeV. The release DOI is
[10.7483/OPENDATA.ATLAS.IMZO.7U52](https://doi.org/10.7483/OPENDATA.ATLAS.IMZO.7U52).

Fresh verified-HTTPS API metadata was obtained on 2026-10-12, with redirects
disabled, a 1 MiB body cap per request, and no disabled certificate checks:

| Official metadata response | Actual response-body bytes | Locally computed SHA-256 |
| --- | ---: | --- |
| [93922 API](https://opendata.cern.ch/api/records/93922) | 337,923 | `750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c` |
| [93915 DATA API](https://opendata.cern.ch/api/records/93915) | 15,864 | `449cebdcffa9b6dfb527ec41519e671fee5e4d4292133f3bf88b99a22607ecb9` |

The exact 302521 entry is:

| Field | Published value |
| --- | --- |
| Filename | `ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root` |
| Size | **110,755,804 bytes** |
| Checksum | **`adler32:b43248ea`** |
| File UUID | `b46e3095-bb29-4d69-b64a-c49176ba87f4` |
| Version UUID | `be59176c-fa5c-46ea-97ab-fe941b1e8b1a` |
| Bucket UUID | `95bcca35-f11d-474a-b954-230ea0dbcaca` |
| Public URI | `root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root` |

No matching 302521 ROOT cache was found before acquisition authorization. The
new budget is a separate user-approved allocation; it does not erase the
historical transfer charges. The two successful metadata requests consumed
353,787 application response-body bytes. Four additional small version-tagged
GitLab documentation requests failed during host lookup, with zero response
body bytes. Including a 65,536-byte reserve for each of the six attempts, the
metadata/documentation charge is **747,003 bytes**. These are application-body
bytes plus explicit reserves, not measured wire traffic. Browser transport
bytes are unavailable. The preserved access receipt is
`.local/phase5_sources_20261012/access.json`; its current SHA-256 is
`a08ed08d8a5aa378c9edfb8e2a9cd729d3904ea69797a80f06ddde0c74c73196`.

The official published Adler-32 and local SHA-256 have distinct roles: the
former is the release's public checksum; the latter identifies the local bytes
actually acquired. A local SHA-256 is not an official published strong digest.
The fresh metadata confirms current release membership, not end-to-end ROOT
transport or the file's physical schema. Actual downloader results belong in
the Phase 5 transfer evidence and this report's physical-access supplement.

## Versioned process and generator evidence

The following values come from the preserved official
[PhysLiteToOpenData v1.0.0 metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0),
acquired 2026-10-09, SHA-256
`7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225`.
The new audit joins it to the fresh record by exact DSID and filename;
[phase5_dsid_manifest.csv](../metadata/phase5_dsid_manifest.csv) preserves
the separate record and table source identities.

| DSID / table generation tag | Documented process and generator | Generated phase-space information | Intended role |
| --- | --- | --- | --- |
| 302521 / e4045 | QCD direct diphoton; Pythia8 v8.186 + EvtGen v1.2.0 | At least two photons with pT >20 GeV; **100 < m_gamma-gamma <160 GeV** | Relevant generated continuum window; not a full continuum prediction |
| 343981 / e5607 | Single-H ggF H125 gamma-gamma; Powheg v2_r3133 + Pythia8 v8.212 + EvtGen v1.2.0 | Decay-constrained H125 example; exact generation/decay implementation unverified | Single-H resonance example, **not HH** |
| 346214 / e6970 | Single-H VBF H125 gamma-gamma; Powheg + Pythia8 + EvtGen | H125 decay-constrained example; exact generation/decay implementation unverified | Single-H resonance example, **not HH** |
| 423103 / e3791 | QCD direct photon production; Pythia8 v8.186 + EvtGen v1.2.0 | At least one hard-process or parton-shower photon with **70 < pT <140 GeV** | Gamma+jet/dijet photon-pT slice; not an m_gamma-gamma window or complete fake model |
| 302520 / e4045 | QCD direct diphoton; Pythia8 v8.186 + EvtGen v1.2.0 | Two photons pT >20 GeV; **55 < m_gamma-gamma <100 GeV** | Excluded as a generic generated 105-160 GeV continuum substitute |
| 364352 / e6452 | Sherpa v2.2.4 diphoton, 0/1 jet at NLO and 2/3 jets at LO | **90 < m_gamma-gamma <175 GeV** | Relevant alternative; 590,212,105 bytes exceeds the new entire 128 MiB allocation |

The strict generator boundaries above are the table's documented descriptions.
They are not a newly measured truth filter efficiency or verification of the
exact generator-level object/pair algorithm. The linked MC15 generation jobs
use mutable `master` URLs; an e4045/e5607/e6970/e3791-matched frozen generation
job and full production chain have not been recovered. **Exact release
generator-filter implementation and nominal weight-index semantics remain
UNKNOWN.** A filename and an e-tag label alone cannot prove them.

The documented 100-160 GeV filter overlaps the study's 105<=m_gamma-gamma<=160
GeV reconstructed window, but generated and reconstructed mass are different
quantities. Migration, the selected photon pairing, and the finite generator
endpoints can bias the reconstructed shape near boundaries. This sample does
not establish the continuum outside its generated support; no extrapolation
or rate stitching to incompatible slices is permitted. Conversely, the
302520 description has no finite generated 105-160 GeV overlap. Possible
detector migration would require an explicit measured study; it is not a
generic replacement for the target continuum.

The later [v1.0.0 release](https://zenodo.org/records/15791092) was published
2025-07-02, after the files' `ODEO_FEB2025_v0` name tag. Its
[skim script](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
uses a 20 GeV photon skim, while record 93922 states 25 GeV. These are separate
source facts. The exact FEB2025 converter/configuration, input dataset tags,
filter, calibration, and skim equivalence remain **UNKNOWN**.

## Normalization and corrections remain disabled

| DSID | Table sigma [pb] | Table filter efficiency | k-factor | Generated N | Table signed sumW | Table sumW2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 302521 | 18.282 | 0.44191 | 1 | 642,000 | 642,000 | 642,000 |
| 343981 | 28.3 | 0.00227 | 1.717 | 200,000 | 5,660,114.774513245 | 162,287,375.54376578 |
| 346214 | 3.782 | 0.00227 | 1 | 80,000 | 299,915.6851153374 | 1,142,827.2423424923 |
| 423103 | 106,210,000 | 0.0000393 | 1 | 1,989,000 | 1,989,000 | 1,989,000 |

These are later official table values, not authorization to normalize the
FEB2025 trees. In the existing physical diagnostics, 423103 has native filter
efficiency 0.000039, unlike the table's 0.0000393; both remain preserved. The
H-sample generated sums differ from table values by amounts consistent with
Float32 rounding, despite double native branches; the aggregation precision
and exact production route remain unknown. The dictionary's square-root
wording for sum fields conflicts with the later skim script's direct
CutBookKeeper-bin sums. No square/square-root repair is applied.

In the later
[converter source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0),
`mcWeight` copies `generatorWeight_NOSYS`, and xsec/filter/k-factor come from
the PMG cross-section tool. This documents the later implementation, not the
exact FEB2025 nominal weight index or generator-to-flat input accounting.
The original [native weight evidence](../metadata/phase4_weight_normalization_evidence.json)
covers [100,10000): negative generator-weight counts are 14/15/0 for
343981/346214/423103. Negative BTAG scalar counts are separately 18/75/103.
The correction scalars are not signed generator weights. No negative values
are replaced with unity, zero, or absolute values, and no scale factor is
applied. Detailed FTAG/BTAG/photon/pileup/JVT limits remain in the
[weight readiness update](phase4_weight_readiness_update.md) and the new
[normalization contract](phase5_normalization_contract.md).

Decay-forced H gamma-gamma samples require exact sigma/filter/branching-ratio
conventions before any extra branching factor. The existing 0.00227 table
efficiencies do not justify multiplying an additional decay branching ratio.
Generated counts, the partial diagnostic sum, selected-C9 sums, native tree
entry counts, and sumW2 are not interchangeable signed pre-skim denominators.
Production/skim completeness is **UNKNOWN** for each DSID. The full-period and
bounded DATA luminosities remain unresolved in the
[luminosity audit](phase5_luminosity_audit.md).

## Combination and physical interpretation limits

All samples remain separate. Different process labels alone do not demonstrate
physical disjointness: 423103 explicitly includes hard-process or shower
photons, and the released reconstruction has no validated prompt/fake origin
partition. Pairwise phase-space/overlap disposition, alternative-sample
exclusion, complete slicing, signed weights, and calibrated selection would
be needed before a combined prediction. A generated filter box alone does not
prove reconstructed disjointness.

The current selection remains `study-preselection-v1`: leading/subleading
photon pT >35/>25 GeV, both |eta|<2.37 excluding 1.37<|eta|<1.52,
105<=m_gamma-gamma<=160 GeV, and the two highest-pT inclusive jets each pT>25
GeV and |eta|<2.5. Raw tight-ID/isolation flags are optional diagnostics,
not selection cuts. No official diphoton trigger or b-tag working point is
applied; m_jj is an inclusive dijet mass, not a validated m_bb.

**Source identification is supported; complete physical continuum coverage,
nominal signed-weight semantics, generated-denominator completeness, exact
decay convention, calibrated DATA/MC compatibility, and absolute normalization
are not established.** Synthetic signed-weight, shape, and transfer-factor
tests can verify software contracts independently; they do not resolve these
physical inputs or constitute real CR closure, HH sensitivity, or reproduction
of an ATLAS likelihood.

## Physical-access supplement

Acquisition of the one 302521 file was explicitly authorized and attempted by
the bounded downloader. Its final receipt at
`.local/phase5_access_20261012/access.json` records **BLOCKED_ACCESS**, zero ROOT
payload bytes and zero remote ROOT operations. Independent inspection finds
only that receipt in the access directory; no final or partial ROOT payload
was created there. **CONTINUUM_FILE_ACCESS = BLOCKED_ACCESS;
CONTINUUM_SCHEMA = NOT_EVALUATED.**

Verified-HTTPS CERN CA retrieval and official EOS HEAD requests succeeded.
The HEAD response reports Content-Length 110,755,804 and an ETag containing
`b43248ea`, consistent with the public metadata. This is a header/identity
check, not a computed ROOT checksum match. Official GET requests redirected
to explicit public HTTP storage; the Windows and WSL HTTP storage attempts
failed, as did a verified-TLS HTTPS storage attempt. HTTPS certificate and
hostname validation remained enabled where HTTPS was attempted, with
additional CERN CA material scoped to the process. No end-to-end TLS transport
or successful payload acquisition is claimed.

The receipt contains 16 charged requests and 15,471 response-body bytes, all
from public certificate retrieval, not ROOT data. Its transfer charge is
1,064,047 bytes (body bytes plus 16 x65,536 reserves). Including the separate
747,003-byte metadata/documentation charge, **Phase 5 charged total =
1,811,050 bytes** and **historical cumulative charged total = 79,945,072 bytes**.
The receipt SHA-256 is
`be764a03f335e9cf238b9e8f1f67a8fd82bfa07aeb2ae145f490e8d6547ab134`.
Failed attempts remain preserved, and the transfer ceased after the bounded
routes failed. This is an access blocker, not a denial of authorization,
budget exhaustion, or global public sample absence.

No 302521 native branch, generated sum, entry count, unit scale, signed-weight
diagnostic or physical validation is inferred from the other three MC files.
Metadata/source investigation and independent synthetic engineering can
continue; physical continuum reconstruction and shape/closure evidence are
blocked by the missing verified input. A future separately bounded transport
retry can reuse the exact approved file identity without substituting an
irrelevant mass slice, while preserving the ledger and current artifacts.

## Reproduction and source integrity

Fresh record responses are saved under `.local/phase5_sources_20261012/`;
preserved v1.0.0 source bytes remain under `.local/phase0_sources/` and are
registered in [sources.md](../metadata/sources.md). The source audit uses
JSON parsing and exact DSID joins, not event-level reads. For an independent
local check in PowerShell:

```powershell
Get-FileHash .local/phase5_sources_20261012/record93922.json -Algorithm SHA256
$record = Get-Content .local/phase5_sources_20261012/record93922.json -Raw | ConvertFrom-Json
$record.metadata._files | Where-Object { $_.key -match '_mc_302521\.' }
Import-Csv metadata/phase5_dsid_manifest.csv | Where-Object dsid -EQ 302521
```

The manifest records whether each identity is fresh metadata, preserved native
evidence, or an uninspected alternative. No dataset or unapproved PDF/PNG is
part of the source/report payload.
