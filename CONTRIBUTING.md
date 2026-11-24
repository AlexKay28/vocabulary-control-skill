# Contributing

Small repo, small rules.

## The one rule that matters

**A threshold you cannot trace to a measurement is a vibe.** New checks and
thresholds must either (a) be derived from a reference corpus (show the
measurement, like `scripts/derive_thresholds.py` does) or (b) be labeled as
editorial choices in comments. No silent third category.

## Layout

- `scripts/` — the harnesses. Pure Python stdlib; no new dependencies.
  PyYAML is used opportunistically but never required (see
  `common.parse_yaml`).
- `config/settings.yaml` — the default profile; single source of truth.
- `examples/` — runnable demos; every example must work end-to-end and its
  README must state the expected exit codes.
- `tests/test_suite.py` — stdlib unittest; runs the harnesses against the
  examples and asserts exit codes. Must pass before any merge:
  `python3 -m unittest discover -s tests -v`

## Adding a banned pattern

Edit `banned_patterns:` in `config/settings.yaml` (or your project's own
settings). No code changes. If the pattern needs inflections, write them
(`\bdelve(s|d|ing)?\b`), don't add five entries.

## Adding a check

1. Decide corpus-grounded vs editorial; document which.
2. Implement it in the relevant script with a config knob, default off or at
   the corpus-derived value.
3. Add a fixture to an example (or a new example) that fails the check.
4. Add a test asserting the exit code and the quoted failure.
