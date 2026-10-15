# Phase7A environment and Git preservation

Base is PR #18, OPEN/DRAFT, `codex/phase6g-backgrounds-b04-b05-b06-1k`,
`64353adfbbd3a28b13ddbdf761896c0a3fc6e680`, fetched and verified before editing.
New independent branch: `codex/phase7a-ggf-hh-sm-loop-readiness`; target is the
Phase6G branch. PR #17 remains an independent sibling; no merges or force push.

Actual retained identities: MG5 3.5.16, Pythia 8.317, HepMC3 3.3.1, Delphes 3.5.1,
ROOT 6.40.04/C++20. Full installed source/library/header/ABI identities were
verified before work and found unchanged afterward. Existing conda registrations
were read, including the retained ROOT and MG5 environments. No reinstall.
Numerical source copies and compilation remain private, outside Git.

Final fixed-point attempt: 139.836 seconds,
116130647 scratch bytes, sampled peak process-tree RSS
917192704 bytes; one worker, 2h/5GiB cap.
Instantaneous unsampled peaks and future production costs remain UNKNOWN.
Source/evidence only. No PDF/PNG, sample, release, LFS or vendor publication.
See `simulation/hh_signal/evidence/environment_preservation.json`.
