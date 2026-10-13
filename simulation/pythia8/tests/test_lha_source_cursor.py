"""Prepare reader API fixtures from a genuine existing hard event; no shower."""
import gzip
from pathlib import Path
import subprocess
import sys
import tempfile

def main():
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / "simulation/pythia8/scripts"))
    from validate_lhe_stream import iter_lhe_events
    with tempfile.TemporaryDirectory(prefix="atlas_hh_lha_api_") as directory:
        root = Path(directory)
        original = repo / "reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz"
        plain = root / "input.lhe"
        with gzip.open(original, "rb") as incoming, plain.open("wb") as outgoing:
            for chunk in iter(lambda: incoming.read(65536), b""):
                outgoing.write(chunk)
        source = next(iter_lhe_events(plain))
        rows = source["rows"]
        normalize = lambda value: format(float(value.replace("D", "e").replace("d", "e")), ".17g")
        text = "E 1 " + source["source_event_content_hash"] + " " + " ".join(rows[0][:2] + [normalize(v) for v in rows[0][2:]]) + "\n"
        for row in rows[1:]:
            text += "P " + " ".join(row[:6] + [normalize(v) for v in row[6:]]) + "\n"
        good, bad = root / "valid.dat", root / "corrupt.dat"
        good.write_text(text)
        lines = text.splitlines()
        words = lines[1].split()
        words[1] = "999"
        lines[1] = " ".join(words)
        bad.write_text("\n".join(lines) + "\n")
        result = subprocess.run([sys.argv[1], sys.argv[2], str(repo / "simulation/pythia8/config/baseline_shower.cmnd"),
                                 str(plain), str(good), str(bad)], check=False)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
