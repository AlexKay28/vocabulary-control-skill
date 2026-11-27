# SKILL — Vocabulary & Prose Control for Papers (Corpus-Grounded)

This is a **grounding-truth method** for controlling the text of a technical
paper so it reads like published, peer-reviewed prose instead of AI-assisted
drafts ("neuroslop"). It was extracted from a real paper pipeline
(DLLM-as-Service) where it took 20 sections from "obviously AI-written" to
20/20 passing against stylometric comparison with published ML papers.

**Core principle:** *good prose is a measurable distribution, not a vibe.*
Every threshold in this skill was derived by measuring a 141k-word corpus of
actually-published ML papers (LLaDA, FlashAttention-2, LoRA, llama3, …) and
holding the drafted text to the same distribution. The text is judged the
same way a stylometer would judge it — no human taste required, and no room
for the LLM to grade its own homework.

## What "controlled text" means here

A text is under control when, per section:

1. **Sentences have the shape of real papers** — median 10–28 words,
   p90 ≤ 45, almost nothing over 40.
2. **At most one metaphor/colloquialism per section, zero neuroslop** —
   "metered taxi", "delve", "tapestry", "unlock the", all counted by regex.
3. **One concept, at most two names** — terminology drift is counted, not
   felt.
4. **Numbers are sparse and all trace to artifacts** — ≤ 4 per 100 words in
   main text, ≥ 25 prose words between numbers, and every cited number must
   exist in a committed results file.
5. **Readability is in-band, not maximal** — Flesch 18–55 for main text.
   Over-55 is as much a failure as under-18: dumbed-down prose is a defect.
6. **Passive voice ≤ 25%, no passive clusters > 3, hedging < 50%.**
7. **No self-contradiction**: no sentence may assert the opposite of its own
   table (header/table consistency in the original `verify_numbers.py`).

## The harness (three scripts, one gate)

All scripts live in `scripts/`, all knobs in `config/`. Pure Python stdlib.

```bash
# Full suite, pytest-style gate:
python3 scripts/run_all.py --input <paper-dir> [--artifacts <results-dir>]
# exit 0 = publishable, exit 1 = fix something

# Individual harnesses:
python3 scripts/style_harness.py   --input <dir>          # 13 stylometric metrics vs corpus
python3 scripts/eval_readability.py --input <dir>        # Flesch, sentence shape, density
python3 scripts/check_claims.py    --input <dir> --artifacts <dir>  # number provenance
```

`--input` accepts a directory with `sections/*.tex` (+`main.tex` abstract), or
flat `.tex` / `.md` / `.txt` files. Markdown works too — the skill is not
LaTeX-specific.

Exit codes are the contract: **0 = pass, 1 = check failed, 2 = input error.**
Wire them into your build loop the way you wire pytest. A paper (or any
text) is "done" only when the suite exits 0.

## The workflow that made it work (use exactly this loop)

1. **Draft a section.**
2. **Run the harness on it.** Failures are not scores, they are a to-do list:
   each named check quotes the offending sentence — long sentences are
   printed with word counts, banned patterns with context, untraced numbers
   with the sentence they appear in.
3. **Fix precisely what is listed** — split the quoted sentences, delete the
   quoted metaphor, rename the drifting term, add the missing artifact or
   delete the number.
4. **Re-run until exit 0.** Do not tune thresholds to pass; tune text.

Rules of thumb learned the hard way in the original pipeline:

- **Metaphors are a >1-per-section budget, not a ban.** One good one is
  fine; regex-listed patterns just stop them from compounding.
- **The abstract is a special section**: ≤ 3 inline numbers, everything
  (claim, comparison, headline number, regime) in ~150 words.
- **Related work gets a forward-reference allowance**; appendices get looser
  vocabulary-overlap and density limits — appendix prose is naturally denser.
- **Never fix a failing metric globally** (rewrite whole sections). Fix the
  quoted sentences, re-measure; the distribution moves fast.
- Don't add neuroslop regexes back to the *threshold list* — add them to
  `banned_patterns:` in `config/settings.yaml`, no code.

## Config (all project-specific knowledge lives here)

The single source of truth is **`config/settings.yaml`** — one YAML file
covering thresholds, banned patterns, terminology, and prose-quality
patterns. `--config` points the scripts at any directory containing a
`settings.yaml`, so a profile is just a YAML file (see `examples/` for five
profiles). PyYAML is used when installed; a built-in subset parser
(`common.parse_yaml`) handles the file otherwise, and the test suite asserts
both paths produce identical results.

