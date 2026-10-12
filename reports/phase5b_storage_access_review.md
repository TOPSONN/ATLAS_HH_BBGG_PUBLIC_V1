# Phase 5B bounded CERN storage review

**CONTINUUM_ACCESS = BLOCKED_NETWORK; FINAL_VERDICT = BLOCKED_STORAGE_ACCESS.**
The single authorized DSID302521 file was not acquired. Fresh diagnostics
establish reachable IPv4 TCP endpoints and successful Windows metadata TLS,
but do not establish a usable storage payload route. The exact official
XRootD open/stat attempt timed out after15 seconds. No ROOT body, final file,
partial file, native event or physical continuum distribution was produced.

## Baseline, exact identity and preservation

The starting local branch, origin branch and PR#8 head were all
`e131de92897b75185981ec2c5ce1c722e9ada6c3`. PR#8 remained OPEN/DRAFT with base
`codex/phase4-mc-truth-validation` at
`704045c6c18c313114e3ab41019e46c70beb086b`; no PR was merged. The initial tree
was clean. GitHub had **NO_CHECKS**, which is not successful CI.

The new [preservation manifest](../metadata/phase5b_baseline_manifest.json)
checks164 baseline tracked files plus269 immutable local files. Known text
paths permit only CRLF-to-LF canonicalization; historical binary figures and
unclassified paths use **raw-byte identity**. CMake preserves the full old
text as a prefix and adds an opt-in Phase5B block. Historical reports,
selection, ROOT inputs, Phase4 recovery and Phase5 outputs remain unchanged.
An initial new preservation draft that used blanket LF normalization was
retained locally, then replaced by this stronger binary-aware manifest.

The original failed access receipt is immutable:
`.local/phase5_access_20261012/access.json`, raw SHA-256
`be764a03f335e9cf238b9e8f1f67a8fd82bfa07aeb2ae145f490e8d6547ab134`.
The old published ledger remains
`9e8a88178bc2d2f5717d71b1e7f9d59f07eb46be0e96c185c6e2ba58997d5ece`
after its documented LF text canonicalization. Neither receipt was amended
to incorporate the new attempts or to promote a historical blocker to PASS.

