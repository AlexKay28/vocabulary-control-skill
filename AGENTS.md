# AGENTS.md

This repo is itself a skill for AI agents — see **SKILL.md** for the
grounding-truth method (corpus-derived thresholds, quote-and-fix workflow,
exit-code gate).

## Commands

Pure Python stdlib; no build, no dependencies.

- **Tests:** `make test` (stdlib unittest; `make test-no-pyyaml` forces the
  built-in YAML parser — both must pass)
- **Demo:** `make demo` (expected to exit 1: the demo neuroslop section must
  fail with quoted reasons)
- **Derive thresholds:** `make derive` (must print 28 / 45 / 15.0 — the
  shipped defaults reproducing from the shipped corpus)

## Conventions

- One source of truth: `config/settings.yaml`. Never add thresholds or
  banned patterns to code; add them to YAML.
- A threshold you cannot trace to a measurement is a vibe (CONTRIBUTING.md).
- Harness scripts must keep the exit-code contract: 0 = pass, 1 = checks
  failed, 2 = input/config error. Automation depends on it.
- Every example in `examples/` must run end-to-end and its README must state
  expected exit codes; changes to behavior need matching test updates in
  `tests/test_suite.py`.
