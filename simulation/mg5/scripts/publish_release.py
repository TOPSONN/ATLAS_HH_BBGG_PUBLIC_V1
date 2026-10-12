#!/usr/bin/env python3
"""Preflight selected completed samples; upload only on explicit --publish.

Draft-only release creation. No Git commits, automatic tagging of a local
checkout, release publication, LFS setup, or automatic release replacement.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from validate_sample import validate_run

REPOSITORY = "TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1"
ASSET_LIMIT_BYTES = 2 * 1024**3  # GitHub requires each asset strictly under 2 GiB.
ASSET_COUNT_LIMIT = 1000
SOURCE = "https://github.com/mg5amcnlo/mg5amcnlo"
REPO = Path(__file__).resolve().parents[3]
LIMIT_DOCUMENTATION = "https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases"
PRIVATE = re.compile(
    r"(?:/home/[^\s<>\"']+|/mnt/[a-z]/[^\s<>\"']+|[A-Za-z]:[\\/](?:Users|HH)[\\/]"
    r"|BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|(?i:api[_-]?key|access[_-]?token|password)\s*[:=]\s*[^\s#]+)"
)
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}")


class PublicationError(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise PublicationError(message)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")
    check(PRIVATE.search(data.decode("utf-8")) is None, "public metadata contains private paths or credentials")
    return data


def check_public_header(path):
    """Reject private information without editing any LHE bytes."""
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as stream:
        header = stream.read(4 * 1024 * 1024)
    check("<init>" in header, "LHE header exceeds publication safety bound")
    check(PRIVATE.search(header.split("<init>", 1)[0]) is None,
          "LHE banner contains private paths or credentials; preserve it locally and generate a clean new run")


def safe_count(value):
    check(isinstance(value, int) and not isinstance(value, bool) and value > 0,
          "actual event count must be a positive integer")
    return value


def build_plan(runs, tag, expected_events=None):
    check(NAME.fullmatch(tag) is not None, "tag must contain only letters, digits, dots, hyphens or underscores")
    check(bool(runs), "at least one completed run is required")
    assets, samples, seen_names, seen_content = [], [], set(), set()
    for run in runs:
        run = Path(run).resolve()
        label = run.name
        check(NAME.fullmatch(label) is not None, "run directory name is unsuitable for a public asset name")
        check(label not in seen_names, "duplicate run directory names")
        seen_names.add(label)
        result = validate_run(run, max_file_gb=2, max_decompressed_gb=100)
        check(result.get("validation_status") == "PASS", "sample did not pass independent validation")
        manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
        check(manifest.get("status") == "PASS", "only completed PASS runs can be released")
        count = safe_count(result["actual_events"])
        check(count == manifest["events_requested"], "requested and actual event counts differ")
        event_digest = result["event_content_sha256"]
        check(event_digest not in seen_content, "duplicate event content would double-count a sample")
        seen_content.add(event_digest)
        sample = run / manifest["lhe_gz"]
        check(sample.name == "sample.lhe.gz" and sample.parent == run,
              "release input must be the run's canonical sample.lhe.gz")
        size = sample.stat().st_size
        check(0 < size < ASSET_LIMIT_BYTES, "LHE asset must be nonempty and strictly smaller than 2 GiB")
        check_public_header(sample)
        summary = {
            "sample_id": label, "actual_events": count,
            "requested_events": manifest["events_requested"],
            "physics_process": manifest["process"], "validation_profile": manifest["profile"],
            "perturbative_order": "LO tree level", "mg5_version": result["mg5_version"],
            "mg5_source_commit": manifest["mg5_source_commit"], "mg5_source_url": SOURCE,
            "sqrt_s_gev": manifest["sqrt_s_gev"], "random_seed": manifest["random_seed"],
            "cross_section_pb": result["cross_section_pb"],
            "cross_section_uncertainty_pb": result["cross_section_uncertainty_pb"],
            "idwtup": result["idwtup"], "pdf_ids": result["pdf_ids"],
            "negative_weight_count": result["negative_weight_count"],
            "zero_weight_count": result["zero_weight_count"],
            "compressed_file_sha256": result["compressed_file_sha256"],
            "decompressed_file_sha256": result["decompressed_file_sha256"],
            "event_content_sha256": event_digest, "card_hashes": manifest["card_hashes"],
            "validation_status": "PASS", "sample_asset": label + ".lhe.gz",
        }
        cards = {}
        for name in ("proc_card_mg5.dat", "run_card.dat", "param_card.dat"):
            text = (run / "cards" / name).read_text(encoding="utf-8")
            check(PRIVATE.search(text) is None, "generator card contains private paths or credentials")
            cards[name] = text
        current_hash = file_hash(sample)
        check(current_hash == result["compressed_file_sha256"], "sample changed after independent validation")
        assets.append({"name": label + ".lhe.gz", "source": sample,
                       "size_bytes": size, "sha256": current_hash})
        for suffix, content in ((".metadata.json", summary), (".cards.json", cards)):
            data = json_bytes(content)
            assets.append({"name": label + suffix, "data": data,
                           "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        samples.append(summary)
    total = sum(sample["actual_events"] for sample in samples)
    if expected_events is not None:
        check(safe_count(expected_events) == total, "sum of independently validated event counts does not meet --expected-events")
    public = {"schema_version": 1, "repository": REPOSITORY, "tag": tag,
              "status": "VALIDATED_LOCAL_RELEASE_PLAN", "actual_events_total": total,
              "cross_section_combination": "No sum: each independent integration remains per sample",
              "samples": samples, "assets": [{k: a[k] for k in ("name", "size_bytes", "sha256")} for a in assets]}
    data = json_bytes(public)
    assets.append({"name": "release_manifest.json", "data": data,
                   "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    checksums = "".join(a["sha256"] + "  " + a["name"] + "\n" for a in assets).encode("ascii")
    assets.append({"name": "SHA256SUMS", "data": checksums,
                   "size_bytes": len(checksums), "sha256": hashlib.sha256(checksums).hexdigest()})
    check(len(assets) <= ASSET_COUNT_LIMIT, "release exceeds GitHub's 1000-asset limit")
    check(all(0 < a["size_bytes"] < ASSET_LIMIT_BYTES for a in assets), "invalid or oversized release asset")
    return public, assets


def run_gh(arguments, **kwargs):
    result = subprocess.run(["gh", *arguments], text=True, capture_output=True,
                            timeout=7200, **kwargs)
    check(result.returncode == 0, "GitHub CLI operation failed; inspect the local receipt and GitHub draft before retrying")
    return result.stdout


def publish_plan(plan, assets, stage, target):
    """Actual network operations; only called after explicit --publish."""
    check(re.fullmatch(r"[0-9a-fA-F]{40}", target or "") is not None,
          "--publish requires --target with an explicit full source commit SHA")
    run_gh(["auth", "status", "--hostname", "github.com"])
    remote = json.loads(run_gh(["api", f"repos/{REPOSITORY}/commits/{target}"]))
    check(remote["sha"].lower() == target.lower(), "target commit did not resolve exactly on GitHub")
    tags = json.loads(run_gh(["api", f"repos/{REPOSITORY}/git/matching-refs/tags/{plan['tag']}"]))
    check(not any(item["ref"] == "refs/tags/" + plan["tag"] for item in tags),
          "tag already exists; choose a new release tag instead of reusing or moving it")
    releases = json.loads(run_gh(["api", "--paginate", "--slurp",
                                 f"repos/{REPOSITORY}/releases?per_page=100"]))
    check(not any(item["tag_name"] == plan["tag"] for page in releases for item in page),
          "release tag already exists; existing releases will not be overwritten")
    check(not stage.exists(), "release staging directory already exists; choose a new --stage")
    stage.mkdir(parents=True)
    for asset in assets:
        destination = stage / asset["name"]
        if "source" in asset:
            shutil.copyfile(asset["source"], destination)
        else:
            destination.write_bytes(asset["data"])
        check(destination.stat().st_size == asset["size_bytes"] and file_hash(destination) == asset["sha256"],
              "staged asset changed during preparation")
    notes = stage / "notes.md"
    notes.write_text(
        "Validated MG5 LO parton-level samples.\n\n"
        f"Actual independently validated events: {plan['actual_events_total']}.\n"
        "Exact generator cards, per-sample cross sections and SHA-256 hashes are included.\n"
        "Independent integrations of the same process do not have additive cross sections.\n"
        "This release remains a draft for user review.\n", encoding="utf-8")
    receipt = {"status": "UPLOAD_IN_PROGRESS", "repository": REPOSITORY,
               "tag": plan["tag"], "target": target, "draft": True,
               "expected_assets": [{k: a[k] for k in ("name", "size_bytes", "sha256")} for a in assets],
               "publication_verified": False}
    receipt_path = stage / "release_receipt.json"
    receipt_path.write_bytes(json_bytes(receipt))
    try:
        run_gh(["release", "create", plan["tag"], *[str(stage / a["name"]) for a in assets],
                "--repo", REPOSITORY, "--draft", "--latest=false", "--target", target,
                "--title", plan["tag"], "--notes-file", str(notes)])
        remote = json.loads(run_gh(["release", "view", plan["tag"], "--repo", REPOSITORY,
                                   "--json", "assets,isDraft,url,tagName,targetCommitish"]))
        check(remote["isDraft"] is True and remote["tagName"] == plan["tag"], "release is not the expected draft")
        # A draft can defer creating the tag until publication. Verify its exact
        # target rather than assuming the tag ref already exists.
        check(remote["targetCommitish"].lower() == target.lower(), "draft target differs from the requested source commit")
        remote_assets = {asset["name"]: asset for asset in remote["assets"]}
        check(set(remote_assets) == {asset["name"] for asset in assets}, "uploaded asset names do not match the plan")
        verify_dir = stage / "remote_verification"
        verify_dir.mkdir()
        verified = []
        for asset in assets:
            check(remote_assets[asset["name"]]["size"] == asset["size_bytes"], "remote asset size differs")
            run_gh(["release", "download", plan["tag"], "--repo", REPOSITORY,
                    "--pattern", asset["name"], "--dir", str(verify_dir)])
            downloaded = verify_dir / asset["name"]
            check(file_hash(downloaded) == asset["sha256"], "downloaded asset SHA-256 differs")
            verified.append({k: asset[k] for k in ("name", "size_bytes", "sha256")})
        receipt.update(status="DRAFT_UPLOADED_VERIFIED", url=remote["url"],
                       publication_verified=True, verified_assets=verified)
    except (PublicationError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        receipt.update(status="PARTIAL_OR_FAILED_DRAFT_UPLOAD", error=str(exc),
                       publication_verified=False,
                       next_action="Inspect the draft and local receipt; no automatic deletion, overwrite, or publication")
        receipt_path.write_bytes(json_bytes(receipt))
        raise PublicationError("draft upload was not fully verified; a partial draft may exist") from exc
    receipt_path.write_bytes(json_bytes(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True,
                        help="completed local run directory; repeat for independent batches")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--expected-events", type=int, help="required for publication; total validated event count")
    parser.add_argument("--target", help="full source commit already present on GitHub; required for --publish")
    parser.add_argument("--stage", type=Path, help="new staging directory, default ~/simulations/mg5_releases/TAG")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="read-only local preflight (also the default)")
    mode.add_argument("--publish", action="store_true", help="explicitly create and upload a GitHub draft, then verify downloaded assets")
    args = parser.parse_args()
    try:
        check(not args.publish or args.expected_events is not None, "--publish requires --expected-events")
        plan, assets = build_plan(args.run, args.tag, args.expected_events)
        if args.publish:
            stage = (args.stage or Path.home() / "simulations" / "mg5_releases" / args.tag).resolve()
            check(not any(stage == run.resolve() or run.resolve() in stage.parents for run in args.run),
                  "release staging must not be inside an input run")
            check(not stage.is_relative_to(REPO), "release staging must stay outside the Git repository")
            result = publish_plan(plan, assets, stage, args.target)
        else:
            result = {"status": "PREFLIGHT_PASS_NO_UPLOAD", "actual_events_total": plan["actual_events_total"],
                      "repository": REPOSITORY, "tag": args.tag, "draft": True,
                      "assets": [{k: a[k] for k in ("name", "size_bytes", "sha256")} for a in assets],
                      "asset_limit_bytes_exclusive": ASSET_LIMIT_BYTES,
                      "limit_documentation": LIMIT_DOCUMENTATION,
                      "production_publication": "NOT_EVALUATED"}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (PublicationError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
