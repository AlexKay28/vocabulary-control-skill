# vocabulary-control-skill

A corpus-grounded skill for controlling the prose of a technical paper (or
any text) so it reads like published, peer-reviewed writing — **measured,
not vibed**. Extracted from the DLLM-as-Service paper pipeline, where it
took all 20 sections of a real paper to a 20/20 pass against stylometric
comparison with published ML papers.

**The method in one line:** measure a reference corpus of actually-published
papers, hold your text to the same distribution, fix exactly what the
harness quotes, and gate on exit code 0 like pytest.

## 60-second demo

```bash
git clone https://github.com/AlexKay28/vocabulary-control-skill
cd vocabulary-control-skill
make demo
```

The demo paper has one clean section and one neuroslop section. The gate
fails (exit 1) and tells you exactly why — every failure is a quote, not a
score:

```
FAIL: 02_deployment — sentence_median (88 > 28), sentence_p90 (88 > 45),
sentence_gt40_pct (50.0% > 15.0%), passive_pct (50.0% > 25.0%),
metaphor_count (2 > 1), terminology_diffusion_model (3 > 2),
comma_splice_pct (50.0% > 10.0%)
```

Fix the quoted sentences, rerun, exit 0. That loop is the whole workflow.

## What it checks

| Harness | What it measures |
|---|---|
| `style_harness.py` | Sentence shape (median/p90/>40%), metaphor & neuroslop counter, terminology consistency (max 2 names per concept), forward refs, number density, comma splices, passive %, vocabulary overlap, Burrows' Cosine Delta, TF-IDF similarity, function-word & sentence-length distribution similarity — all vs the reference corpus |
| `eval_readability.py` | Flesch band (18–55 main text; *too readable is also a failure*), long-sentence caps, passive clusters, hedging, bracket density, words-between-numbers, acronyms expanded, over-explained definitions, repeated caveats, bare captions |
| `check_claims.py` | **Number provenance**: every number cited in prose must trace to a committed artifact JSON (exact, rounded, or within tolerance); untraced numbers are reported with their full sentence |
| `run_all.py` | Single gate: exit 0 = publishable |

## Why "corpus-grounded"

Every threshold in `config/settings.yaml` was derived from the bundled
`reference_corpus/` — 15 published ML papers (~141k words: LLaDA,
FlashAttention-2, LoRA, Llama 3, …) — not chosen by hand. Proof:

```bash
python3 scripts/derive_thresholds.py
# sentence_median_max: 28   (corpus median 21 + 7 slack)
# sentence_p90_max: 45      (corpus p90 — hard ceiling)
# sentence_gt40_pct_max: 15.0  (corpus 13.0% + 2.0 slack)
```

A threshold you cannot trace to a measurement is a vibe; `derive_thresholds.py`
recomputes them for your own field's corpus (see `examples/04-custom-corpus/`).

## Quickstart for your text

```bash
python3 scripts/run_all.py \
  --input your-text-dir \      # sections/*.tex + main.tex, or flat .tex/.md/.txt
  --artifacts your-results     # optional: enables number-provenance
echo $?                        # 0 = publishable
```

Configuration is one YAML file — `config/settings.yaml` is the default
profile, and `--config` points at any directory containing your own
`settings.yaml` (thresholds, banned patterns, terminology, prose-quality
patterns). Editing thresholds never requires touching code. PyYAML is used
if installed; a built-in subset parser covers everything else.

## Examples (each runnable, each with expected exit codes)

| # | Scenario |
|---|---|
| `01-ml-paper-latex` | Full pipeline: LaTeX paper, terminology map, artifact provenance; clean section passes, neuroslop section fails |
| `02-blog-post-markdown` | Markdown blog post, no artifacts, zero-metaphor profile |
| `03-strict-mode` | Same text passes default profile, fails strict — profiles are just YAML |
| `04-custom-corpus` | Build your own corpus, derive thresholds from it |
| `05-ci-gating` | pytest wrapper, pre-commit hook, GitHub Action |

Reports of a real 20/20 pass (`examples/style_report_v7.md`) and a real
failing later version (`examples/style_report_v9_FAILING.md`) are included —
the tool catches its own source project's drift.

## For agents

`SKILL.md` is the grounding-truth document: the method, the workflow, the
rules of thumb learned the hard way, and how to extend the skill to a new
project. `criteria/CRITERIA.md` is the "what done looks like" contract
template (Successful / Accurate / Interesting / Readable).

## Tests & development

```bash
make test            # 12 tests, stdlib unittest, no dependencies
make test-no-pyyaml  # same, forcing the built-in YAML parser
```

Pure Python stdlib. MIT licensed. See `CONTRIBUTING.md` for the one rule
that matters (traceable thresholds) and `CHANGELOG.md` for history.
