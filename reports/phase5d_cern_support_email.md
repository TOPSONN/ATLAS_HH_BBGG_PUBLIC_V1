# Phase 5D final CERN support email

**PREPARED / UNSENT.** No message was sent. Sending requires separate user
authorization; the earlier draft and original receipts remain unchanged.

To: atlas-outreach-opendata-support@cern.ch

Subject: Record 93922 / DSID 302521: supported access, production provenance and PHYSLITE pilot

Dear ATLAS Open Data support,

Could you help with access and exact production provenance for this member of
[CERN Open Data record 93922](https://opendata.cern.ch/record/93922)?

```text
DSID: 302521
File: ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
Published size: 110755804 bytes
Published checksum: adler32:b43248ea
HTTPS origin: https://eospublic.cern.ch/eos/opendata/atlas/rucio/opendata/
XRootD origin: root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/
```

On 2026-10-12 UTC, Windows retrieved catalog metadata and EOS HEAD reported
the expected size/checksum. IPv4 DNS/TCP probes passed. Selected Windows CERN
TLS checks passed; EOS default trust failed, while scoped pinned-CA trust
passed. WSL IPv4 TLS timed out and IPv6 reported no route. Storage redirects
reset/timed out; a metadata-only XRootD open/stat timed out after 15 seconds
without GetSize. No ROOT payload/partial file was acquired. TLS verification
was retained; root:// makes no TLS claim. Failed download routes remain
stopped, and their cause is unknown.

Please confirm external readability, any known object/redirect issue and a
supported HTTPS/XRootD endpoint, procedure, trust configuration and Windows/WSL
client settings. Can acquisition be bounded within our approved 128 MiB Phase
5 / 256 MiB cumulative limits, carrying previous charges forward? Operation
reserves are application bookkeeping, not measured wire traffic.

Before any normalization/corrections, could you identify official records for:

1. Exact FEB2025 converter commit/release/configuration, skim/merge commands,
   producer patches, conditions payloads and complete input DIDs/campaigns
   linking this member to e4045?
2. The nominal generator weight name/index and its mapping to mcWeight, plus
   the complete signed generated pre-skim sumW/sumW2 aggregation, bookkeeper
   population/cycle and evidence that all required inputs were counted once?
3. Applicable generator/common include and DirectPhotonFilter versions,
   photon eligibility/pair definition, and the relation of mHat to retained
   truth photons and the reconstructed diphoton skim?
4. The applicable cross-section database/version and sigma, filter-efficiency,
   k-factor and branching-ratio conventions, including any embedded factors?
5. PHOTON/JVT/BTAG/FTAG object populations, working points, payloads,
   invalid/sentinel behavior, BTAG–FTAG double-counting rules and the applicable
   prompt-diphoton/gamma+jet sample-overlap prescriptions?
6. Which public supported AnalysisBase release/platform/configuration and
   calibration payloads do you recommend for documented DATA run 266919
   (80000) plus MC364542 (80014), followed by a separate MC364352 prompt
   pilot? The public 25.2.2 research example is not candidate-validated.

The proposed research members are, respectively:

```text
data15_13TeV:DAOD_PHYSLITE.37001628._000001.pool.root.1
mc20_13TeV:DAOD_PHYSLITE.37322576._000009.pool.root.1
mc20_13TeV:DAOD_PHYSLITE.38191666._000047.pool.root.1
```

Inspected v1.0.0 and February candidate
`0cfc9416d6146ebdb31234f1e486f77abe28aa83` remain unmapped to actual production.
Neither generatorWeight_NOSYS nor candidate 642000 sums verify the nominal
index/complete denominator. No factors were applied, research files acquired
or new runtime installed.

Sanitized technical evidence and source hashes are available. Thank you.

## Evidence and dispatch gate

Prepared evidence: [sanitized Phase 5C network receipt](../metadata/phase5c_sanitized_network_evidence.json)
and [Phase 5D provenance review](phase5d_provenance_review.md). The network
receipt's inspected raw SHA-256 is
`0ac4afc45c708068d4befd0d9c104c83c27fa5af6a49d28e2789c962d80d048d`.
It omits resolved addresses, credentials, local user paths, proxy endpoints
and redirect capability queries. Do not attach unsanitized historical receipts.

An official reply is new evidence to review; it does not authorize downloading,
installation or normalization. No additional recipient/message was created.
