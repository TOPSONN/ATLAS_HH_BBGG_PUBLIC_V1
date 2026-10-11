# ATLAS_HH_BBGG_PUBLIC_V1 agent instructions

Use the existing ROOT 6.40.04 / C++20 environment and preserve historical data,
selection definitions, scientific reports, and Git history. Phase 4 starts from
the Phase 3 feature head and must remain independent of plotting PR #6.
Existing plotting contracts still apply when working on their branches.

## FINAL_FIGURE_APPROVAL_BEFORE_PUSH

Effective immediately, generated PDF and PNG figures stay local until the user
explicitly approves their final versions. Source development, tests, commits and
normal source-code PR workflows may continue. Exclude all unapproved figures,
including modifications to tracked figures, from staging and commits; stage
explicit source and report paths.

Before every push inspect both staged files and every outgoing commit payload,
including intermediate versions. No unapproved PDF or PNG may be included.
Approval applies to exact final versions (paths and SHA-256 hashes) and their
scientific captions/provenance. Regeneration or caption/provenance changes require
renewed approval. Successful CTest or visual QA never constitutes user approval.

Keep distinct local versions for visual comparison. Report figure status as
LOCAL_DRAFT, QA_PASSED, AWAITING_USER_APPROVAL, APPROVED_FOR_PUSH, or PUSHED.
Only approved final figures may be committed and pushed. Preserve historical
scientific results and previously published artifacts; prior publication does
not approve a new version. Do not automatically merge pull requests.
