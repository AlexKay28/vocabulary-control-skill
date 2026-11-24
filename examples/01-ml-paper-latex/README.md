# Example 01 — ML paper (LaTeX, full pipeline)

Demonstrates the complete setup: stylometric gate, terminology consistency,
number provenance. The paper has one clean section (should pass) and one
deliberately neuroslop section (should fail, with quoted evidence).

## Layout

```
settings.yaml            # profile: thresholds + banned patterns + terminology
input/
  main.tex               # abstract (≤3 inline numbers)
  sections/
    01_introduction.tex  # clean — PASS
    02_deployment.tex    # neuroslop — FAIL (5 names for one concept, metaphors)
artifacts/results.json   # the numbers the text is allowed to cite
```

## Run it

```bash
# From the repo root:
python3 scripts/style_harness.py \
  --input examples/01-ml-paper-latex/input \
  --config examples/01-ml-paper-latex --quiet
# expect: exit 1 — 02_deployment FAIL (metaphor_count, terminology_diffusion_model)

python3 scripts/eval_readability.py \
  --input examples/01-ml-paper-latex/input \
  --config examples/01-ml-paper-latex
# expect: quoted flesch/sentence failures on 02_deployment

python3 scripts/check_claims.py \
  --input examples/01-ml-paper-latex/input \
  --config examples/01-ml-paper-latex \
  --artifacts examples/01-ml-paper-latex/artifacts
# expect: exit 1 — "23" and "47" are traced, but any number not in
# artifacts/results.json is reported with its sentence

python3 scripts/run_all.py \
  --input examples/01-ml-paper-latex/input \
  --config examples/01-ml-paper-latex \
  --artifacts examples/01-ml-paper-latex/artifacts
# expect: exit 1 until 02_deployment is rewritten; then exit 0
```

## What to try

- Delete the metaphor from `02_deployment.tex`, rerun: the metaphor failure
  disappears but the terminology failure remains (4 names for one concept).
- Add `{"value": "99", "reason": "test"}` to `claim_exemptions` — nothing
  changes, because exemptions only cover numbers that exist in prose.
- Point `--corpus` at `reference_corpus/` (default) vs a custom corpus
  (see example 04) and watch `vocab_overlap` move.