The fresh [official record API](https://opendata.cern.ch/api/records/93922)
response SHA-256 is
`750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c`.
The record names exactly one authorized target:

```text
ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
size110755804 bytes; published adler32:b43248ea
root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
```

These are source-identity facts, not acquired-file checksum verification.
The new [transfer audit](../metadata/phase5b_transfer_audit.json) binds exact
raw receipt/source hashes, operation outcomes and preserved charges.

## Actual metadata-only diagnostics

| Surface | DNS/TCP | Verified TLS / application result |
| --- | --- | --- |
| Windows IPv4 | DNS and probed443/1094/8443 TCP succeeded | Open Data TLS1.3, GitLab TLS1.3 and CA TLS1.2 succeeded |
| Windows EOS default trust | TCP443 succeeded | Default certificate verification failed; verification was not disabled |
| Windows scoped CERN trust | Pinned CA documents acquired with validated HTTPS | Exact EOS HEAD200, Content-Length110755804, ETag includesb43248ea |
| WSL IPv4 | DNS and all selected TCP endpoints succeeded | All directly probed443 TLS handshakes timed out |
| WSL IPv6 | CERN addresses resolved | Probed TCP failed with errno101, no route |
| Official API exact-file HEAD | Metadata request only | Timed out, no response body consumed |
| ROOT XRootD exact-URI open/stat | One attempt;15s process timeout | BLOCKED_XROOTD_METADATA, no GetSize result and no payload reads |

The redirect storage hosts observed in the old receipt were tested for TCP
reachability only. That success does not establish working HTTP, HTTPS,
authorization, an XRootD handshake or bulk throughput. Windows returned no
IPv6 address in its chosen results; that is not a global claim that CERN lacks
IPv6. Python's configured HTTP proxy inventory was empty on both surfaces;
it does not rule out a transparent network intermediary. These observations
localize behavior but do not identify a firewall, service outage or security
cause. Repeating the previous reset/timeout payload routes has no evidence-based
advantage, so no new bulk request was sent.

The installed environment has ROOT's XRootD feature and client libraries;
`xrdfs`, `xrdcp` and Python XRootD bindings were absent. An initial direct
`RRawFileNetXNG` link failed on `fcntl64@GLIBC_2.28` in the installed client
dependency. That failed source is retained locally. The final tiny helper
uses the existing `RRawFile::Create` factory and ROOT dynamic plugin loading,
with buffering disabled, the exact fixed official URI and `GetSize()` only.
It compiled with the existing conda compiler and without replacing packages,
adding linker-error suppression or introducing remote TFile/TTree operations.
The timed-out process was terminated; stderr was discarded because XRootD
exceptions can contain redirect capability URLs. No certificate verification
was disabled. The public `root://` metadata protocol makes **no TLS claim**.

## Accounting and its actual limits

| Preserved / new increment | Charged bytes |
| --- | ---: |
| Historical cumulative before original Phase5 |78,134,022|
| Original Phase5 including documentation |1,811,050|
| New Windows network diagnostics:17 operations |1,114,112|
| New WSL network diagnostics:24 operations |1,572,864|
| New Windows source metadata:6 operations |738,697|
| New XRootD metadata:1 operation |65,536|
| **New Phase5B increment** |**3,491,209**|
| **Phase5 charged total** |**5,302,259 /134,217,728**|
| **Historical cumulative charged total** |**83,436,281 /268,435,456**|

New consumed HTTP metadata bodies total345,481 bytes: record337,923;
CA documents1,709 and3,448; job JSON2,401. The48 new application diagnostic
operations reserve48*65,536=3,145,728 bytes, including failed attempts.
Own increments are counted once; inherited receipt summaries are not added
again. ROOT payload consumed is **0**. Control traffic, encrypted wire bytes,
DNS retransmissions, XRootD internal retries and socket buffering are
**UNMEASURED**. Reserves are accounting allowances rather than measurements
or a hard network-wire cap. The XRootD receipt's legacy
`remote_ROOT_operations=0` denotes no remote ROOT-object/event operation;
its separately logged open/stat operation count is1.

The approved body-plus-reserve ceilings are respected. This does not prove a
metered XRootD **bulk** implementation: no bulk client was developed or used
because metadata access itself failed. No unmetered xrdcp, TFile::Cp, remote
ROOT streaming, partial retry or alternate file was attempted.

## Executed source versus hardened tooling

The three HTTP/DNS/TCP/TLS receipts were executed using the preserved v1
diagnostic source, raw SHA-256
`a3d51d5861f7ae6988532a047ccf73a8c8d881ee8070a1ad91cf02b02e3ffb69`.
Their actual byte/operation arithmetic was independently checked. Subsequent
mock tests exposed validation gaps for malformed prior receipts and caller
caps/endpoints. The hardened published source rejects negative/noninteger/bool
amounts, incomplete/duplicate prior chains, nonexact metadata endpoints,
ROOT GET, unsafe output names and unverified TLS contexts before any request.
It was **not used retroactively** to make those live requests. Both initial
failed mock results and final40/40 mock results remain local and hash-bound
in the quality evidence. These are engineering checks, not successful storage
or physical ROOT tests.

The actual metadata additionally acquired an official DSID302521 job at the
API-reported immutable commit. See the [filter](phase5b_generator_filter_review.md)
and [weight](phase5b_weight_provenance.md) reviews. It improves source evidence;
mapping to exact e4045/FEB2025, truth-pair eligibility, nominal weight index
and complete signed pre-skim denominator remain unverified.

## Recommended official escalation

Prepare a support request through the contact channel of the
[CERN Open Data portal](https://opendata.cern.ch/record/93922).
Include public record93922, the exact filename/official URI, published
size/checksum, sanitized UTC receipt times, Windows-vs-WSL observations,
successful HEAD metadata and the15s public XRootD stat timeout. Ask whether
this specific file's storage redirect/public XRootD endpoint is healthy and
which official bounded transport is supported. Do not attach redirect query
tokens, proxy credentials or raw client exception URLs. This is a recommendation;
**no support message was sent**. A later transfer must preserve these charges,
validate its meter before payload reads and require all physical gates anew.
