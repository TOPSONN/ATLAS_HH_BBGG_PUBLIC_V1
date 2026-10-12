# Phase 5C CERN support request

Status: **PREPARED / UNSENT**. This document does not authorize sending email.
The evidence attachment is [the sanitized network receipt](../metadata/phase5c_sanitized_network_evidence.json).
Historical raw receipts remain local and unchanged; credentials, private
network details, resolved addresses and redirect queries are excluded.

## Draft email

To: atlas-outreach-opendata-support@cern.ch

Subject: Public GamGam record 93922 / DSID 302521: storage access failures from Windows and WSL

Dear ATLAS Open Data support,

We are conducting a bounded public-data methods study and cannot acquire
one member of [CERN Open Data record 93922](https://opendata.cern.ch/record/93922).
Could you help confirm its availability and a supported access procedure?

```text
DSID: 302521
File: ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
Published size: 110755804 bytes
Published checksum: adler32:b43248ea
HTTPS origin: https://eospublic.cern.ch/eos/opendata/atlas/rucio/opendata/
XRootD origin: root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/
```

Our observations on 2026-10-12 UTC are:

- Windows retrieved the record metadata successfully. An EOS HEAD request
  returned HTTP 200 with the expected size/checksum headers. These responses
  do not establish that the complete object can be read.
- IPv4 DNS and TCP connectivity to the probed public services succeeded.
  Windows validated TLS to the CERN CA, Open Data and GitLab endpoints.
  The default Windows EOS trust check failed certificate verification; a
  separately scoped check using locally pinned CERN CA material succeeded.
- Ubuntu WSL resolved IPv4/IPv6 addresses. IPv4 TCP connections succeeded,
  but the probed HTTPS TLS handshakes timed out. IPv6 TCP attempts reported
  errno 101, no route. These observations do not identify a server, firewall
  or proxy cause.
- Earlier redirected storage connections reset on Windows or timed out on
  WSL. The observed public storage hosts were st-096-dd904134.cern.ch and
  st-120-100gb-bknoxg.cern.ch, port 8443. Redirect capability queries have
  been removed from this request and the published evidence.
- One metadata-only XRootD open/stat request to the exact public object
  timed out after 15 seconds. GetSize did not complete; no event read was
  attempted. This root:// observation makes no TLS claim.
- No ROOT payload bytes or final/partial ROOT file have been acquired.
  Further attempts on these failing transport paths have stopped.

Could you please advise:

1. Is this exact file currently available and readable from outside CERN?
2. Is there a supported alternative endpoint or documented download method
   for this member, retaining its published identity and checksum?
3. What HTTPS or XRootD procedure, trust configuration and client settings
   do you recommend for external Windows/Ubuntu WSL users?
4. Is there a known storage or redirect issue affecting this object or
   these endpoints? If so, is there an expected resolution or workaround?
5. Can the supported method enforce a response-byte limit before acquisition?
   We must preserve an approved 128 MiB Phase 5 and 256 MiB cumulative budget.

The attached sanitized receipt distinguishes HTTP body bytes from reserved
operation charges. Those charges are application bookkeeping, not measured
wire traffic. We have not disabled TLS verification or performed a bulk
retry. Successful metadata alone has not been reported as successful input
or physics validation.

Thank you for your help.

## Delivery and scope

The draft has **not been sent**. No mail or messaging tool was called.
Send only after separate user authorization. A support reply is new evidence;
it must be checked for exact member identity, verified TLS where applicable,
metered transport and all historical charges before any resumed transfer.
No new dataset, physical normalization, research-file acquisition, HH fit
or signal extraction is implied by preparing this request.
