# vocabulary-control-skill

A corpus-grounded skill for controlling the prose of a technical paper (or
any text) so it reads like published, peer-reviewed writing — measured, not
vibed. Extracted from the DLLM-as-Service paper pipeline, where it took all
20 sections to a 20/20 pass against stylometric comparison with real
published ML papers.

**The method in one line:** measure a reference corpus of actually-published
papers, hold your text to the same distribution, fix exactly what the
harness quotes, and gate on exit code 0 like pytest.

- `SKILL.md` — the grounding-truth instructions for AI agents: method,
  workflow, and rules of thumb.
- `scripts/` — `style_harness.py` (13 stylometric metrics), `eval_readability.py`
  (Flesch bands, sentence shape, density), `check_claims.py` (every prose
  number must trace to an artifact), `run_all.py` (single pytest-style gate).
- `config/` — all thresholds and project-specific patterns (metaphors,
  terminology, acronyms) as data, editable without touching code.
- `criteria/CRITERIA.md` — the "what done looks like" contract template
  (Successful / Accurate / Interesting / Readable).
- `reference_corpus/` — 15 published ML papers (~141k words) + manifest,
  the yardstick the thresholds were derived from.
- `examples/style_report_v7.md` — a real 20/20-passing report.

Pure Python stdlib, no dependencies.

```bash
python3 scripts/run_all.py --input your-paper-dir --artifacts your-results-dir
echo $?   # 0 = publishable
```

Works with LaTeX (`sections/*.tex` + `main.tex`) and plain Markdown/text
directories alike. See `SKILL.md` for the full workflow and per-script usage.
