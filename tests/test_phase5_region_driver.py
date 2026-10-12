"""Deterministic derived-cache fixtures; no native ROOT data or physical fit."""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal

EXECUTABLE = Path(sys.argv[1]).resolve()
SELECTION = Path(sys.argv[2]).resolve()
sys.argv = [sys.argv[0]]
DATA_HEADER = "entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue".split(",")
MC_HEADER = "dsid,entry,run,event,mc_weight,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,C9_selected,roundoff_objects,invalid_reason,cartesian_mass_closure_pass".split(",")


def fixtures(mc=False):
    rows = []
    masses = [115, 125, 130, 115, 125, 100, 160, 115, 115, 115, 115, 115]
    weights = [1, -2, 0, 3, 2, -1, 1, 2, -2, 0, 4, 1]
    c9 = [1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0]
    for index, mass in enumerate(masses):
        deta = 1 if index in (3, 4) else .5
        row = dict(entry=str(100+index), run="276336", event=str(5000+index), valid="1", photon_n="2", jet_n="2",
                   photon1_pt="50", photon2_pt="30", photon1_eta=str(deta/2), photon2_eta=str(-deta/2),
                   jet1_pt="45", jet2_pt="35", jet1_eta=".2", jet2_eta="-.2", m_gg=str(mass), m_jj="90",
                   deltaR_gg="2", deltaR_jj="2.5", roundoff_objects="0")
        if index == 7:
            row["valid"] = "0"
            for key in ("photon1_pt", "photon2_pt", "photon1_eta", "photon2_eta", "jet1_pt", "jet2_pt", "jet1_eta", "jet2_eta", "m_gg", "m_jj", "deltaR_gg", "deltaR_jj"):
                row[key] = ""
        if index == 8:
            row["jet2_pt"] = "25"
        if index == 9:
            row["photon1_pt"] = "35"
        if index == 10:
            row.update(photon_n="1", photon2_pt="", photon2_eta="", m_gg="", deltaR_gg="")
        if index == 11:
            row.update(jet_n="0", jet1_pt="", jet2_pt="", jet1_eta="", jet2_eta="", m_jj="", deltaR_jj="")
        if mc:
            row.update(dsid="343981", mc_weight=str(weights[index]), C9_selected=str(c9[index]),
                       invalid_reason="gg_negative_pair_M2" if index == 7 else "", cartesian_mass_closure_pass="1")
        else:
            row.update(deltaEta_gg=str(deta) if row["deltaR_gg"] else "", deltaPhi_gg="1.5" if row["deltaR_gg"] else "",
                       deltaEta_jj=".4" if row["deltaR_jj"] else "", deltaPhi_jj="2" if row["deltaR_jj"] else "",
                       p1_tight_id="0", p2_tight_id="0", p1_tight_iso="0", p2_tight_iso="0",
                       issue="gg_negative_pair_M2" if index == 7 else "")
        rows.append(row)
    return rows


def serialize(header, rows):
    # Native writers use an unquoted scalar cache. All fixture values are
    # comma/newline-free; malformed quoting is tested explicitly below.
    return ",".join(header)+"\n"+"".join(",".join(str(row.get(key, "")) for key in header)+"\n" for row in rows)


