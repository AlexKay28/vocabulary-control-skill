# Recipe 01 — No backwards claims (A1, A2)

**From the paper:** DLLM-as-Service §1 originally claimed a 15.6× advantage
"survived" harness corrections. The 15.6× was the *defective* harness;
corrections brought it to 2.5×. Separately, a §3 header claimed DG "wins at
every length" over a table containing a 0.7× row. Both were caught by
bespoke checks in `verify_numbers.py` (`check_no_backwards_fifteenfold`,
`check_header_table_consistency`). This recipe makes them declarative.

## Rules

- `A1-no-fifteenfold` (forbidden): `fifteenfold|15.6` must not appear in §1.
- `A2-no-wins-at-every` (forbidden): `wins at every` must not appear in §3
  when the table contradicts it.

## Run

```bash
python3 scripts/check_rules.py \
  --input recipes/01-no-backwards-claims/input \
  --config recipes/01-no-backwards-claims
# expect: exit 1 — both rules fire, with the offending sentences quoted

python3 scripts/check_rules.py \
  --input recipes/01-no-backwards-claims/input_fixed \
  --config recipes/01-no-backwards-claims
# expect: exit 0 — corrected 2.5× claim and softened header pass
```

## Agent usage

When editing a claim that changed after re-measurement, add a `forbidden`
rule naming the *old* number in the sections where it must not resurface.
This is stronger than memory: the gate fails if a later edit reintroduces
the retracted figure anywhere in the introduction.
