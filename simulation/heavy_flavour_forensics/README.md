# Existing heavy-flavour forensics and background preparation

Phase6E starts from Phase6D commit
`7b1fccb41133f4f97a5277fa09efc90a1da41239`. No original event is edited,
removed, retagged or regenerated. Full LHE/HepMC/ROOT inputs and installed
generators remain in their original locations. New cards are proposals with
actual MG5 parse/diagram checks, not registered production profiles.

The actual light-jjgg source997 is the one-based997th LHE/ledger/HepMC event
and zero-based ROOT entry996. It has incoming u/g and outgoing g/u hard partons,
with no hard bottom. The preserved Pythia graph identifies the direct FSR
gluon17→b19+bbar20 branching. All571 Pythia and HepMC particle tuples map
uniquely after the actual status conversion, and all1149 mother edges agree.
Native ROOT Float_t particle/jet/photon/event fields were physically read back.
Two terminal B hadrons and the native-b jets are recorded with explicit
geometric associations and qualified hadronization ancestor sets. Missing
production positions and ambiguous sole-parent attribution remain UNKNOWN.

The selected native jet flavors remain5,2,21,21,5 and bit0 tags1,0,0,0,0.
Conditional P(at least two tags)=0.493910275786, despite the observed event
failing the double-tag selection. Hard-parton, shower-parton, heavy-hadron and
native Delphes labels are separate. Diagnostic associations do not replace
native Flavor or replay an original pseudorandom tag draw.

`scripts/source997.py --output NEW_DIRECTORY` performs installation-dependent
read-only verification. Its `--verify-evidence evidence/source997.json` mode
replays the small published derived graph and manifest without opening ROOT;
it is explicitly offline evidence replay. The latter verifies prior evidence,
not a new native readback. See the [Traditional Chinese guide](USER_GUIDE_ZH_TW.md).

`scripts/influence.py --output NEW_DIRECTORY` retains all1000 original source
events per process and the frozen Phase6D weights/selections. It calculates
expected counts, weighted yields, tag variance, source-pilot variance,
top5/top10 contributions, concentration and qualified precision information.
It separates six exclusive leading-tagged-pair types from three exclusive
event tag-origin classes. Conditional category covariance has negative
off-diagonal terms; categories cannot be treated as independent counts.
Full per-event numerical tables stay local; small summaries and the
[flavour decomposition CSV](../../metadata/phase6e_flavour_decomposition.csv)
are selected for publication.

The authoritative final light-jjgg expected count remains0.501324516614.
Source997 contributes98.5211%; the other999 contribute0.007414240828.
Removing it or rescaling a999-event mean is DIAGNOSTIC_ONLY, not a corrected
prediction, overlap subtraction or stitching rule. The concentration ratio
near1.03 and inverse squared relative-SE measure precision/concentration in
this pilot; they do not create new independent source events. There are still
1000 original source events per process.

`scripts/parse_process_cards.py` permits only whitelisted import/define/generate
commands against the retained MG5 installation. It does not export a process,
launch, integrate or generate an event. Canonical bbγj, stable-H ttH and
qqbar ZH cards pass actual tree construction at their recorded amplitude orders;
separate Z→bb and top/W trees parse. Ordinary-SM tree H→γγ is an expected
NoDiagram rejection. `higgs_contract.py` tests exactly-once Decimal BR algebra
and double-count guards without adopting physical BR defaults or supplying a
real external-LHE decay closure receipt.

Future100-event commands are documented but unexecuted. Separate explicit pilot
authorization, decay/width/BR normalization closure and applicable photon-fake
and matching/overlap models are required before physical interpretation.
Process names do not prove exclusive reconstructed final states; these samples
are not combined into an official ATLAS background prediction.

Publication is source/cards/config/tests plus small derived JSON/CSV and reports.
The payload auditor permits only new Phase6E paths and the exact three new MG5
candidate cards, caps each text file at2MiB and the full payload at6MiB, and
rejects full event tables, physical samples, vendored source, private paths,
binaries, archives and figures. Every staged/outgoing commit is inspected before
push. CI performs portable graph/numerical/normalization checks and earlier
reference regressions; it does not install or run the physics stack.

Scientific entries are the [source997 report](../../reports/phase6e_source997_forensics.md),
[flavour classification](../../reports/phase6e_heavy_flavour_classification.md),
[overlap review](../../reports/phase6e_background_overlap.md),
[new cards](../../reports/phase6e_new_process_cards.md),
[Higgs contract](../../reports/phase6e_higgs_decay_contract.md) and
[final decision](../../reports/phase6e_final_decision.md). No PDF/PNG is produced,
and no PR is merged or force-pushed by this task.
