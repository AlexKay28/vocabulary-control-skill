# Recipe 04 — Every ratio names its arm (A3, A6)

**From the paper:** DLLM compared a quality arm (dense AR-3B) and a latency
arm (AR-30B MoE) that were *not the same model*. `check_arm_attribution_inline`
required every ratio to name its arm or cite a table/figure, and required the
asymmetry disclosure at first use rather than only in §7 Threats. This recipe
shows the two rule types that encode it: `proximity` and `first_use`.

## Rules

- `A3-ratio-names-arm` (proximity): every `N.N×` must have an arm name
  (AR/DG/LLaDA) or a Table/Figure citation within 30 words.
- `A6-asymmetry-disclosed-first-use` (first_use): the first "AR-30B" in §1
  must carry the MoE / dense-AR-3B asymmetry disclosure within 40 words.

## Run

```bash
python3 scripts/check_rules.py \
  --input recipes/04-arm-attribution/input \
  --config recipes/04-arm-attribution
# expect: exit 1 — the unattributed 3.21× and the undisclosed first use fire;
#         the 2.5× ratio passes because "AR-30B" sits inside its window

python3 scripts/check_rules.py \
  --input recipes/04-arm-attribution/input_fixed \
  --config recipes/04-arm-attribution
# expect: exit 0
```

## Agent usage

Use `proximity` for any claim that needs local grounding (a ratio → its
arm, a percentage → its denominator, a latency → its hardware). Use
`first_use` for disclosures that must happen once, early, and inline. Both
quote the exact sentence and the window that failed, so the fix is local.
