# Phase 5C storage decision

**STORAGE_ACCESS = BLOCKED; ROOT_FILE_ACQUIRED = NO.** The exact approved
302521 member is absent from the ignored local inputs and outputs. No new
ROOT transfer, remote TFile/TTree read, or research dataset acquisition was
attempted in Phase 5C. The previously observed failures do not identify a
public-storage outage or its cause.

The immutable baseline is `1c7da77fe4c852c929be39b10544220033de9fec`.
[Baseline preservation](../metadata/phase5c_baseline_manifest.json) covers
190 tracked files and 407 prior local evidence files, including original
ROOT inputs, draft figures, Phase 0 sources and Phase 5B output versions.
Only additions to the preserved CMake prefix are permitted.

## Object identity and current observations

[Official record 93922](https://opendata.cern.ch/record/93922) lists:

```text
ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
110755804 bytes; adler32:b43248ea
```

The retained record response has raw SHA-256
`750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c`.
A catalog `online` flag, filename, HTTP HEAD or ETag is metadata evidence;
none is a verified acquired file or a native schema observation. Actual
Adler-32/SHA-256, TFile readability, tree/branch types and DSID consistency
remain **NOT_VERIFIED / NOT_EVALUATED**. The 10, 100 and 10000-entry physical
stages were not executed.

[Sanitized evidence](../metadata/phase5c_sanitized_network_evidence.json)
projects the original Phase 5 receipt, four Phase 5B receipts and the new
Phase 5C documentation receipt. Raw originals remain untouched. It retains
public hostnames and observed outcomes while excluding addresses, proxy
endpoints, user paths, raw error messages and redirect queries.

IPv4 connectivity, selected Windows metadata/TLS successes, WSL TLS
timeouts, IPv6 no-route results, storage resets/timeouts and the failed
XRootD metadata operation are distinct observations. No one observation
establishes a root cause or object availability. No TLS verification was
disabled. The root:// metadata probe makes no TLS assertion.

Phase 5C attempted six new official documentation GETs once each. All
returned the sanitized error class `URLError`, with zero HTTP body bytes
and no recorded HTTP status. The underlying cause remains UNKNOWN. This
does not establish that the documents are unavailable. Route/provenance
reviews use rehashed historical official source snapshots, with dates and
applicability limits. No further attempts followed these failures.

## Accounting and stop rule

| Accounting item | Charged bytes |
| --- | ---: |
| Original Phase 5 including its earlier documentation | 1811050 |
| Four Phase 5B incremental receipts, counted once | 3491209 |
| Phase 5C six once-only documentation operations | 393216 |
| Phase 5 cumulative charge | **5695475 / 134217728** |
| Project cumulative charge | **83829497 / 268435456** |
| Phase 5C received HTTP bodies / ROOT payload | **0 / 0** |

The model charges consumed response bodies plus 65536 bytes per application
operation. Wire/control traffic, TLS exchanges and XRootD internal retries
are **UNMEASURED**; the reserve is not a hard wire cap. Remaining model
allowances are 128522253 Phase 5 and 184605959 cumulative bytes. The exact
file plus one reserve would bring the Phase 5 model charge to 116516815;
this arithmetic is not acquisition approval, transport verification or a
guarantee against additional requests or overhead.

The executed collector is archived unchanged at
`metadata/phase5c_source_evidence/collector_executed_v1.py.txt`, SHA-256
`77d73864febb1d9c929d35dcbb28318b41b4776e22477950bcf9207b605befae`.
Subsequent source hardening rejects non-HTML/empty/truncated documents and
refuses another CLI pass when the existing Phase 5C receipt is present.
It cannot accept a Phase 5C prior through the older Phase 5B accounting
adapter. A future supported access method requires an accounting-aware
replacement carrying **every** receipt forward; do not omit this pass's
393216-byte charge or reuse an older downloader's stale totals.

## Required evidence before resuming

The [prepared support request](phase5c_cern_support_request.md) is UNSENT.
Await new official evidence rather than repeat unsuccessful routes.
An alternative must identify the exact object and establish verified
transport with enforceable response-byte limits, conservative accounting,
redirect handling and immediate mismatch aborts. Research files or substitute
datasets require separate authorization and budgets.

If the authorized member is acquired, keep it in a fresh ignored local
directory. First require exact filename, raw byte count, calculated published
Adler-32 and recorded SHA-256. Then run the existing local ROOT metadata
guards, reject recovered/truncated/external-storage inputs and inventory
native types. Only afterward inspect exactly recorded 10, 100 and at most
10000 entry prefixes, checking collection consistency and native DSID values.
Reuse existing Phase 4 reconstruction; stop on any discrepancy. The existing
metadata-only guard does not verify actual DSID values until entries are read.

Passing synthetic/data-only tests cannot close Gates C/D or demonstrate
continuum physics closure. Exact-production weights, full signed pre-skim
denominators, calibrations and exposure remain separate gates even after
successful file intake. Physical normalization is disabled.
