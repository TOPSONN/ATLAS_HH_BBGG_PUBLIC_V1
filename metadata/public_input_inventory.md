# Public statistical and event-input inventory

Step: STEP_2_PHASE_0_SOURCE_FEASIBILITY. Checked: 2026-10-09 UTC.
**Status: PARTIAL.** Status definitions and the distinction between documentation and runtime verification follow [phase0_feasibility.md](../note/phase0_feasibility.md).

## Classification

- **A — public numerical information:** a published number/curve/table can support comparison or replotting. Registered table descriptions establish identity, not successful payload download.
- **B — sufficient statistical input:** a verified complete model, observations, nuisance constraints/correlations and required resources permit reproduction of the official statistical calculation. Not established here.
- **C — explicitly simplified model:** any newly constructed counting or approximate likelihood needs declared assumptions and validation. It cannot be described as the official ATLAS likelihood.
- **D — not reproducible with verified inputs:** essential event, calibration, signal or model ingredients are unverified/incomplete for the claimed reproduction.

These classes describe uses of inputs, rather than four names for a HEPData table format. A profiled scan is an output of a likelihood, not its complete generative model; a weighted plot discards category information. This is a statistical inference from the [registered table descriptions](https://api.datacite.org/dois/10.17182/hepdata.160696.v1) and the [journal fit procedure](https://doi.org/10.1016/j.physletb.2026.140280).

## HEPData 160696 identity and versions

Record [ins2943676](https://www.hepdata.net/record/ins2943676), alternate [160696](https://www.hepdata.net/record/160696), DOI [10.17182/hepdata.160696](https://doi.org/10.17182/hepdata.160696), version DOI [10.17182/hepdata.160696.v1](https://doi.org/10.17182/hepdata.160696.v1).

The official [DataCite collection metadata](https://api.datacite.org/dois/10.17182/hepdata.160696.v1) reports **version 1, 30 HasPart table DOIs**, registered 20 October 2025. All 30 individual DOI metadata responses were retrieved successfully. They identify HEPData records 166045-166074, with the individual mapping below. This verifies the table inventory, not table numerical values or resource attachments.

The DOI abstract still contains the preprint values mu_HH<3.8 and -1.7<kappa_lambda<6.6. The [journal](https://doi.org/10.1016/j.physletb.2026.140280) reports 3.7 and -1.6 respectively. Payload-version agreement is UNKNOWN. No conclusion about a numerical table update follows from the DOI metadata update timestamp.

## Access and product status

| Product | Status | Result / consequence |
| --- | --- | --- |
| Collection/table DOI identity, title and description | VERIFIED | DataCite official API: HTTP 200 for collection/version and all 30 tables. |
| HEPData collection HTML/JSON | ACCESS_UNVERIFIED | HTTP 403 for ins2943676 and 160696, including version=1 JSON and no-www variant. |
| Table 3 record JSON | ACCESS_UNVERIFIED | [166047?format=json](https://www.hepdata.net/record/166047?format=json): HTTP 403. |
| Submission YAML archive | ACCESS_UNVERIFIED | [Version 1 YAML request](https://www.hepdata.net/download/submission/ins2943676/1/yaml): HTTP 403. |
| Table 3 YAML / CSV / ROOT export | ACCESS_UNVERIFIED | Requests to `/download/table/ins2943676/Table%203/1/{yaml,csv,root}` all returned HTTP 403. Availability/format correctness could not be established behind that response. |
| Covariance/correlation matrices | ACCESS_UNVERIFIED | No matrix is named in the 30 DOI titles/descriptions. The inaccessible resource list prevents a global absence claim. |
| RooWorkspace / HistFactory / pyhf or other full likelihood | ACCESS_UNVERIFIED | No such model is identified by the 30 table descriptions; attachment listing inaccessible. Do not report NOT_AVAILABLE globally. |
| Best-fit/upper-limit numerical reference | VERIFIED in publication, A | Journal numbers are readable; Table 3 upper-limit product is registered. Its numerical payload is unverified. |
| Official statistical reproduction | D with current verified inputs | Class B sufficiency has not been established. Class C would require new assumptions. |

DataCite `formats=[]` and `contentUrl=null` do **not** mean that HEPData supplies no downloadable formats. Those fields simply do not expose them in this metadata response. HTTP 403 likewise establishes only this audit's access failure. No statistical ROOT export or workspace was downloaded or executed.

## Registered HEPData tables

The table register below is generated from the actual individual DOI titles/descriptions, with descriptions paraphrased. Each DOI links to its metadata and each record link is the registered target URL. For every row, **description: VERIFIED; values/exports: ACCESS_UNVERIFIED**. Do not infer category thresholds, bin values, axis grids, errors or correlations from the titles.

| Table | Registered content | DOI metadata | Registered HEPData URL |
| --- | --- | --- | --- |
| 1 | Weighted combined mgg fit curves | [v1/t1](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t1) | [166045](https://www.hepdata.net/record/166045) |
| 2 | Weighted combined mgg data | [v1/t2](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t2) | [166046](https://www.hepdata.net/record/166046) |
| 3 | 95% upper limits, separate runs and combination | [v1/t3](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t3) | [166047](https://www.hepdata.net/record/166047) |
| 4 | kappa_lambda observed profile scan | [v1/t4](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t4) | [166048](https://www.hepdata.net/record/166048) |
| 5 | kappa_lambda expected profile scan | [v1/t5](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t5) | [166049](https://www.hepdata.net/record/166049) |
| 6 | kappa_2V observed profile scan | [v1/t6](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t6) | [166050](https://www.hepdata.net/record/166050) |
| 7 | kappa_2V expected profile scan | [v1/t7](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t7) | [166051](https://www.hepdata.net/record/166051) |
| 8 | Observed two-coupling contours | [v1/t8](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t8) | [166052](https://www.hepdata.net/record/166052) |
| 9 | Expected two-coupling contours | [v1/t9](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t9) | [166053](https://www.hepdata.net/record/166053) |
| 10 | High-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t10](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t10) | [166054](https://www.hepdata.net/record/166054) |
| 11 | High-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t11](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t11) | [166055](https://www.hepdata.net/record/166055) |
| 12 | High-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t12](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t12) | [166056](https://www.hepdata.net/record/166056) |
| 13 | High-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t13](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t13) | [166057](https://www.hepdata.net/record/166057) |
| 14 | High-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t14](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t14) | [166058](https://www.hepdata.net/record/166058) |
| 15 | High-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t15](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t15) | [166059](https://www.hepdata.net/record/166059) |
| 16 | Low-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t16](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t16) | [166060](https://www.hepdata.net/record/166060) |
| 17 | Low-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t17](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t17) | [166061](https://www.hepdata.net/record/166061) |
| 18 | Low-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t18](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t18) | [166062](https://www.hepdata.net/record/166062) |
| 19 | Low-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t19](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t19) | [166063](https://www.hepdata.net/record/166063) |
| 20 | Low-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t20](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t20) | [166064](https://www.hepdata.net/record/166064) |
| 21 | Low-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t21](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t21) | [166065](https://www.hepdata.net/record/166065) |
| 22 | Low-mass Run-2 mgg distribution / fitted curves; exact category label unverified | [v1/t22](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t22) | [166066](https://www.hepdata.net/record/166066) |
| 23 | Low-mass Run-3 mgg distribution / fitted curves; exact category label unverified | [v1/t23](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t23) | [166067](https://www.hepdata.net/record/166067) |
| 24 | Observed kappa_lambda auxiliary scan; region assignment requires payload | [v1/t24](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t24) | [166068](https://www.hepdata.net/record/166068) |
| 25 | Expected kappa_lambda auxiliary scan; region assignment requires payload | [v1/t25](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t25) | [166069](https://www.hepdata.net/record/166069) |
| 26 | Observed kappa_lambda auxiliary scan; region assignment requires payload | [v1/t26](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t26) | [166070](https://www.hepdata.net/record/166070) |
| 27 | Expected kappa_lambda auxiliary scan; region assignment requires payload | [v1/t27](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t27) | [166071](https://www.hepdata.net/record/166071) |
| 28 | Observed kappa_lambda auxiliary scan; region assignment requires payload | [v1/t28](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t28) | [166072](https://www.hepdata.net/record/166072) |
| 29 | Expected kappa_lambda auxiliary scan; region assignment requires payload | [v1/t29](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t29) | [166073](https://www.hepdata.net/record/166073) |
| 30 | Run-3 category yields in 120-130 GeV window | [v1/t30](https://api.datacite.org/dois/10.17182/hepdata.160696.v1/t30) | [166074](https://www.hepdata.net/record/166074) |


## ATLAS auxiliary material

The [official auxiliary page](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/) supplies paper/auxiliary figures as PDF/PNG and six auxiliary tables, `tabaux_01` through `tabaux_06`: simulation setup, BDT inputs, category boundaries, Run-2 yields, Run-3 yields, and fit-result summaries (page captions). These establish reference documentation. The public HTML's 199 hyperlinks were inspected; no direct workspace, numerical ROOT/YAML/CSV file or archive was found **among those links**. This scoped observation is not evidence that no attachment exists on HEPData or another site.

PDF/PNG tables and plots are human-readable A references. Digitisation, table transcription, replotting and likelihood construction were not performed. The publication's data-availability statement directs plot/table values to HEPData and does not release its analysis event dataset; that statement is not a claim that a workspace is absent. [Publisher PDF, Data availability](https://pure-oai.bham.ac.uk/ws/portalfiles/portal/301457864/1-s2.0-S0370269326001346-main.pdf).

## Event input and correction inventory

| Input | Evidence and status | Reproduction consequence |
| --- | --- | --- |
| Public GamGam collision/MC records | VERIFIED metadata: [93915](https://opendata.cern.ch/record/93915), [93922](https://opendata.cern.ch/record/93922) | Candidate 2015-2016 objects, not the journal 308 fb^-1 sample. No event file inspected. |
| PHYSLITE data/MC collections | VERIFIED metadata: [80020](https://opendata.cern.ch/record/atlas-80020), Higgs children [80012](https://opendata.cern.ch/record/80012), [80013](https://opendata.cern.ch/record/80013) | Richer public research format; not automatically a complete HH input package. |
| Photon and jet kinematics/ID | VERIFIED documentation: [flat dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details), [PHYSLITE catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html) | Physical types/units/branches UNKNOWN until first-file verification. |
| Nominal b-tag/photon SF | VERIFIED flat dictionary and [producer v1.0.0](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/tree/v1.0.0) | Nominal b-tag SF exists; photon producer SF is loose ID/isolation. Tight-selection applicability UNKNOWN. |
| Diphoton trigger + correction | Dedicated field NOT_AVAILABLE in inspected flat dictionary; PHYSLITE matching documented, decision/correction recipe UNKNOWN | Cannot equate `trigP` or trigger matching with journal diphoton acceptance. |
| MC cross-section/filter/k-factor/generated sums | VERIFIED published [metadata](https://opendata.atlas.cern/docs/data/for_education/13TeV25_metadata); mapping to exact processed v0 file UNKNOWN | No normalised predictions before matching signed pre-skim sums and overlap rules. |
| Appropriate HH->bbgg signal/coupling variations | UNKNOWN; no named HH process found in complete GamGam MC and inspected Higgs child index names | No signal efficiency, coupling reinterpretation or HH sensitivity estimate is justified. |
| Complete HH detector/theory uncertainties | UNKNOWN; two flat JER fields are documented; [research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp) warn of missing samples | Do not substitute arbitrary nuisance values or official uncertainties for validated public-data uncertainties. |
| Full Run-2/Run-3 coverage | NOT_AVAILABLE in these specified 2015-2016 records (scoped to these records) | Official combined-data reproduction is D even if some statistical tables become accessible. |

## Closing the partial gate

First retrieve the record/resource listing and at least one versioned numerical table through an ordinary public client; record URL, format, checksum, axes/errors and values. Compare Table 3 with the journal and explicitly resolve the 3.8/3.7 version difference. Inspect any linked model/correlation resources before deciding whether B is possible. Separately validate the physical event schema, production provenance, trigger/calibration inputs and suitable HH MC. Until then, retain PARTIAL and the bounded next-step plan in [phase0_decision.md](../note/phase0_decision.md).
