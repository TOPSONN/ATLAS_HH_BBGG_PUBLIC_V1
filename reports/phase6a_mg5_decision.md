# Phase 6A V2 setup and reference decision

Setup, physics/cards, actual100/1000 generation, independent validation, cross-section evidence and the final actual100-event self-service command passed (A-H). Remote reference publication and documentation/Git/CI integrity also passed (I-J): both actual GitHub LHE blobs were downloaded and independently validated; the full remote tree matched and GitHub CI completed successfully with 74 tests on source/reference payload commit b17bec4012d56f0bb2f5354bca15ba6ebf3c26f9. No production PASS is asserted.

The independent branch starts at live origin/main f7a3420155bd557e4146fd1959a60f68742ea930. The historical Phase5 branch/PR8 and Phase6A PR9 are preserved. Existing ROOT/data/selection/history files are unchanged. Explicit stage and every outgoing-commit audits are required before each push; no new/modified PDF/PNG was generated or included. PRs are never automatically merged.

PRODUCTION_1M_STATUS: NOT_EXECUTED_BY_DESIGN. Future single or independent-batch production, its runtime/disk benchmark and its Release publication remain NOT_EVALUATED. The next user action after reviewing this PR and the guide is a local production dry-run, then a manually chosen generation time.

PR: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/10 (main target, OPEN, no automatic merge). CI source-payload evidence: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/38237083358. The final documentation seal is reverified remotely after push; future production and large Release publication remain NOT_EVALUATED.
