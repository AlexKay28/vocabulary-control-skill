#!/usr/bin/env python3
"""Derive thresholds from a reference corpus instead of choosing them by hand.

The grounding step of the method: a threshold you cannot trace to a
measurement is a vibe. This script measures your corpus and prints a
`thresholds:` block ready to paste into config/settings.yaml.

Two kinds of thresholds exist, and the script labels them honestly:

  CORPUS-GROUNDED — taken directly from corpus measurements (+ slack):
      sentence_median_max, sentence_p90_max, sentence_gt40_pct_max,
      vocab_overlap_min (half-corpus probe: how much of half the corpus'
      vocabulary the other half uses), sentence shape in general.

  EDITORIAL — the method deliberately holds your text tighter than the
      average published paper (corpus number density is ~9.6/100 words, but
      the cap is 4.0): these keep the defaults and say so in comments.

Usage:
  python3 derive_thresholds.py --corpus <dir>
  python3 derive_thresholds.py --corpus <dir> --out thresholds_snippet.yaml
"""

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    DEFAULT_CORPUS, err, load_corpus, corpus_to_prose, split_sentences,
)

import re


def _tokens(text: str) -> list:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 1]


def _pct(values: list, q: float) -> float:
    vals = sorted(values)
    if not vals:
        return 0.0
    return vals[min(len(vals) - 1, int(len(vals) * q))]


def main():
    ap = argparse.ArgumentParser(description="Derive thresholds from a corpus")
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    ap.add_argument("--out", default=None, help="Write YAML snippet to file")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    if len(corpus) < 2:
        err("ERROR: need at least 2 corpus documents for the vocab-overlap probe")

    all_text = "\n".join(corpus_to_prose(t) for t in corpus.values())
    sentences = split_sentences(all_text)
    lengths = [len(s.split()) for s in sentences if s.split()]
    n_words = len(all_text.split()) or 1
    numbers = len(re.findall(r"\b\d[\d,.]*\b", all_text))

    median = _pct(lengths, 0.5)
    p90 = _pct(lengths, 0.9)
    gt40 = sum(1 for l in lengths if l > 40) / len(lengths) * 100 if lengths else 0
    density = numbers / n_words * 100

    # Vocab-overlap probe: split corpus docs in half; how much of half A's
    # vocabulary does half B use? That number is what "sounds like the field".
    ids = sorted(corpus)
    half = len(ids) // 2
    flat_a = set()
    for i in range(half):
        flat_a |= set(_tokens(corpus_to_prose(corpus[ids[i]])))
    flat_b = set()
    for i in range(half, len(ids)):
        flat_b |= set(_tokens(corpus_to_prose(corpus[ids[i]])))
    overlap_probe = len(flat_a & flat_b) / len(flat_b) if flat_b else 0.65

    # Suggested values (slack rules documented inline)
    sugg = {
        "sentence_median_max": round(median + 7),
        "sentence_median_min": 10,
        "sentence_p90_max": round(p90),
        "sentence_gt40_pct_max": round(gt40 + 2.0, 1),
        "vocab_overlap_min": round(max(0.55, overlap_probe * 0.92), 2),
        "vocab_overlap_appendix_min": round(max(0.45, overlap_probe * 0.92 - 0.10), 2),
    }

    snippet = f"""# thresholds: derived from your corpus by scripts/derive_thresholds.py
# Corpus: {len(corpus)} documents, {n_words:,} words, {len(sentences):,} sentences
#
# Measured: sentence median={median}, p90={p90}, >40-word sentences={gt40:.1f}%,
# number density={density:.1f}/100 words, half-corpus vocab overlap={overlap_probe:.2f}

thresholds:
  # ── corpus-grounded (measured + slack) ──
  sentence_median_max: {sugg['sentence_median_max']}      # corpus median {median} + 7 slack
  sentence_median_min: 10              # fixed floor: shorter reads choppy
  sentence_p90_max: {sugg['sentence_p90_max']}           # corpus p90 — hard ceiling
  sentence_gt40_pct_max: {sugg['sentence_gt40_pct_max']}   # corpus {gt40:.1f}% + 2.0 slack
  vocab_overlap_min: {sugg['vocab_overlap_min']}          # half-corpus probe {overlap_probe:.2f} × 0.92
  vocab_overlap_appendix_min: {sugg['vocab_overlap_appendix_min']}  # appendices use denser jargon

  # ── editorial (deliberately tighter than the average published paper) ──
  metaphor_max_per_section: 1          # method choice, not corpus-derived
  terminology_names_max: 2             # one concept, two names at most
  forward_ref_per_1k_max: 8.0          # main-text forward references
  number_density_max: 4.0              # corpus is {density:.1f} — the method caps at 4.0
  abstract_numbers_max: 3              # numbers allowed in the abstract
  passive_pct_max: 25.0                # % of passive sentences
  comma_splice_pct_max: 10.0           # % of 3+-clause comma splices
  flesch_main_min: 18                  # readability band: readable but not dumbed down
  flesch_main_max: 55
  match_tolerance_pct: 0.1             # prose numbers match artifacts within 0.1%
"""

    print(snippet)
    if args.out:
        Path(args.out).write_text(snippet)
        print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
