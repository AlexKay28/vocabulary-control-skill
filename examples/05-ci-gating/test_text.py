"""Pytest wrapper: run the vocabulary-control suite as tests.

Drop this file into your paper repository and edit the paths below. Each
script becomes one pytest case with the usual semantics:

    pytest test_text.py -v

No extra dependencies beyond pytest itself; the harness scripts are pure
stdlib. The suite exit codes are the test outcomes: exit 0 = pass,
exit 1 = fail (failures quoted in stdout), exit 2 = config error.
"""

import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent          # adjust: where the skill lives
PAPER = SKILL / "paper"                          # adjust: your paper dir
ARTIFACTS = SKILL / "results"                    # adjust: your artifact JSON dir
CONFIG = SKILL / "config"                        # adjust: your settings.yaml dir

CASES = [
    ("style", ["style_harness.py", "--input", str(PAPER), "--config", str(CONFIG),
               "--quiet"]),
    ("readability", ["eval_readability.py", "--input", str(PAPER),
                     "--config", str(CONFIG)]),
    ("claims", ["check_claims.py", "--input", str(PAPER), "--config", str(CONFIG),
                "--artifacts", str(ARTIFACTS)]),
]


def _run(script_args):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script_args[0]), *script_args[1:]],
        capture_output=True, text=True,
    )


def test_style_harness():
    r = _run(CASES[0][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_readability():
    r = _run(CASES[1][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_number_provenance():
    r = _run(CASES[2][1])
    assert r.returncode == 0, r.stdout + r.stderr
