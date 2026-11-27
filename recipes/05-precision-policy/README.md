# Recipe 05 — Numeric precision policy (A7)

**From the paper:** DLLM fixed precision per metric — latency 1 dp, F1 3 dp,
ratios 1 dp, rates 3 dp — and `check_precision_policy` enforced it, so
re-measurement could not silently change precision between sections.
Inconsistent decimals read as inconsistent experiments.

## Rules

- `A7-f1-three-dp`: F1 → exactly 3 decimal places.
- `A7-latency-one-dp`: latency → exactly 1 decimal place.
- `A7-ratio-one-dp`: ratio → exactly 1 decimal place.

The `precision` rule type looks for the metric keyword, then the first
number within the next few words (optionally after "of/is/=/:"), and counts
its decimals.

## Run

```bash
python3 scripts/check_rules.py \
  --input recipes/05-precision-policy/input \
  --config recipes/05-precision-policy
# expect: exit 1 — F1 0.81 (2 dp), latency 23.456 (3 dp), ratio 3.21 (2 dp)

python3 scripts/check_rules.py \
  --input recipes/05-precision-policy/input_fixed \
  --config recipes/05-precision-policy
# expect: exit 0 — 0.812 / 23.5 / 3.2
```

## Agent usage

Combine with `check_claims.py`: provenance says *the number exists in the
artifacts*, precision says *it is printed the way the paper prints it*.
Together they kill both invented numbers and sloppy transcription.
