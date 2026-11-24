#!/usr/bin/env python3
"""Run the full vocabulary-control suite: style + readability + claims.

Single entry point, pytest-like contract:

  exit 0 = the text passes every check (publishable)
  exit 1 = at least one check failed (see per-script output above)

Usage:
  python3 run_all.py --input <paper-dir> [--artifacts <dir>] [options...]

Options are forwarded to the individual scripts; see --help output of each.
--artifacts is optional: the claims check is skipped when omitted.
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["style_harness.py", "eval_readability.py", "check_claims.py"]


def main():
    ap = argparse.ArgumentParser(description="Run the full text-control suite")
    ap.add_argument("--input", required=True)
    ap.add_argument("--artifacts", default=None,
                    help="Artifact JSON dir/file; enables the claims check")
    ap.add_argument("--config", default=None)
    ap.add_argument("--main-regex", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args, extra = ap.parse_known_args()

    failures = {}
    for script in SCRIPTS:
        if script == "check_claims.py" and not args.artifacts:
            print(f"[skip] {script} (no --artifacts given)")
            continue
        cmd = [sys.executable, str(HERE / script), "--input", args.input]
        if args.config:
            cmd += ["--config", args.config]
        if args.main_regex:
            cmd += ["--main-regex", args.main_regex]
        if script == "check_claims.py":
            cmd += ["--artifacts", args.artifacts]
        if args.quiet:
            cmd += ["--quiet"] if script == "style_harness.py" else []
        if args.json:
            cmd += ["--json"]
        cmd += extra

        print(f"\n{'=' * 80}\n  RUNNING {script}\n{'=' * 80}")
        r = subprocess.run(cmd)
        if r.returncode == 1:
            failures[script] = "checks failed"
        elif r.returncode != 0:
            failures[script] = f"error (exit {r.returncode})"

    print(f"\n{'=' * 80}\n  SUITE SUMMARY\n{'=' * 80}")
    if not failures:
        print("  ALL PASS — text meets the corpus-derived criteria.")
        sys.exit(0)
    for script, why in failures.items():
        print(f"  FAIL: {script} — {why}")
    sys.exit(1)


if __name__ == "__main__":
    main()
