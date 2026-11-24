# Example 03 — Strict mode

The same harness, tighter limits. `input/draft.md` passes the default
profile but fails this one — strict mode is for final drafts, or for venues
where any LLM fingerprint is costly.

## Run it

```bash
# default profile — passes:
python3 scripts/style_harness.py \
  --input examples/03-strict-mode/input --quiet
# expect: exit 0

# strict profile — fails:
python3 scripts/style_harness.py \
  --input examples/03-strict-mode/input \
  --config examples/03-strict-mode --quiet
# expect: exit 1 — sentence_median over 22, sentences over 35 (p90), etc.
```

The point: profiles are just YAML. "Strict" is not a flag in the code — it
is a different set of numbers. Make a `settings-final.yaml` next to your
working `settings.yaml` and run the strict gate only before submission.