| Settings section | Controls |
|---|---|
| `thresholds:` | every counter and its limit (corpus-derived defaults) |
| `banned_patterns:` | metaphor/neuroslop regexes, editable without code |
| `terminology:` | concept → acceptable names (max 2 by default) |
| `prose_quality:` | acronyms, overexplained definitions, repeated caveats, claim exemptions |
| `reference_corpus/` | 15 published papers + MANIFEST; the yardstick itself |

Section classification: a section is "main" (strict limits) if its filename
matches `--main-regex` (default `^(0[1-8]|abstract)`); everything else is
appendix-like (relaxed limits). Change per project, keep the two-tier idea:
main text must read cleanly; appendices are allowed to be dense.

## Where the thresholds come from (and how to re-derive them)

The defaults were derived from the bundled corpus, not chosen by hand —
`python3 scripts/derive_thresholds.py` recomputes them and reproduces the
shipped values (28 / 45 / 15.0) exactly. Two kinds of thresholds exist and
the script labels them honestly: **corpus-grounded** (sentence shape,
vocab overlap — measured + documented slack) and **editorial** (number
density 4.0 while the corpus sits at 9.6 — the method holds your text
tighter than the average published paper, and says so). For a new field,
build a corpus of published papers from that field and re-derive; see
`examples/04-custom-corpus/`.

## Extending to a new project

1. Point `--input` at your paper/text directory.
2. Copy `config/settings.yaml` into your project as the project profile and
   copy `criteria/CRITERIA.md` alongside it; fill the placeholders, and map
   each project-specific check to a script or a settings entry.
3. Replace the example concepts in `terminology:` with your own (the
   max-2-names rule needs your real terms to work).
4. Add project metaphors to `banned_patterns:` (one edit, no code).
5. Provide `--artifacts` (results JSONs) and run `check_claims` — every
   number in prose must exist there. Numbers stored as JSON strings count
   too; matches accept exact, rounded (1–3 dp), or within
   `match_tolerance_pct` (default 0.1%) values, because prose legitimately
   rounds artifact values. Add explicit `claim_exemptions` for things like
   config knobs ("K=8") with a stated reason rather than deleting checks.
6. Optionally: build your own reference corpus (any published papers from
   your field as .txt files + MANIFEST.json), pass `--corpus`, and re-derive
   thresholds with `derive_thresholds.py`.

## What each script actually measures

**style_harness.py** (per section, vs corpus): sentence length (median/p90/
%>40), banned-pattern count, terminology names, forward refs per 1k words,
number density, comma-splice %, 2/3-gram JSD (informational), vocabulary
overlap, passive %, abstract numbers, Burrows' Cosine Delta, TF-IDF cosine
similarity to nearest corpus doc, function-word similarity, sentence-length
histogram intersection. Writes a markdown + JSON report.

**eval_readability.py**: Flesch band per section type, sentence-length
checks, passive clusters, hedge ratio, number/bracket density, words-per-
number, acronym expansion (R4), overexplained definitions (R5), repeated
caveats (R6), bare captions (R7, .tex only).

**check_claims.py**: flattens artifact JSONs into a known-number set
(including numeric strings), extracts every number from prose, and lists
untraced ones with sentence context. Matches accept exact, rounded (1–3 dp),
or within `match_tolerance_pct` (default 0.1%). This is the generalized core
of the original `verify_numbers.py`, which also proved the sharper
claim-level checks worth keeping as method: no header/table contradictions,
one canonical number per claim, precision policy fixed per metric. Implement
those per project inside `check_claims` or alongside it — see
`criteria/CRITERIA.md`.

**check_rules.py**: declarative rule engine for project-specific criteria —
the checks that were bespoke Python in the original `verify_numbers.py`,
now YAML. Six rule types: `forbidden` (retracted numbers/phrases must not
resurface), `required` (punchlines, caveats, headline numbers must not be
buried by refactors), `max_count` (caveat budgets), `proximity` (every ratio
names its arm within N words), `first_use` (asymmetries disclosed inline at
first use), `precision` (fixed decimals per metric). `recipes/` contains six
agent-ready recipes taken directly from the arXiv paper (A1/A2, I3/I5, R9,
A3/A6, A7, S1), each with a failing fixture, a fixed fixture, and the story.
Runs automatically inside `run_all.py` when `rules:` is non-empty.

**derive_thresholds.py**: recomputes corpus-grounded thresholds from any
`--corpus` (and honestly labels editorial ones); on the shipped corpus it
reproduces the defaults exactly — the proof that defaults are derived, not
vibes.

## Origin

Extracted from the DLLM-as-Service paper pipeline (`paper/style_harness.py`,
`paper/eval_readability.py`, `paper/verify_numbers.py`, `paper/CRITERIA.md`,
`paper/reference_corpus/`). The exemplar report in `examples/` shows a real
20/20-passing paper measured with this method.
