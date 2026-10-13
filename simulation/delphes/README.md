# Independent ATLAS-like Delphes methods study

This module uses an explicitly study-defined copy of the official Delphes 3.5.1
ATLAS card. It is `FAST_SIM_ATLAS_LIKE`, `NOT_OFFICIAL_ATLAS`, with no current
ATLAS calibration, complete-background or HH-sensitivity claim. Existing MG5,
Pythia, ROOT readers and historical reference bytes are preserved.

The exact upstream card/tag/source identity and source semantics are in
[card_source_review.json](evidence/card_source_review.json). The study changes
truth/reco anti-kT radii from 0.6 to 0.4 and the parton-flavour cone from 0.5 to 0.4,
retaining the upstream response/isolation/JES/tagging functions. The canonical
card hash is `cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47`.
An explicit global RNG seed is genuinely read by the pinned Delphes framework;
exact per-process runtime cards use 610301/610302/610303 and retain both canonical
and runtime hashes. No pileup module is introduced.

The parton-cone flavour includes eligible shower partons, rather than only
original hard partons or hadron ghost association. BTag is a sampled bit 0,
not a continuous DL1/GN2 score. Electron/photon/jet uniqueness uses shared
candidate constituents, not a geometric overlap cut. These choices and limits
are documented in the [detector-card report](../../reports/phase6c_detector_card.md)
and [b-tag report](../../reports/phase6c_btag_validation.md).

Physical processing uses the existing 1000-event HepMC3 runs locally, and the
separate published 100-event inputs for small detector references. Shared input
events are never counted as independent hard statistics. Generator-normalized
weights, source indices/hashes and Pythia ancestry require a validated sidecar
when native Delphes ROOT does not retain every field.

The pipeline has an independent Delphes ROOT adapter; it does not reinterpret
the native `Delphes` tree as the existing ATLAS educational `analysis` tree.
Photon and jet response diagnostics, raw/source-weighted cutflows and per-jet
tag fractions have explicit study definitions and statistical limits.

Personal ROOT output stays outside Git. Selected actual 100-event ROOT files
may be published only after compatible native ROOT/Delphes readback, bounded
size and exact-provenance checks. Portable CI can verify ROOT magic, hashes,
cards/manifests and metadata correspondence; this is distinct from physical
ROOT/physics validation. No personal run triggers a commit, push or release.
Unapproved PDF/PNG figures remain local.

The assigned source/card review is complete. The unmodified official isolated
installation passed ROOT 6.40.04/C++20 ABI/interface checks. The complete
controller physically passed Stage A 10 bbgg inputs, Stage B 100 per process
and Stage C 1000 per process, with all native counters complete and zero invalid
or skipped inputs. Independent PyROOT readback passed all seven runs. Bundled
Tcl/FastJet are used, with ROOT libraries loaded from the verified environment.
The three Stage B ROOT files pass the strict privacy/signature/size guard.
Actual selected-copy preparation and portable integrity passed all three
references. [Draft PR #13](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/13)
is OPEN/DRAFT against the Phase6B branch. At verified source/data snapshot
`1c20514c44db624dd926ed058deca39c1c41fbfb`, actual GitHub ROOT downloads match
all three hashes/sizes and the whole 334-file blob tree; all four relevant
push/PR CI runs succeeded. The exact bounded receipt is
[github_publication.json](evidence/github_publication.json), with workflow links
in the [publication report](../../reports/phase6c_github_publication.md).
The later report-only seal receives a separate final-HEAD check recorded in
the PR body/final handoff; this document does not claim its own future hash.
Historical PR #9 remains OPEN/ready for review; #11 and #12 remain OPEN/DRAFT.
The [native receipts](evidence/native_runs.json),
[independent readback](evidence/independent_readback.json) and
[reproducibility evidence](evidence/reproducibility.json) distinguish physical
processing, independent auditing and equal scientific content from ROOT binary
identity. The repeated 10-event run adds no hard statistics.
The [Traditional Chinese guide](USER_GUIDE_ZH_TW.md) supplies complete commands;
[binned tagging evidence](evidence/btag_binned_statistics.json) uses Stage C only.

The [official 3.5.1 repository](https://github.com/delphes/delphes/tree/3.5.1)
and the distributed GPLv3-or-later license apply to the upstream and derivative
cards. The unmodified license is retained in
[UPSTREAM_LICENSE_GPL3.txt](cards/UPSTREAM_LICENSE_GPL3.txt).
