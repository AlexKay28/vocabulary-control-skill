#!/usr/bin/env python3
"""Evaluate readability and expression density of a text/paper.

Generalized extraction of the DLLM-as-Service readability harness.

  - readability: Flesch Reading Ease, sentence length, passive clusters, hedging
  - density:     number density, bracket density, words-per-number
  - prose quality (project patterns from settings.yaml `prose_quality:`):
      R4 acronyms expanded on first use
      R5 over-explained definitions
      R6 repeated caveats
      R7 bare figure/table captions (.tex only)

Usage:
  python3 eval_readability.py --input <paper-dir> [--config <dir>]
  python3 eval_readability.py --input mypaper --json
  python3 eval_readability.py --input mypaper --read     # readability only
  python3 eval_readability.py --input mypaper --density  # density only

Exit codes:
  0 = all checks pass
  1 = one or more checks fail
  2 = input error
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    DEFAULT_CONFIG, err, load_prose_quality, load_sections,
    load_thresholds, split_sentences, strip_latex,
)


def flesch_reading_ease(text: str) -> float:
    """Flesch Reading Ease, no external dependencies."""
    sentences = split_sentences(text)
    words = text.split()
    if not sentences or not words:
        return 0.0
    syllables = 0
    for word in words:
        clean = re.sub(r"[^a-zA-Z]", "", word).lower()
        if not clean:
            continue
        syllables += max(1, len(re.findall(r"[aeiouy]+", clean)))
    asl = len(words) / len(sentences)
    asw = syllables / len(words)
    return 206.835 - 1.015 * asl - 84.6 * asw


def check_readability(sections: dict, is_main: dict, th: dict) -> list:
    """Returns list of (section, metric, value, status, threshold)."""
    results = []
    for name, text in sorted(sections.items()):
        main = is_main.get(name, False)
        fre_min = th["flesch_main_min"] if main else th["flesch_appendix_min"]
        fre_max = th["flesch_main_max"] if main else 80

        sentences = split_sentences(text)
        if not sentences:
            continue
        word_counts = [len(s.split()) for s in sentences]
        median_wc = sorted(word_counts)[len(word_counts) // 2]
        long_40 = sum(1 for c in word_counts if c > 40)
        long_60 = sum(1 for c in word_counts if c > 60)
        fre = flesch_reading_ease(text)

        passive_re = re.compile(r"\b(?:was|is|were|are|be|been|being)\s+\w+(?:ed|en)\b", re.IGNORECASE)
        consecutive = best = 0
        for s in sentences:
            if passive_re.search(s):
                consecutive += 1
                best = max(best, consecutive)
            else:
                consecutive = 0

        hedge_re = re.compile(
            r"\b(?:may be|might be|could be|possibly|it appears|it seems|"
            r"arguably|presumably)\b", re.IGNORECASE)
        hedge_ratio = sum(1 for s in sentences if hedge_re.search(s)) / len(sentences)

        def add(metric, value, ok, threshold):
            results.append((name, metric, value, "PASS" if ok else "FAIL", threshold))

        add("flesch", f"{fre:.1f}", fre_min <= fre <= fre_max, f"[{fre_min}, {fre_max}]")
        add("median_words", str(median_wc),
            th["median_sentence_min"] <= median_wc <= th["median_sentence_max"],
            f"[{th['median_sentence_min']}, {th['median_sentence_max']}]")
        add("sentences_gt40", str(long_40), long_40 <= th["sentences_gt40_max"],
            f"<= {th['sentences_gt40_max']}")
        add("sentences_gt60", str(long_60), long_60 <= th["sentences_gt60_max"],
            f"<= {th['sentences_gt60_max']}")
        add("passive_cluster", str(best), best <= th["passive_cluster_max"],
            f"<= {th['passive_cluster_max']}")
        add("hedge_ratio", f"{hedge_ratio:.2f}", hedge_ratio <= th["hedge_per_sentence_max"],
            f"<= {th['hedge_per_sentence_max']}")
    return results


def _count_numbers(text: str) -> int:
    return len(re.findall(r"\b\d+\.?\d*\b", text))


def _count_brackets(text: str) -> int:
    brackets = re.findall(r"\([^)]+\)", text)
    return sum(1 for b in brackets if not re.search(r"~[,)]|[A-Z][a-z]+\s+(et al|&)", b))


def check_density(sections: dict, is_main: dict, th: dict) -> list:
    results = []
    total_numbers = total_words = total_brackets = 0
    for name, text in sorted(sections.items()):
        wc = len(text.split())
        if wc == 0:
            continue
        main = is_main.get(name, False)
        numbers = _count_numbers(text)
        brackets = _count_brackets(text)
        num_density = numbers / wc * 100
        brk_density = brackets / wc * 100
        words_per_num = wc / numbers if numbers > 0 else 999

        nd_th = th["number_density_main_max"] if main else th["number_density_abs_max"]
        results.append((name, "num_density", f"{num_density:.1f}",
                        "PASS" if num_density <= nd_th else "FAIL", f"<= {nd_th}"))
        bd_th = th["bracket_density_main_max"] if main else 5.0
        results.append((name, "brk_density", f"{brk_density:.1f}",
                        "PASS" if brk_density <= bd_th else "FAIL", f"<= {bd_th}"))
        wpn_ok = words_per_num >= th["words_per_number_min"] or not main
        results.append((name, "words_per_num", f"{words_per_num:.0f}",
                        "PASS" if wpn_ok else "FAIL", f">= {th['words_per_number_min']}"))
        if name.lower() == "abstract":
            ok = numbers <= th["abstract_numbers_max"]
            results.append((name, "abstract_numbers", str(numbers),
                            "PASS" if ok else "FAIL", f"<= {th['abstract_numbers_max']}"))
        if main:
            total_numbers += numbers
            total_words += wc
            total_brackets += brackets

    if total_words:
        agg_nd = total_numbers / total_words * 100
        agg_bd = total_brackets / total_words * 100
        agg_wpn = total_words / total_numbers if total_numbers else 999
        results.append(("MAIN_TOTAL", "num_density", f"{agg_nd:.1f}",
                        "PASS" if agg_nd <= th["number_density_main_max"] else "FAIL",
                        f"<= {th['number_density_main_max']}"))
        results.append(("MAIN_TOTAL", "brk_density", f"{agg_bd:.1f}",
                        "PASS" if agg_bd <= th["bracket_density_main_max"] else "FAIL",
                        f"<= {th['bracket_density_main_max']}"))
        results.append(("MAIN_TOTAL", "words_per_num", f"{agg_wpn:.0f}",
                        "PASS" if agg_wpn >= th["words_per_number_min"] else "FAIL",
                        f">= {th['words_per_number_min']}"))
    return results


def check_acronyms(sections: dict, acronyms: list) -> list:
    """R4: each configured acronym must be expanded at first use."""
    results = []
    full_text = "\n".join(sections.values())
    for acr in acronyms:
        # expanded if "long form (ACRONYM)" appears, or ACRYM never used
        expanded = re.search(
            rf"[a-z][a-z \-]{{2,40}}\s\({acr}\)", full_text, re.IGNORECASE)
        used = re.search(rf"\b{acr}\b", full_text)
        ok = bool(expanded) or not used
        results.append(("GLOBAL", f"acronym_{acr}", "ok" if ok else "expanded at first use?",
                        "PASS" if ok else "FAIL", "expansion or absence"))
    return results


def check_overexplained(sections: dict, patterns: list) -> list:
    """R5: flag definitions that restate what the formula already says."""
    results = []
    for name, text in sorted(sections.items()):
        hits = sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)
        results.append((name, "overexplained_def", str(hits),
                        "PASS" if hits == 0 else "FAIL", "<= 0"))
    return results


def check_caveats(sections: dict, patterns: list, max_per_section: int, exempt_re) -> list:
    """R6: same caveat repeated too often outside exempt sections."""
    results = []
    for name, text in sorted(sections.items()):
        if exempt_re and exempt_re.search(name):
            results.append((name, "repeated_caveats", "n/a", "PASS", "exempt section"))
            continue
        total = sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)
        results.append((name, "repeated_caveats", str(total),
                        "PASS" if total <= max_per_section else "FAIL",
                        f"<= {max_per_section}"))
    return results


def check_captions(raw_sections: dict) -> list:
    """R7 (.tex only): every \\caption should carry a number or a comparison."""
    results = []
    cap_re = re.compile(r"\\caption\{([^}]*)\}")
    for name, raw in sorted(raw_sections.items()):
        captions = cap_re.findall(raw)
        if not captions:
            continue
        bare = 0
        for cap in captions:
            has_num = bool(re.search(r"\d", cap))
            has_cmp = bool(re.search(r"vs|\\times|×|/|ratio|advantage", cap, re.IGNORECASE))
            if not (has_num or has_cmp):
                bare += 1
        results.append((name, "bare_captions", str(bare),
                        "PASS" if bare == 0 else "FAIL", "<= 0"))
    return results


def print_table(results: list, title: str) -> int:
    print(f"\n{'=' * 80}\n  {title}\n{'=' * 80}")
    print(f"  {'Section':<25} {'Metric':<20} {'Value':>8}  {'Status':<6} Threshold")
    print(f"  {'-' * 75}")
    fails = 0
    for section, metric, value, status, threshold in results:
        marker = "  " if status == "PASS" else ">>"
        print(f"{marker} {section:<25} {metric:<20} {value:>8}  {status:<6} {threshold}")
        if status == "FAIL":
            fails += 1
    print(f"  {'-' * 75}")
    n_checks = len(results)
    print(f"  [{title}] {n_checks - fails}/{n_checks} checks pass")
    return fails


def main():
    ap = argparse.ArgumentParser(description="Readability + density harness")
    ap.add_argument("--input", required=True)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--main-regex", default=r"^(0[1-8]|abstract)")
    ap.add_argument("--read", action="store_true")
    ap.add_argument("--density", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    th = load_thresholds(args.config)
    pq = load_prose_quality(args.config)
    sections, raw, is_main = load_sections(args.input, args.main_regex)

    as_json = args.json
    do_read = args.read or as_json or not (args.read or args.density)
    do_density = args.density or as_json or not (args.read or args.density)

    all_results = []
    if do_read:
        all_results += check_readability(sections, is_main, th)
    if do_density:
        all_results += check_density(sections, is_main, th)

    exempt_re = re.compile(pq.get("caveat_exempt_regex", r"$^")) if pq else None
    if pq:
        if pq.get("acronyms"):
            all_results += check_acronyms(sections, pq["acronyms"])
        if pq.get("overexplanation_patterns"):
            all_results += check_overexplained(sections, pq["overexplanation_patterns"])
        if pq.get("caveat_patterns"):
            all_results += check_caveats(
                sections, pq["caveat_patterns"],
                pq.get("caveat_max_per_section", 4), exempt_re)
    # R7 only makes sense for LaTeX sources
    if any(v.strip().startswith("\\") or "\\caption" in v for v in raw.values()):
        all_results += check_captions(raw)

    total_fails = 0
    if as_json:
        out = {
            "results": [
                {"section": s, "metric": m, "value": v, "status": st, "threshold": t}
                for s, m, v, st, t in all_results
            ],
            "total_checks": len(all_results),
            "total_fails": sum(1 for r in all_results if r[3] == "FAIL"),
        }
        print(json.dumps(out, indent=2))
    else:
        groups = []
        if do_read:
            groups.append(("READABILITY", [r for r in all_results if r[1] in
                           {"flesch", "median_words", "sentences_gt40", "sentences_gt60",
                            "passive_cluster", "hedge_ratio"}]))
        if do_density:
            groups.append(("EXPRESSION DENSITY", [r for r in all_results if r[1] in
                           {"num_density", "brk_density", "words_per_num", "abstract_numbers"}]))
        pq_results = [r for r in all_results if r[1] in
                      {"overexplained_def", "repeated_caveats", "bare_captions"}
                      or r[1].startswith("acronym_")]
        if pq_results:
            groups.append(("PROSE QUALITY", pq_results))
        for title, rows in groups:
            if rows:
                total_fails += print_table(rows, title)

        print(f"\n{'=' * 80}")
        if total_fails == 0:
            print("  ALL CHECKS PASS")
        else:
            print(f"  {total_fails} CHECK(S) FAILED")
        print(f"{'=' * 80}")

    sys.exit(1 if any(r[3] == "FAIL" for r in all_results) else 0)


if __name__ == "__main__":
    main()
