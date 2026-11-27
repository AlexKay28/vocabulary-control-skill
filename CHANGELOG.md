# Changelog

## v1.1.0 — 2026-11-27

- `scripts/check_rules.py`: declarative text-rule engine (forbidden,
  required, max_count, proximity, first_use, precision) — the original
  paper's bespoke `verify_numbers.py` editorial checks as YAML.
- `recipes/`: six agent-friendly recipes from the DLLM-as-Service arXiv
  paper (A1/A2 no backwards claims, I3/I5 punchlines not buried, R9 no
  editorializing, A3/A6 arm attribution, A7 precision policy, S1 abstract
  structure), each with failing + fixed fixtures and the original story.
- `run_all.py` now runs `check_rules` automatically when `rules:` is set.
- Test suite: 14 tests, all recipes covered (fail fixture + fixed fixture).

## v1.0.0 — 2026-11-24

Initial public release. Extracted from the DLLM-as-Service paper pipeline.

- `scripts/`: style harness (13 stylometric metrics vs reference corpus),
  readability/density harness, claim-provenance harness, threshold
  derivation, single pytest-style gate. Pure Python stdlib.
- `config/settings.yaml`: single YAML source of truth (thresholds, banned
  patterns, terminology, prose-quality). Built-in YAML-subset parser when
  PyYAML is absent; test suite asserts parser parity.
- `reference_corpus/`: 15 published ML papers (~141k words) + MANIFEST.
  Shipped defaults reproduce from it via `derive_thresholds.py`.
- `examples/`: five runnable profiles (LaTeX paper, Markdown blog, strict
  mode, custom corpus, CI gating) plus a real 20/20-passing report and a
  real failing report from the source project's own drift.
- `criteria/CRITERIA.md`: the Successful/Accurate/Interesting/Readable
  contract template.
- `tests/`: 12-test stdlib unittest suite covering settings loading,
  example behavior, JSON output, derivation reproducibility, and (when
  available) the original paper's gate behavior.
