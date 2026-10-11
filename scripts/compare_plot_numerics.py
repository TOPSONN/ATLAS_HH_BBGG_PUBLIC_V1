"""Independent read-only identity audit for the eleven Phase 2/3 TH1D/display pairs.

This is a bounded project contract, not a universal plotting comparator.
Run with the already installed atlas-hh-root PyROOT environment. This program
opens only per-figure native histogram/graph ROOT files in READ mode. It does
not create figures, inspect collision event trees, or modify authoring inputs.
Styling, canvas dimensions, standard version and caption additions may change;
existing scientific metadata and all stored numeric source/display values may
not change. A nonzero exit status denotes a missing or different value.
"""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

PLOTS = {
    "phase2": (
        "deltaR_gg", "jet_eta", "jet_pt", "m_gg", "m_jj",
        "photon_eta", "photon_pt",
    ),
    "phase3": (
        "jet_pt_selected", "m_gg_preselection", "m_jj_preselection",
        "photon_pt_selected",
    ),
}

SCIENCE_FIELDS = (
    "root_version", "sample_kind", "record", "period", "selection",
    "unit_status", "weighting", "inspected", "accepted", "start", "end",
    "energy_tev", "luminosity_pb", "luminosity_validated",
    "luminosity_evidence",
)


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def numeric_digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_histogram(hist):
    if hist.ClassName() != "TH1D" or hist.GetDimension() != 1:
        raise ValueError("Expected the preserved one-dimensional TH1D source")
    axis = hist.GetXaxis()
    bins = hist.GetNbinsX()
    stats = array("d", [0.0] * 13)
    hist.GetStats(stats)
    sumw2 = hist.GetSumw2()
    snapshot = {
        "name": str(hist.GetName()), "class": str(hist.ClassName()),
        "dimension": int(hist.GetDimension()), "nbins": int(bins),
        "cells": int(hist.GetNcells()),
        "edges": [float(axis.GetBinLowEdge(i)) for i in range(1, bins + 2)],
        "contents_with_flows": [float(hist.GetBinContent(i))
                                for i in range(hist.GetNcells())],
        "source_errors_with_flows": [float(hist.GetBinError(i))
                                     for i in range(hist.GetNcells())],
        "source_sumw2": [float(sumw2.At(i)) for i in range(sumw2.GetSize())],
        "source_error_option": int(hist.GetBinErrorOption()),
        "entries": float(hist.GetEntries()),
        "stats": list(stats),
        "mean": float(hist.GetMean()), "stddev": float(hist.GetStdDev()),
        "effective_entries": float(hist.GetEffectiveEntries()),
        "norm_factor": float(hist.GetNormFactor()),
        "bin_labels": [str(axis.GetBinLabel(i)) for i in range(1, bins + 1)],
    }
    return snapshot


def read_graph(graph):
    if graph.ClassName() != "TGraphAsymmErrors":
        raise ValueError("Expected the preserved TGraphAsymmErrors display")
    count = graph.GetN()
    return {
        "name": str(graph.GetName()), "class": str(graph.ClassName()),
        "points": int(count),
        "x": [float(graph.GetPointX(i)) for i in range(count)],
        "y": [float(graph.GetPointY(i)) for i in range(count)],
        "error_x_low": [float(graph.GetErrorXlow(i)) for i in range(count)],
        "error_x_high": [float(graph.GetErrorXhigh(i)) for i in range(count)],
        "error_y_low": [float(graph.GetErrorYlow(i)) for i in range(count)],
        "error_y_high": [float(graph.GetErrorYhigh(i)) for i in range(count)],
    }


def read_plot(base: Path):
    import ROOT
    root_path = base.with_suffix(".root")
    sidecar_path = base.with_suffix(".plot.json")
    if not root_path.is_file() or not sidecar_path.is_file():
        raise ValueError(f"Missing native ROOT file or sidecar: {base}")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    root_file = ROOT.TFile.Open(str(root_path), "READ")
    if not root_file or root_file.IsZombie():
        raise ValueError(f"Unreadable native ROOT file: {root_path}")
    try:
        metadata_object = root_file.Get("atlas_plot_metadata")
        if not metadata_object or not metadata_object.InheritsFrom("TNamed"):
            raise ValueError(f"ROOT metadata missing: {root_path}")
        native_metadata = json.loads(str(metadata_object.GetTitle()))
        if native_metadata != sidecar:
            raise ValueError(f"ROOT metadata does not match sidecar: {base}")
        for field in SCIENCE_FIELDS:
            if field not in sidecar:
                raise ValueError(f"Required science field missing: {base}: {field}")
        key_names = [str(key.GetName()) for key in root_file.GetListOfKeys()]
        if len(key_names) != len(set(key_names)):
            raise ValueError(f"Duplicate native object cycles: {root_path}")
        numerics = {}
        for key_name in key_names:
            obj = root_file.Get(key_name)
            if obj.InheritsFrom("TH1"):
                numerics[key_name] = read_histogram(obj)
            elif obj.InheritsFrom("TGraph"):
                numerics[key_name] = read_graph(obj)
            elif not obj.InheritsFrom("TNamed"):
                raise ValueError(f"Unexpected object class: {base}: {key_name}: {obj.ClassName()}")
        if base.name not in numerics or numerics[base.name]["class"] != "TH1D":
            raise ValueError(f"Named native source histogram missing: {base}")
        display_name = base.name + "_display"
        if display_name not in numerics:
            raise ValueError(f"Stored statistical display graph missing: {base}")
        return {
            "native_file": str(root_path), "native_sha256": file_sha256(root_path),
            "sidecar_sha256": file_sha256(sidecar_path),
            "science_metadata": {field: sidecar[field] for field in SCIENCE_FIELDS},
            "standard": sidecar.get("standard"),
            "numerics": numerics,
        }
    finally:
        root_file.Close()


