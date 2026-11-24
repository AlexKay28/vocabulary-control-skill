# Example 04 — Custom reference corpus + derived thresholds

The default `reference_corpus/` is 15 published ML papers (~141k words).
For another field — systems, economics, medicine — build your own: drop
plain-text versions of published papers into a directory and derive the
thresholds from them instead of trusting the defaults.

## Run it

```bash
python3 scripts/derive_thresholds.py \
  --corpus examples/04-custom-corpus/mini-corpus
# prints corpus measurements + a `thresholds:` block ready to paste into
# settings.yaml. With this mini-corpus the suggested sentence_p90_max is
# lower than the default 45 — tiny corpora yield tight, noisy estimates;
# use at least ~10 papers in practice.

python3 scripts/derive_thresholds.py \
  --corpus examples/04-custom-corpus/mini-corpus \
  --out my-thresholds.yaml
# same, written to a file

# then use it:
python3 scripts/style_harness.py --input <your-text> \
  --corpus examples/04-custom-corpus/mini-corpus --quiet
```

## What the script reports (and why)

- **Corpus-grounded thresholds** come from measurements + documented slack
  (e.g. `sentence_median_max = corpus median + 7`). On the shipped corpus
  this reproduces the defaults exactly (28 / 45 / 15.0), which is the
  validation that the defaults are derived, not vibes.
- **Editorial thresholds** (`number_density_max: 4.0` while the corpus sits
  at 9.6) are deliberately tighter than average published prose — the script
  says so in comments rather than pretending otherwise.
- **The vocab-overlap probe** splits your corpus in half and measures how
  much of one half's vocabulary the other half uses; that is what "sounds
  like the field" means numerically.

MANIFEST.json (title/arxiv/venue per file, like `reference_corpus/`) is
optional; without it, every `*.txt` in the directory is used.
