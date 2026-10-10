# Phase 1 bounded ROOT access audit

Project: ATLAS_HH_BBGG_PUBLIC_V1. Physical inspection completed 2026-10-10 UTC.
**Access: PASS.** This applies to one checksum-verified local file, not the complete release.

## Identity established before access

The [official collision record 93915](https://opendata.cern.ch/record/93915),
[JSON index](https://opendata.cern.ch/api/records/93915), DOI
[10.7483/OPENDATA.ATLAS.GYRR.GRP3](https://doi.org/10.7483/OPENDATA.ATLAS.GYRR.GRP3),
lists 16 GamGam files. The downloader selected the smallest suitable collision ROOT file:

| Field | Recorded value |
| --- | --- |
| Filename | `ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root` |
| Official URI | `root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root` |
| HTTPS gateway | [Same EOS host and path](https://eospublic.cern.ch/eos/opendata/atlas/rucio/opendata/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root) |
| Published / received size | 17,541,818 / 17,541,818 bytes |
| Published / measured Adler-32 | `037f48e7` / `037f48e7`: PASS |
| Local SHA-256 | `01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7` |
| Official record snapshot | 15,864 bytes; SHA-256 `449cebdcffa9b6dfb527ec41519e671fee5e4d4292133f3bf88b99a22607ecb9` |

The HTTPS URL is a derivation from the official `root://` URI, not a separately listed
dataset. Gateway size and the published checksum establish the correspondence. The
identity, size, checksum and URL were saved before HEAD or file-body requests.

## Access, range support and limits

The first EOS HEAD failed system certificate verification; no ROOT bytes were read.
The [official CERN CA download page](https://ca.cern.ch/cafiles/certificates/Download.aspx?ca=grid)
provides CERN Root CA 2 and CERN Grid CA (1). These were fetched using verified HTTPS
and added to a process-local SSL context. Certificate and hostname verification stayed
enabled for HTTPS; system trust and other conda environments were unchanged. CA hashes
and repeated attempts are in [root_access_ledger.json](root_access_ledger.json).

The verified HTTPS gateway returned a 307 redirect to an official CERN EOS storage
node on HTTP port 8443. The downloader accepted only the same exact object path on
`st-*.cern.ch:8443`, limited the redirect count, and redacted the temporary EOS
capability query. **The storage-node body transfer used plaintext HTTP.** The
published Adler-32 was verified afterward; it is a consistency check, not a
cryptographic authenticity proof. The local SHA-256 supplies a precise reproducibility
identity; it is not a publisher-signed SHA-256. No private/user credential was used.

The storage node answered `Range: bytes=0-0` with **HTTP 206**,
`Content-Range: bytes 0-0/17541818`, and exactly one response-body byte. A subsequent
bounded full GET returned HTTP 200, the exact indexed size, and matching checksum.
Only this 16.73 MiB sample was retrieved; no other dataset file was downloaded.

| Accounting | Bytes |
| --- | ---: |
| ROOT sample body | 17,541,818 |
| One-byte range probe | 1 |
| Record metadata | 15,864 |
| Three pairs of CA certificate responses, including retries | 15,471 |
| Total application-measured HTTP response bodies | **17,573,154** |
| Downloader charge: bodies + 64 KiB for each of 18 attempted requests | 18,752,802 |
| Two diagnostic curl HEAD requests: zero body, additional protocol reserve | 131,072 |
| Total charged including diagnostics | **18,883,874** |
| Cumulative budget | **268,435,456 (256 MiB)** |
| Single-file ceiling | 67,108,864 (64 MiB) |
| Remote ROOT operations | **0** |

The strict application budget covers response-body reads plus a conservative request
reserve. It persists across retries; `--resume` does not reset it. Transfer guards
reject advertised oversize, compressed representations, truncation, unexpected hosts,
checksum mismatch, and attempts exceeding the remaining allowance. An unadvertised
oversize can consume one reserved probe byte before stopping. Failure prohibits
physical inspection. Error/redirect bodies are closed without application reads.
**TLS/TCP packet-level wire bytes were not measured**; protocol reserves must not be
presented as a measured wire count. This limitation also covers server-side buffers.

## Local physical inspection

ROOT opened the local regular file with `TFile::Open(..., "READ")`; remote URLs,
friend trees, and external branch storage are refused. Metadata inspection found tree
`analysis` and 119 top-level branches. Only the 25 requested fields were read, with
typed native readers and an enforced entry limit of 10. ROOT may decompress local
baskets containing more entries; it does not request further network data and the
application inspects only entries 0 through 9.

The first schema-only run explicitly failed on documented `std::vector` versus actual
RVec types and inspected **zero entries**. Its ignored CSV and diagnostic summary were
preserved. Native RVec readers and synthetic fixtures were then added; the successful
run inspected exactly 10 entries. Input SHA-256 before/after was identical. No
selection, reconstruction, yield, histogram or statistical result was computed.

## Reproduction

Activate the existing `atlas-hh-root` environment, then run from the repository:

```bash
set -euo pipefail
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate atlas-hh-root
cd /mnt/c/HH
build="$HOME/build/atlas_hh_phase1_$(date -u +%Y%m%dT%H%M%SZ)"
bash scripts/validate_phase1.sh "$build"
audit=".local/phase1_reproduce_$(date -u +%Y%m%dT%H%M%SZ)"
python3 -B scripts/fetch_phase1_sample.py --output-dir "$audit"
sample="$audit/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root"
printf '%s  %s\n' '01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7' "$sample" | sha256sum --check
"$build/inspect_root_schema" \
  --input "$audit/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root" \
  --manifest "$audit/schema.csv" --summary "$audit/schema.txt" \
  --max-entries 10 \
  --evidence 'record93915;ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root;sha256=01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7;ROOT6.40.04'
sha256sum "$audit/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root"
```

The command checks SHA-256 against the pinned identity before invoking the inspector;
the downloader independently verifies the published checksum. For an interrupted
attempt use the **same directory** with `--resume`, preserving its cumulative ledger;
do not create another directory to evade the budget. Completed sample/output files
are not overwritten. Reinspection of an already downloaded local sample needs no
network. A later mutable record or different file hash is new evidence requiring
review, not a silent replacement of this audit. New independent reproductions have
their own explicitly bounded audit ledger. Raw samples/logs remain ignored locally.
