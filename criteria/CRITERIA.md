# Paper Criteria

What "done" looks like for a text written under this skill. Four categories —
**successful, accurate, interesting, readable** — each with measurable
checks. This is the project-facing contract template: copy it into your
project and fill the placeholders in `[brackets]`. Most checks are enforced
by the harness scripts (all must exit 0); the rest are manual review points
flagged at the end of each section.

The scripts take `--input <dir>` (and `--artifacts <dir>` for S3/A-checks).
See `SKILL.md` for the workflow.

---

## 1. Successful

A paper succeeds when a reader can reconstruct the claim, the comparison,
and the regime from the text alone, and every cited number traces to a
committed artifact.

| # | Check | How measured |
|---|---|---|
| S1 | Abstract states: the claim, the comparison (arms matched on what), the headline number, and the regime. | Manual / abstract-number count (`style_harness.py`). |
| S2 | Every contribution in §1 maps to a section that delivers it, and the conclusion restates the regime. | Manual. |
| S3 | Every number cited in prose traces to a result JSON. | `check_claims.py`. |
| S4 | Declared defect magnitudes match their artifacts. | `check_claims.py` + manual spot-check. |
| S5 | Value macros (injected numbers) equal their artifact fields within tolerance — no drift after re-measurement. | `check_claims.py`. |
| S6 | Paper compiles: 0 errors, 0 undefined refs, 0 overfull boxes. | `[your build command, log parsed]`. |

## 2. Accurate

A paper is accurate when no sentence asserts the opposite of its own data,
and no comparison silently switches the arm it is measuring.

| # | Check | How measured |
|---|---|---|
| A1 | No sentence claims the pre-correction advantage "survived" if corrections changed it. *(Original case: 15.6× was the defective harness; corrected to 2.5×.)* | `[project-specific check in check_claims.py]`. |
| A2 | A bold paragraph header must not contradict the table below it. | Manual / `[project-specific]`. |
| A3 | Every ratio in prose names its configuration or cites a table/figure that does. | Manual / `[project-specific]`. |
| A4 | Macro values match artifact values (no drift). | `check_claims.py`. |
| A5 | Table headers match their rows (column count, labels, units). | Manual. |
| A6 | Any asymmetry between compared arms is disclosed inline at first use, not only in the threats section. | Manual. |
| A7 | Numeric precision policy holds (`[latency 1 dp, F1 3 dp, ratios 1 dp]`). | `[project-specific policy]`. |
| A8 | Tooling-version asymmetries between arms are disclosed in the threats section, not hidden. | Manual. |

## 3. Interesting

A paper is interesting when the stakes are concrete and the punchlines are
not buried.

| # | Check | How measured |
|---|---|---|
| I1 | §1 shows one concrete input → output example, with scored vs excluded fields marked. | `[project-specific]`. |
| I2 | The task's stakes are named concretely, not abstractly. | Manual. |
| I3 | The headline punchline appears in the results section, not only in the limitations section. | Manual / `[project-specific]`. |
| I4 | One canonical ratio per claim; cross-harness variants demoted to a footnote or parenthetical. | Manual. |
| I5 | Major caveats live in the main text, not buried in the limits section. | Manual. |

## 4. Readable

A paper is readable when a first-time reader can follow it without
re-reading sentences or hunting for definitions.

| # | Check | How measured |
|---|---|---|
| R1 | Flesch Reading Ease in [18, 55] for main text, [20, 80] for appendices. | `eval_readability.py`. |
| R2 | Median sentence length in [10, 28] words. | `eval_readability.py`, `style_harness.py`. |
| R3 | ≤ 2 sentences > 40 words per section; 0 sentences > 60 words. | `eval_readability.py`. |
| R4 | Acronyms expanded on first use (`[SLA, SOC, EOS, KV, MoE]`). | `eval_readability.py` + `config/prose_quality.json`. |
| R5 | No over-explained definitions (glossing what the formula already states). | `eval_readability.py` + `config/prose_quality.json`. |
| R6 | Repeated caveats consolidated — appear inline at most `[4]` times outside the threats section. | `eval_readability.py` + `config/prose_quality.json`. |
| R7 | Figure captions are self-contained: each states what is shown and the finding. | `eval_readability.py` (bare-caption proxy) + manual. |
| R8 | Number density ≤ 4.0 / 100 words in main text; bracket density ≤ 1.5 / 100 words; ≥ 25 words between numbers. | `eval_readability.py`, `style_harness.py`. |
| R9 | No editorializing ("plot twist", "the arm we were not rooting for") — neutral prose only. | `banned_patterns.txt` + manual. |
| R10 | Metaphors/colloquialisms ≤ 1 per section; zero generic neuroslop. | `style_harness.py` + `config/banned_patterns.txt`. |
| R11 | One concept carries at most 2 distinct names across the text. | `style_harness.py` + `config/terminology.json`. |
| R12 | Passive voice ≤ 25% of sentences, no cluster > 3; hedging < 50% of sentences. | `eval_readability.py`, `style_harness.py`. |

---

## How to run

```bash
# Stylometric + terminology + metaphor checks (needs reference_corpus/)
python3 scripts/style_harness.py --input <paper-dir>

# Readability + density + prose-quality patterns
python3 scripts/eval_readability.py --input <paper-dir>

# Provenance: every prose number must exist in the artifact JSONs
python3 scripts/check_claims.py --input <paper-dir> --artifacts <results-dir>

# Or the whole gate at once:
python3 scripts/run_all.py --input <paper-dir> --artifacts <results-dir>
# All must exit 0 before a version is publishable.
```

## Manual review points (not automated)

- S1/S2: abstract ↔ contributions ↔ conclusion alignment.
- I2: stakes named concretely.
- A6/A8: asymmetries disclosed (first use and threats section).
- Figure content (captions are checked; rendered images are not).
