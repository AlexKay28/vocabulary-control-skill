#!/usr/bin/env python3
"""Test suite for vocabulary-control-skill. Pure stdlib (unittest).

Each test runs a harness script as a subprocess against the bundled examples
and asserts exit codes plus key failure strings — the same contract agents
rely on. Run:

    python3 -m unittest discover -s tests -v          # all tests
    python3 tests/test_suite.py                        # same
    VCS_NO_PYYAML=1 python3 -m unittest discover -s tests  # fallback YAML parser
"""

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
EXAMPLES = REPO / "examples"
DLLM = REPO.parent / "DLLM-as-Service"   # optional: deeper real-paper tests


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, cwd=REPO, timeout=300,
    )


class TestSettingsLoading(unittest.TestCase):
    def test_settings_yaml_loads(self):
        sys.path.insert(0, str(SCRIPTS))
        import common
        s = common.load_settings(REPO / "config")
        self.assertIn("thresholds", s)
        self.assertIn("banned_patterns", s)
        self.assertGreater(len(s["banned_patterns"]), 20)
        th = common.load_thresholds(REPO / "config")
        self.assertEqual(th["sentence_p90_max"], 45)
        self.assertEqual(th["metaphor_max_per_section"], 1)

    def test_fallback_yaml_parser_matches_pyyaml(self):
        sys.path.insert(0, str(SCRIPTS))
        import common
        text = (REPO / "config" / "settings.yaml").read_text()
        parsed = common.parse_yaml(text)
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        self.assertEqual(parsed, yaml.safe_load(text))


class TestExample01MlPaper(unittest.TestCase):
    def test_neuroslop_section_fails_with_quoted_reasons(self):
        r = run("style_harness.py",
                "--input", str(EXAMPLES / "01-ml-paper-latex/input"),
                "--config", str(EXAMPLES / "01-ml-paper-latex"), "--quiet")
        self.assertEqual(r.returncode, 1)
        self.assertIn("02_deployment", r.stdout)
        self.assertIn("metaphor_count", r.stdout)
        self.assertIn("terminology_diffusion_model", r.stdout)

    def test_claims_trace_to_artifacts(self):
        r = run("check_claims.py",
                "--input", str(EXAMPLES / "01-ml-paper-latex/input"),
                "--config", str(EXAMPLES / "01-ml-paper-latex"),
                "--artifacts", str(EXAMPLES / "01-ml-paper-latex/artifacts"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestExample02BlogPost(unittest.TestCase):
    def test_clean_blog_passes(self):
        r = run("run_all.py",
                "--input", str(EXAMPLES / "02-blog-post-markdown/input"),
                "--config", str(EXAMPLES / "02-blog-post-markdown"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestExample03StrictMode(unittest.TestCase):
    def test_default_passes(self):
        r = run("style_harness.py",
                "--input", str(EXAMPLES / "03-strict-mode/input"), "--quiet")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_strict_fails(self):
        r = run("style_harness.py",
                "--input", str(EXAMPLES / "03-strict-mode/input"),
                "--config", str(EXAMPLES / "03-strict-mode"), "--quiet")
        self.assertEqual(r.returncode, 1)
        self.assertIn("sentence_p90", r.stdout)


class TestExample04DeriveThresholds(unittest.TestCase):
    def test_derive_runs_and_reports(self):
        r = run("derive_thresholds.py",
                "--corpus", str(EXAMPLES / "04-custom-corpus/mini-corpus"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sentence_p90_max", r.stdout)
        self.assertIn("half-corpus vocab overlap", r.stdout)

    def test_derive_reproduces_shipped_defaults(self):
        """The shipped corpus must reproduce the shipped defaults — proof the
        defaults are derived, not vibes."""
        r = run("derive_thresholds.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sentence_median_max: 28", r.stdout)
        self.assertIn("sentence_p90_max: 45", r.stdout)
        self.assertIn("sentence_gt40_pct_max: 15.0", r.stdout)


class TestJsonOutput(unittest.TestCase):
    def test_style_json_is_valid(self):
        import json
        r = run("style_harness.py",
                "--input", str(EXAMPLES / "03-strict-mode/input"), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("sections", data)
        self.assertIn("corpus_baseline", data)


@unittest.skipUnless(DLLM.exists(), "DLLM-as-Service repo not present")
class TestRealPaper(unittest.TestCase):
    def test_v9_gate_fails_with_known_findings(self):
        """Later paper versions drift from the criteria; the gate must catch it."""
        r = run("style_harness.py",
                "--input", str(DLLM / "paper/v9"), "--quiet")
        self.assertEqual(r.returncode, 1)
        self.assertIn("abstract_numbers", r.stdout)

    def test_v9_provenance_finds_untraced_numbers(self):
        r = run("check_claims.py",
                "--input", str(DLLM / "paper/v9"),
                "--artifacts", str(DLLM / "results"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("600,000", r.stdout)


if __name__ == "__main__":
    unittest.main()