class Contract(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="phase5_regions_", dir=Path.cwd()))
        self.case = 0

    def run_case(self, *, rows=None, mc=False, header=None, text=None, sample=None, start="100", end="112", units="PROVISIONAL", existing=False, ok=False):
        self.case += 1
        cache = self.base/f"cache_{self.case}.csv"
        output = self.base/f"output_{self.case}"
        if text is None:
            text = serialize(header or (MC_HEADER if mc else DATA_HEADER), rows if rows is not None else fixtures(mc))
        cache.write_text(text, encoding="utf-8")
        cache_hash = hashlib.sha256(cache.read_bytes()).hexdigest()
        if existing:
            output.mkdir()
            (output/"preserve.txt").write_text("existing user work", encoding="utf-8")
        result = subprocess.run([str(EXECUTABLE), str(cache), str(SELECTION), str(output), sample or ("343981" if mc else "DATA"), str(start), str(end), units], text=True, capture_output=True, timeout=30)
        self.assertEqual(hashlib.sha256(cache.read_bytes()).hexdigest(), cache_hash)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertEqual(set(path.name for path in output.iterdir()), {"event_regions.csv", "region_counts.csv", "summary.json"})
            summary = json.loads((output/"summary.json").read_text())
            self.assertEqual(summary["status"], "PASS_BOUNDED_DERIVED_CACHE_INVENTORY")
            self.assertFalse(summary["normalization_applied"])
            self.assertFalse(summary["scale_factors_applied"])
            self.assertFalse(summary["physical_transfer_factor_applied"])
            self.assertFalse(summary["native_ROOT_read_by_this_app"])
            self.assertFalse(summary["source_ROOT_identity_verified_by_this_app"])
            self.assertEqual(summary["unit_status"], "PROVISIONAL")
            self.assertEqual(summary["physical_closure_status"], "BLOCKED")
            ledger = list(csv.DictReader(io.StringIO((output/"event_regions.csv").read_text())))
            counts = {row["category"]: row for row in csv.DictReader(io.StringIO((output/"region_counts.csv").read_text()))}
            return summary, ledger, counts
        self.assertNotEqual(result.returncode, 0, "Malformed cache unexpectedly accepted")
        self.assertIn("FAIL region inventory", result.stderr)
        if existing:
            self.assertEqual((output/"preserve.txt").read_text(), "existing user work")
            self.assertEqual(len(list(output.iterdir())), 1)
        else:
            self.assertFalse(output.exists(), "Rejected input left partial scientific output")

    def test_data_partition_and_premass_population(self):
        summary, rows, counts = self.run_case(ok=True)
        expected = ["CR", "PROSPECTIVE_SR", "CR", "VR", "RESERVED_WINDOW_PARTITION", "OUTSIDE_STUDY_DOMAIN", "CR", "INVALID_INPUT", "FAILS_JET_SELECTION", "FAILS_C5", "FAILS_C5", "FAILS_JET_SELECTION"]
        self.assertEqual([row["region"] for row in rows], expected)
        self.assertEqual((summary["entries"], summary["C5"], summary["C5_plus_jets"], summary["C9"], summary["outside_study_domain"]), (12, 9, 7, 6, 1))
        self.assertEqual(rows[5]["C5"], "1")
        self.assertEqual(rows[5]["C5_plus_jets"], "1")
        self.assertEqual(rows[5]["C9"], "0")
        self.assertEqual(rows[4]["C9"], "1")
        self.assertEqual(sum(int(row["raw_entries"]) for row in counts.values() if row["kind"] == "DISJOINT_REGION"), 12)
        self.assertEqual(Decimal(counts["INPUT"]["sumW"]), Decimal(12))
        self.assertEqual(Decimal(counts["INPUT"]["sumW2"]), Decimal(12))
        self.assertEqual(summary["generator_weight_semantics"], "NOT_APPLICABLE")

    def test_mc_signed_diagnostic_moments(self):
        summary, ledger, counts = self.run_case(mc=True, ok=True)
        weights = [Decimal(row["mc_weight"]) for row in fixtures(True)]
        self.assertEqual(Decimal(counts["INPUT"]["sumW"]), sum(weights))
        self.assertEqual(Decimal(counts["INPUT"]["sumW2"]), sum(weight*weight for weight in weights))
        self.assertEqual(Decimal(counts["INPUT"]["sumAbsW"]), sum(abs(weight) for weight in weights))
        self.assertEqual((int(counts["INPUT"]["positive_weights"]), int(counts["INPUT"]["negative_weights"]), int(counts["INPUT"]["zero_weights"])), (7, 3, 2))
        for category, record in counts.items():
            if record["kind"] != "DISJOINT_REGION":
                continue
            selected = [Decimal(row["raw_weight"]) for row in ledger if row["region"] == category]
            self.assertEqual(int(record["raw_entries"]), len(selected))
            self.assertEqual(Decimal(record["sumW"]), sum(selected))
            self.assertEqual(Decimal(record["sumW2"]), sum(weight*weight for weight in selected))
        self.assertEqual(summary["generator_weight_semantics"], "UNKNOWN")
        self.assertIn("SEMANTICS_UNKNOWN", summary["weight_scope"])
        self.assertEqual(summary["C9"], 6)

    def test_exact_schema_guards(self):
        for header in (DATA_HEADER+["unintended"], DATA_HEADER[:-1], DATA_HEADER[:-1]+["entry"], [DATA_HEADER[1], DATA_HEADER[0]]+DATA_HEADER[2:]):
            with self.subTest(header=header):
                self.run_case(header=header)
        self.run_case(mc=True, sample="DATA")
        self.run_case(sample="343981")
        self.run_case(text=serialize(DATA_HEADER, fixtures()).replace("entry,", '"entry",', 1))

    def test_row_width_blank_and_quoting(self):
        text = serialize(DATA_HEADER, fixtures())
        self.run_case(text=text.replace("5000,1,2", "5000,1", 1))
        self.run_case(text=text.replace("5000,1,2", "5000,1,2,EXTRA", 1))
        self.run_case(text=text+"\n")
        self.run_case(text=text.replace("5000,", '"5000",', 1))
        self.run_case(text=text.replace("5000,", "5000\x00,", 1))
        self.run_case(text=",".join(DATA_HEADER)+"\n"+"x"*65537+"\n")

    def test_contiguous_and_identity_guards(self):
        rows = fixtures(); rows[1]["entry"] = "102"; self.run_case(rows=rows)
        rows = fixtures(); rows[1]["entry"] = "100"; self.run_case(rows=rows)
        rows = fixtures(); rows[1]["run"] = rows[0]["run"]; rows[1]["event"] = rows[0]["event"]; self.run_case(rows=rows)
        self.run_case(rows=fixtures()[:-1])
        self.run_case(end="111")
        rows = fixtures(); rows[0]["run"] = str(2**32); self.run_case(rows=rows)
        rows = fixtures(); rows[0]["event"] = str(2**64); self.run_case(rows=rows)

    def test_bool_multiplicity_and_numeric_guards(self):
        for field, value in (("valid", "true"), ("valid", "2"), ("photon_n", "-1"), ("jet_n", "100001"), ("roundoff_objects", "5"), ("photon1_pt", "nan"), ("photon1_eta", "inf"), ("m_gg", "115bad"), ("p1_tight_id", "2"), ("photon1_pt", "-1"), ("photon1_pt", "20")):
            with self.subTest(field=field, value=value):
                rows = fixtures(); rows[0][field] = value; self.run_case(rows=rows)

    def test_partial_object_and_invalid_cache_guards(self):
        rows = fixtures(); rows[0]["m_gg"] = ""; self.run_case(rows=rows)
        rows = fixtures(); rows[7]["m_gg"] = "115"; self.run_case(rows=rows)
        rows = fixtures(); rows[10]["photon2_pt"] = "30"; self.run_case(rows=rows)
        rows = fixtures(); rows[11]["jet1_eta"] = ".5"; self.run_case(rows=rows)
        rows = fixtures(); rows[0]["deltaR_gg"] = ""; self.run_case(rows=rows)

    def test_mc_dsid_c9_weight_and_numerical_guards(self):
        for field, value in (("dsid", "346214"), ("mc_weight", "nan"), ("mc_weight", "inf"), ("C9_selected", "0"), ("C9_selected", "2"), ("cartesian_mass_closure_pass", "0"), ("cartesian_mass_closure_pass", "true")):
            with self.subTest(field=field):
                rows = fixtures(True); rows[0][field] = value; self.run_case(rows=rows, mc=True)

    def test_cli_bounds_units_and_output_preservation(self):
        for sample in ("0", "-1", "2147483648", "343981x"):
            self.run_case(mc=True, sample=sample)
        for start, end in (("100", "100"), ("100", "99"), ("-1", "112"), ("100", "64101"), ("100", str(2**63)), (" 100", "112")):
            self.run_case(start=start, end=end)
        self.run_case(units="VERIFIED")
        self.run_case(existing=True)
        result = subprocess.run([str(EXECUTABLE)], capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)

    def test_reproducible_outputs_and_crlf(self):
        text = serialize(MC_HEADER, fixtures(True))
        a, ledger_a, counts_a = self.run_case(mc=True, text=text, ok=True)
        b, ledger_b, counts_b = self.run_case(mc=True, text=text.replace("\n", "\r\n"), ok=True)
        self.assertEqual(ledger_a, ledger_b)
        self.assertEqual(counts_a, counts_b)
        for key in ("entries", "C5", "C5_plus_jets", "C9", "outside_study_domain", "generator_weight_semantics", "weight_scope", "limits"):
            self.assertEqual(a[key], b[key])


if __name__ == "__main__":
    unittest.main(verbosity=2)
