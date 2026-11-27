# Recipe 06 — Abstract structure (S1)

**From the paper:** the DLLM abstract had to state the claim, the comparison
(arms matched on what), the headline number, and the regime — a reviewer
should reconstruct the paper from the abstract alone. This recipe turns that
contract into three `required` rules scoped to the abstract section.

## Rules

- `S1-headline-number`: abstract must contain a number.
- `S1-comparison-stated`: abstract must name the comparison
  (vs / compared / baseline / matched).
- `S1-regime-stated`: abstract must state the regime
  (under / across / conditions / regime).

Note the interplay with `style_harness.py`: `abstract_numbers_max: 3` caps
how many numbers the abstract may carry, while `S1-headline-number` requires
at least one. Both are needed — a numberless abstract and a spreadsheet
abstract are different failures.

## Run

```bash
python3 scripts/check_rules.py \
  --input recipes/06-abstract-structure/input \
  --config recipes/06-abstract-structure
# expect: exit 1 — no number, no comparison, no regime (vague abstract)

python3 scripts/check_rules.py \
  --input recipes/06-abstract-structure/input_fixed \
  --config recipes/06-abstract-structure
# expect: exit 0
```

## Agent usage

`required` rules scoped with `sections: '^abstract$'` are the cheapest
structural review you can automate: every vague-abstract failure mode
("we study X, we discuss Y") is a missing-required-pattern failure.
