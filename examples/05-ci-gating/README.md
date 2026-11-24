# Example 05 — CI gating

The suite's exit codes are designed for automation. Three integration
patterns, from lightest to strongest:

## 1. pytest wrapper (`test_text.py`)

Copy into your repo, edit the paths at the top, and the suite runs as three
pytest cases with failure output quoted in the test log:

```bash
pytest test_text.py -v
```

## 2. pre-commit hook (`.pre-commit-config.yaml`)

Runs the gate on every commit that touches the paper, the results, or the
settings. Commits that introduce neuroslop never reach the branch.

## 3. GitHub Action (`.github/workflows/text-gate.yml`)

Runs the full suite on push/PR and uploads the markdown style report as a
build artifact on failure — the reviewer sees exactly which sentences
failed, not just a red cross.

All three assume this skill is vendored into (or submodule'd by) your repo;
fix the paths to match your layout.
