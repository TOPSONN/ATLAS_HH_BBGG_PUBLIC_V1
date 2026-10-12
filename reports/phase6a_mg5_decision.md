# Phase 6A final decision and acceptance report

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1
TASK: PHASE6A_MADGRAPH5_LO_GENERATION_AND_GITHUB_SAMPLES_V1
STATUS: PASS_MG5_GENERATION_AND_GITHUB_PUBLICATION

MG5_INSTALLED: YES; verified isolated user-owned installation
MG5_VERSION: 3.5.16 LTS
MG5_SOURCE: https://github.com/mg5amcnlo/mg5amcnlo.git; v3.5.16; 3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7
MG5_ENVIRONMENT: Ubuntu WSL2 x86_64; Python 3.12.15; six 1.17.0; GCC/G++/gfortran 14.4.0; make 4.4.1; separate conda prefix; ROOT 6.40.04/C++20 preserved
GENERATOR_MODEL: bundled sm-no_b_mass; standalone model release number UNKNOWN; exact source identity and restriction hashes recorded

PROCESS: p p > b b~ a a QCD=2 QED=2 (MG5 interprets = as <=; tree continuum alpha_s^2 alpha_em^2)
PERTURBATIVE_ORDER: LO only
FLAVOUR_SCHEME: 5F massless hard process; proton contains g,u,d,s,c,b and antiquarks; b mass=0, ymb=0
SQRT_S: 13000 GeV; beams 6500+6500 GeV
PDF_SET: built-in CTEQ6L1, identifier 10042; alpha_s(MZ)=0.130, LO running
GENERATION_CUTS: photon pT>=25 GeV, |eta|<=2.5; b pT>=20 GeV, |eta|<=5; DeltaR(gamma,gamma), DeltaR(b,gamma), DeltaR(b,bbar)>=0.4; maxjetflavor=4 for b cut classification; ptgmin=0; muR=muF=125 GeV

SMOKE_100: PASS_REAL_MG5_GENERATION
SMOKE_ACTUAL_EVENTS: 100
SMOKE_CROSS_SECTION: 0.06597578 +/- 0.0006215035 pb (finite-domain LO integration)
SMOKE_SAMPLE_SHA256: 1427fd1446f6bce5627be769a5fde905206f01b684d72d2b8ee35b46a198c568
SMOKE_GITHUB_STATUS: PUBLISHED_AND_DOWNLOADED_HASH_VERIFIED; 22486 bytes

REFERENCE_1000: PASS_REAL_MG5_GENERATION
REFERENCE_ACTUAL_EVENTS: 1000
REFERENCE_CROSS_SECTION: 0.06624666 +/- 0.0005940933 pb (finite-domain LO integration)
REFERENCE_SAMPLE_SHA256: bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343
REFERENCE_GITHUB_STATUS: PUBLISHED_AND_DOWNLOADED_HASH_VERIFIED; 166818 bytes

LHE_STRUCTURE_VALIDATION: PASS; LHE 3.0; gzip CRC and XML; every event checked
FOUR_MOMENTUM_CLOSURE: PASS; max residuals 5.699985194951296e-08 / 9.699988368083723e-08 GeV for 100 / 1000 events
WEIGHT_VALIDATION: PASS; IDWTUP=-4, event_norm=average; zero negative and zero zero weights; histogram weight XWGTUP/N
REPRODUCIBILITY: exact cards, seeds, source/PDF identities, integration logs, banners, deterministic gzip and original/published hashes; no event edits; cross-toolchain bitwise identity not claimed

USER_SELF_SERVICE: PASS_PHYSICALLY_EXECUTED; 100/1000 bbgg, 23 diphoton at 14 TeV with changed cuts/supplied cards, 7 bbgg with supplied cards, final isolated-output 3 bbgg; interactive prompt/help/quit executed; 10000-event option supported but not physically tested
USER_COMMAND: bash simulation/mg5/scripts/generate_sample.sh --events 100 --seed 20261020 --energy 13000 --output .local/user-samples/my_new_bbgg_100
USER_GUIDE: simulation/mg5/USER_GUIDE_ZH_TW.md; personal samples LOCAL_ONLY; no automatic Git publication

GITHUB_CI: PASS; actual MG5 reference samples push and pull_request Actions SUCCESS; 22 portable tests; ROOT main baseline CTest 5/5 PASS
GITHUB_SAMPLE_PATHS:
- reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz
- reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz
GITHUB_PR_BASE: main
GITHUB_PR_HEAD: codex/phase6a-mg5-lo-bbgg

GATES_PASS: A, B, C, D, E, F, G, H, I, J
GATES_FAIL: NONE
GATES_BLOCKED: NONE

COMMIT_HASH: tested source/data commit 93a63c0f9642eeb65057721d2729f2d9b40e6892; final documentation-seal head is verified after push and recorded in final local receipt
PULL_REQUEST_URL: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/9

FINAL_VERDICT: PASS_MG5_GENERATION_AND_GITHUB_PUBLICATION
NEXT_RECOMMENDED_STEP: independently generate local samples using documented command and reviewed profiles; any shower/detector phase requires a separate requested scope

Preservation: 31 historical main tracked files unchanged; only existing .gitignore/.gitattributes were narrowly updated. Main remains f7a3420155bd557e4146fd1959a60f68742ea930. PR #8 remains OPEN/DRAFT at 3eb5124f9782960afd8992559aeb4210ac308f77. No force-push or automatic merge. No figures were generated or published.

Limitations: this fixed-scale, CTEQ6L1 massless-b LO finite partonic domain is not an inclusive ATLAS background prediction, full isolated-photon NLO observable, detector-performance validation or HH sensitivity estimate. A higher-order photon study needs an explicit isolation/fragmentation treatment. Launchpad timed out; installation used pinned official Git source with upstream release-directory packaging, not a downloaded release tarball. Failed diagnostic attempts remain local.

Evidence: metadata/phase6a_mg5_github_publication.json, metadata/phase6a_mg5_run_manifest.json, sample_manifest.json, simulation/mg5/evidence/reference-validation.json, validator-tests.txt, self_service_actual_runs.json and root-ctest.txt. The source/data CI and remote proof concern the immutable tested commit; the final seal changes only reports and metadata.
