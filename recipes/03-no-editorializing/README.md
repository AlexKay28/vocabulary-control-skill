# Recipe 03 — No editorializing (R9)

**From the paper:** DLLM §1 contained "the arm we were not rooting for
inherited every default" — advocacy, not measurement. `check_plot_twist_neutral`
made the introduction neutral prose or removed the passage. This recipe
generalizes the check to the standard surprise/advocacy vocabulary.

## Rules

- `R9-no-editorializing` (forbidden): plot twists, rooting for arms,
  "shockingly", etc. in §1.
- `R9-no-surprise-hedges` (forbidden): "surprisingly", "interestingly",
  "remarkably", "curiously" in all main sections + abstract.

## Run

```bash
python3 scripts/check_rules.py \
  --input recipes/03-no-editorializing/input \
  --config recipes/03-no-editorializing
# expect: exit 1 — all three editorializing hits quoted

python3 scripts/check_rules.py \
  --input recipes/03-no-editorializing/input_fixed \
  --config recipes/03-no-editorializing
# expect: exit 0 — same facts, neutral prose
```

## Agent usage

When a draft says a result is surprising, delete the adverb, keep the
number. Add venue-specific banned phrases to the alternation as reviewers
flag them; the list is a living document, the rule type never changes.