def first_difference(left, right, path=""):
    """Return a precise mismatch; floating values must have identical IEEE bits."""
    if type(left) is not type(right):
        return f"{path}: type {type(left).__name__} != {type(right).__name__}"
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return f"{path}: keys differ: {sorted(left)} != {sorted(right)}"
        for key in left:
            mismatch = first_difference(left[key], right[key], f"{path}.{key}")
            if mismatch:
                return mismatch
    elif isinstance(left, list):
        if len(left) != len(right):
            return f"{path}: length {len(left)} != {len(right)}"
        for index, (a, b) in enumerate(zip(left, right)):
            mismatch = first_difference(a, b, f"{path}[{index}]")
            if mismatch:
                return mismatch
    elif isinstance(left, float):
        if not math.isfinite(left) or not math.isfinite(right):
            return f"{path}: nonfinite numeric value"
        if struct.pack("!d", left) != struct.pack("!d", right):
            return f"{path}: {left!r} != {right!r} (IEEE-754 identity required)"
    elif left != right:
        return f"{path}: {left!r} != {right!r}"
    return None


def compact_inventory(plot):
    histograms = [o for o in plot["numerics"].values() if o["class"] == "TH1D"]
    graphs = [o for o in plot["numerics"].values() if o["class"] == "TGraphAsymmErrors"]
    return {
        "histograms": [{
            "name": h["name"], "bins": h["nbins"],
            "range": [h["edges"][0], h["edges"][-1]],
            "entries": h["entries"],
            "underflow": h["contents_with_flows"][0],
            "overflow": h["contents_with_flows"][-1],
            "in_range_sum": sum(h["contents_with_flows"][1:-1]),
            "numeric_sha256": numeric_digest(h),
        } for h in histograms],
        "display_graphs": [{
            "name": g["name"], "points": g["points"],
            "numeric_sha256": numeric_digest(g),
        } for g in graphs],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_directory", type=Path)
    parser.add_argument("new_directory", type=Path, nargs="?",
                        help="Omit only for a baseline inventory; this is not a comparison PASS")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    import ROOT
    ROOT.gROOT.SetBatch(True)
    if ROOT.gROOT.GetVersion() != "6.40.04":
        raise ValueError("Required existing ROOT 6.40.04 environment is not active")
    results = []
    failures = []
    for phase, names in PLOTS.items():
        for name in names:
            identity = f"{phase}/{name}"
            try:
                old = read_plot(args.old_directory / phase / name)
                item = {
                    "plot": identity, "old_native_sha256": old["native_sha256"],
                    "old_sidecar_sha256": old["sidecar_sha256"],
                    "old_standard": old["standard"],
                    "science_metadata": old["science_metadata"],
                    "inventory": compact_inventory(old),
                }
                if args.new_directory:
                    new = read_plot(args.new_directory / phase / name)
                    for subject in ("science_metadata", "numerics"):
                        difference = first_difference(old[subject], new[subject], subject)
                        if difference:
                            raise ValueError(difference)
                    item.update({
                        "new_native_sha256": new["native_sha256"],
                        "new_sidecar_sha256": new["sidecar_sha256"],
                        "new_standard": new["standard"],
                        "status": "PASS_EXACT_NUMERIC_AND_SCIENCE_METADATA_IDENTITY",
                    })
                else:
                    item["status"] = "BASELINE_INVENTORY_ONLY"
                results.append(item)
            except Exception as error:
                failures.append({"plot": identity, "error": str(error)})
    output = {
        "root_version": ROOT.gROOT.GetVersion(),
        "old_directory": str(args.old_directory.resolve()),
        "new_directory": str(args.new_directory.resolve()) if args.new_directory else None,
        "comparison": "IEEE-754 exact values; no tolerances; source errors and display errors",
        "expected_plots": 11, "audited_plots": len(results),
        "status": "FAIL" if failures else ("PASS" if args.new_directory else "BASELINE_INVENTORY_ONLY"),
        "results": results, "failures": failures,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{output['status']}: {len(results)}/11 plots; {len(failures)} failures")
    for failure in failures:
        print(f"FAIL {failure['plot']}: {failure['error']}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
