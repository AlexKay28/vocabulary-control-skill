# Recipe 02 — Punchlines must not be buried (I3, I5)

**From the paper:** the DLLM tail-latency punchline ("3.21× breaks a batch-1
SLA") lived only in §4 Limits, and the input-length caveat (prefill slope
steeper, moves L*) was buried in §4.4 while §2 presented L* = 48 as fixed.
`check_tail_punchline_in_results` and `check_input_length_not_buried` forced
both into the sections where the reader needs them.

## Rules

- `I3-tail-punchline-in-results` (required): §3 must mention the batch-1 SLA
  punchline.
- `I5-prefill-caveat-present` (required): §2 must contain "steeper".
- `I5-caveat-names-input` (required): §2 must name the input dependence.

## Run

```bash
python3 scripts/check_rules.py \
  --input recipes/02-punchline-not-buried/input \
  --config recipes/02-punchline-not-buried
# expect: exit 1 — all three rules fire (punchline and caveat missing)

python3 scripts/check_rules.py \
  --input recipes/02-punchline-not-buried/input_fixed \
  --config recipes/02-punchline-not-buried
# expect: exit 0
```

## Agent usage

After writing a section, list its punchlines as `required` rules pointed at
that section. If a later restructure moves the punchline into an appendix,
the gate fails — this is the check that survives refactors, which prose
review alone does not.
