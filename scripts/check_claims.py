#!/usr/bin/env python3
"""Claim-provenance harness: every number cited in prose must trace to an artifact.

Generalized extraction of the DLLM-as-Service `verify_numbers.py` pattern.
The original checked specific macros against specific result JSONs; the
general contract is the same and is the part worth keeping as method:

  A paper is accurate when no sentence asserts a number that is not backed
  by a committed artifact. If a number appears in the text but not in the
  artifacts file, the text is claiming something the data does not say.

How it works:
  1. Flatten every JSON file in --artifacts into a set of known numbers.
  2. Extract every numeric token from prose (inline, not math/tables).
  3. Every prose number must match a known number (within formatting
     tolerance: 15.6 vs 15.60 vs 15.6x compare equal; small integers like
     section indices, years, and n-sizes may be exempted via config).
  4. Report untraced numbers with full sentence context, exit 1.

Config (settings.yaml `prose_quality:` section) supports:
  "claim_exemptions": [ {"value": "8", "reason": "K=8 config knob"} ... ]
  "precision_policy": {"latency": 1, "f1": 3}   (informational)

Usage:
  python3 check_claims.py --input <paper-dir> --artifacts <dir-or-file>
  python3 check_claims.py --input mypaper --artifacts results/ --json

Exit codes:
  0 = all prose numbers trace to artifacts
  1 = untraced numbers found (listed with context)
  2 = input error
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    DEFAULT_CONFIG, err, load_prose_quality, load_sections,
    load_thresholds, number_set_from_json, split_sentences, strip_latex,
)

# Numbers that are almost never claims about measured results.
GENERIC_EXEMPT = {
    "1", "2", "3", "0", "01", "02", "03", "04", "05", "06", "07", "08", "09",
}


def normalize_num(tok: str):
    """'15.60', '15.6', '15.6x', '2,400', '3.21×' -> comparable float or None."""
    tok = tok.replace(",", "").rstrip("xX×%")
    if re.fullmatch(r"\d+\.?\d*", tok):
        try:
            return float(tok)
        except ValueError:
            return None
    return None


def collect_artifact_numbers(artifacts) -> set:
    """Flatten artifact file(s) into a set of floats."""
    known = set()
    path = Path(artifacts)
    files = []
    if path.is_dir():
        files = sorted(p for p in path.rglob("*.json"))
    elif path.is_file():
        files = [path]
    if not files:
        err(f"ERROR: no artifact JSON files found at {artifacts}")
    for f in files:
        try:
            known |= number_set_from_json(json.loads(f.read_text()))
        except json.JSONDecodeError as e:
            err(f"ERROR: {f} is not valid JSON: {e}")
    known_floats = set()
    for v in known:
        try:
            known_floats.add(float(v))
        except ValueError:
            pass
    return known_floats


def check_claims(sections: dict, known: set, exemptions: set,
                 tolerance_pct: float = 0.1) -> list:
    """Returns list of dicts for every untraced number.

    A prose number is accepted if it matches a known artifact number exactly,
    after rounding to 1–3 decimals, or within ``tolerance_pct`` percent
    (relative). Rounding/tolerance acceptance is deliberate: prose rounds
    artifact values.
    """
    untraced = []
    for name, text in sorted(sections.items()):
        plain = strip_latex(text) if "\\begin" in text or text.count("$") else text
        plain = re.sub(r"\b\d[\d.]*\s*[%x×]\b", "X", plain)  # tolerances like "5%"
        for sent in split_sentences(plain):
            for tok in re.findall(r"\b\d[\d,.]*\b", sent):
                val = normalize_num(tok)
                if val is None:
                    continue
                if tok in exemptions or str(int(val)) in GENERIC_EXEMPT:
                    continue
                # accept exact, rounded, or integer-form matches
                if any(c in known for c in
                       (val, round(val, 1), round(val, 2), round(val, 3), round(val))):
                    continue
                # tolerance: accept if any known number is within tolerance_pct
                tol = abs(val) * tolerance_pct / 100
                if any(abs(k - val) <= tol for k in known):
                    continue
                untraced.append({
                    "section": name,
                    "value": tok,
                    "context": sent[:250],
                })
    return untraced


def main():
    ap = argparse.ArgumentParser(description="Number-provenance harness")
    ap.add_argument("--input", required=True, help="Paper/text directory")
    ap.add_argument("--artifacts", required=True, help="Results JSON file or directory")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--main-regex", default=r"^(0[1-8]|abstract)")
    ap.add_argument("--tolerance-pct", type=float, default=None,
                    help="Relative match tolerance in percent "
                         "(default: settings.yaml match_tolerance_pct)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    pq = load_prose_quality(args.config)
    th = load_thresholds(args.config)
    tolerance_pct = args.tolerance_pct
    if tolerance_pct is None:
        tolerance_pct = th.get("match_tolerance_pct", 0.1)
    exemptions = {str(e["value"]) for e in pq.get("claim_exemptions", [])
                  if isinstance(e, dict) and "value" in e}

    sections, _raw, _is_main = load_sections(args.input, args.main_regex)
    known = collect_artifact_numbers(args.artifacts)

    untraced = check_claims(sections, known, exemptions, tolerance_pct)

    if args.json:
        print(json.dumps({
            "artifact_numbers": len(known),
            "untraced": untraced,
            "total_untraced": len(untraced),
        }, indent=2))
    else:
        print(f"Artifact numbers known: {len(known)}")
        if not untraced:
            print("ALL PROSE NUMBERS TRACE TO ARTIFACTS")
        else:
            print(f"\n{len(untraced)} UNTRACED NUMBER(S):")
            for u in untraced:
                print(f"  [{u['section']}] {u['value']} in: \"{u['context']}\"")
    sys.exit(1 if untraced else 0)


if __name__ == "__main__":
    main()
