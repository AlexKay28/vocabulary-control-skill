#!/usr/bin/env python3
"""Style harness: compare paper prose against a reference corpus of published papers.

Grounding-truth tool extracted from the DLLM-as-Service paper pipeline. It
measures your text the same way a stylometer would, then holds it to
thresholds derived from a corpus of real published papers — so "good prose"
is defined by evidence, not vibes.

Metrics (all compared section-by-section against the corpus):
  1.  Sentence length (median, p90, % > 40 words)
  2.  Metaphor/colloquialism/neuroslop density (banned_patterns.txt, max per section)
  3.  Terminology consistency (distinct names for the same concept)
  4.  Forward-reference density (per 1000 words)
  5.  Number density (numbers per 100 words)
  6.  Comma-splice index (3+ comma-separated clauses)
  7.  N-gram overlap (2/3-gram JSD divergence vs corpus)
  8.  Vocabulary overlap (fraction of your words found in the corpus)
  9.  Passive-voice ratio
  10. Abstract number count
  11. Burrows' Cosine Delta (stylometric distance)
  12. TF-IDF cosine similarity to best-matching corpus doc
  13. Function-word + sentence-length-distribution similarity

Usage:
  python3 style_harness.py --input <paper-dir> [--corpus <dir>] [--config <dir>]
  python3 style_harness.py --input mypaper --out reports/
  python3 style_harness.py --input mypaper --json
  python3 style_harness.py --input mypaper --section 01_introduction --quiet

Exit codes:
  0 = all checks pass
  1 = one or more checks fail
  2 = configuration/input error
"""

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    DEFAULT_CONFIG, DEFAULT_CORPUS, err,
    load_banned_patterns, load_corpus, load_sections, load_terminology,
    load_thresholds, corpus_to_prose, count_numbers, count_words,
    split_sentences,
)

# ─── stylometric metrics ──────────────────────────────────────────────────

FUNCTION_WORDS = set("""
the a an and or but in on at to for of with by from as is are was were be been being
have has had do does did will would can could should may might must this that these those
it its they them their there here where when how what which who whom whose
not no nor so than too very just only also even still yet already
we us our ours you your yours he him his she her hers
about above after again against all am any because before below between both during each
few further into more most other own same some such than through under until up down out
off over under again further then once
if though although unless since until while whereas whether
one two three first second third last next both either neither each every
said says say said make makes made go goes went get gets got take takes took come comes came
see sees saw know knows knew think thinks thought use uses used find finds found
""".split())

STOPWORDS = FUNCTION_WORDS | set("""
s t re ve ll d m i me my mine
""".split())


def cosine_similarity_vec(v1: dict, v2: dict) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in v1 if k in v2)
    mag1 = math.sqrt(sum(v * v for v in v1.values()))
    mag2 = math.sqrt(sum(v * v for v in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def relative_freq(tokens: list, word_list: set) -> dict:
    freq = Counter(w for w in tokens if w in word_list)
    total = sum(freq.values()) or 1
    return {w: c / total for w, c in freq.items()}


def function_word_similarity(section_tokens: list, corpus_tokens: list) -> float:
    """Cosine similarity on function-word relative frequencies (syntax style)."""
    return cosine_similarity_vec(
        relative_freq(section_tokens, FUNCTION_WORDS),
        relative_freq(corpus_tokens, FUNCTION_WORDS),
    )


def burrows_cosine_delta(section_tokens: list, corpus_doc_tokens: list) -> float:
    """Burrows' Cosine Delta: stylometric distance to the closest corpus doc."""
    N_MFW = 50
    doc_freqs = []
    for doc_tokens in corpus_doc_tokens:
        freq = Counter(doc_tokens)
        total = sum(freq.values()) or 1
        doc_freqs.append({w: c / total for w, c in freq.items()})

    all_words = Counter()
    for doc_tokens in corpus_doc_tokens:
        all_words.update(doc_tokens)
    mfw = [w for w, _ in all_words.most_common(N_MFW)]

    means, stds = {}, {}
    for w in mfw:
        vals = [df.get(w, 0) for df in doc_freqs]
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        means[w] = mean
        stds[w] = math.sqrt(variance) if variance > 0 else 0.0001

    sec_freq = Counter(section_tokens)
    sec_total = sum(sec_freq.values()) or 1
    sec_z = {
        w: (sec_freq.get(w, 0) / sec_total - means[w]) / stds[w]
        for w in mfw
    }

    best_sim = 0.0
    for df in doc_freqs:
        doc_z = {
            w: (df.get(w, 0) - means[w]) / stds[w]
            for w in mfw
        }
        sim = cosine_similarity_vec(sec_z, doc_z)
        best_sim = max(best_sim, sim)
    return 1.0 - best_sim  # lower = more similar


def sentence_length_similarity(section_text: str, corpus_sentence_lengths: list) -> float:
    """Histogram intersection of sentence-length distributions (1.0 = identical)."""
    sec_lengths = [len(s.split()) for s in split_sentences(section_text) if s.split()]
    if not sec_lengths or not corpus_sentence_lengths:
        return 0.0
    max_bin = 60
    sec_hist = [0] * (max_bin + 1)
    for l in sec_lengths:
        sec_hist[min(l, max_bin)] += 1
    sec_total = sum(sec_hist) or 1
    sec_hist = [c / sec_total for c in sec_hist]
    corp_hist = [0] * (max_bin + 1)
    for l in corpus_sentence_lengths:
        corp_hist[min(l, max_bin)] += 1
    corp_total = sum(corp_hist) or 1
    corp_hist = [c / corp_total for c in corp_hist]
    return sum(min(a, b) for a, b in zip(sec_hist, corp_hist))


def tfidf_cosine_similarity(section_text: str, corpus_docs: list) -> float:
    """TF-IDF cosine similarity to the best-matching corpus document."""
    n_docs = len(corpus_docs)
    df = Counter()
    for doc in corpus_docs:
        for w in set(doc):
            df[w] += 1
    idf = {w: math.log((1 + n_docs) / (1 + d)) + 1 for w, d in df.items()}

    def tfidf_vector(tokens):
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        return {w: (c / total) * idf.get(w, 0) for w, c in tf.items()}

    doc_vectors = [tfidf_vector(doc) for doc in corpus_docs]
    sec_tokens = [w for w in re.findall(r"[a-z]+", section_text.lower()) if len(w) > 1]
    sec_vec = tfidf_vector(sec_tokens)
    return max(
        (cosine_similarity_vec(sec_vec, dv) for dv in doc_vectors),
        default=0.0,
    )


# ─── text analysis ─────────────────────────────────────────────────────────

def find_metaphors(text: str, metaphor_re) -> list:
    """Find banned-pattern hits; counts unique sentences, not word matches."""
    results = []
    seen_sentences = set()
    for m in metaphor_re.finditer(text):
        start = max(0, text.rfind(".", 0, m.start()) + 1)
        end = text.find(".", m.end())
        if end == -1:
            end = len(text)
        sentence = text[start:end].strip()
        sent_key = sentence[:100]
        if sent_key in seen_sentences:
            continue
        seen_sentences.add(sent_key)
        results.append({"phrase": m.group(), "context": sentence[:200]})
    return results


def check_terminology(text: str, terminology: dict) -> dict:
    """Check terminology consistency for each configured concept."""
    results = {}
    for concept, spec in terminology.items():
        groups = spec.get("groups", {})
        names_found = set()
        for pattern in spec.get("patterns", []):
            for match in re.findall(pattern, text, re.IGNORECASE):
                name = match.strip().lower() if isinstance(match, str) else match[0].strip().lower()
                name = groups.get(name, name)
                names_found.add(name)
        results[concept] = {
            "count": len(names_found),
            "names": sorted(names_found),
            "canonical": spec.get("canonical", concept),
        }
    return results


FORWARD_REF_PATTERNS = [
    r"Appendix~?\\ref",
    r"see [A-Z]ppendix",
    r"\\S\\ref",
    r"Section~?\\ref",
    r"Figure~?\\ref",
    r"Table~?\\ref",
    r"Eq\.~?\\ref",
    r"\bAppendix\b",
    r"\bsee (?:Section|Figure|Table) ",
]


def count_forward_refs(text: str) -> int:
    return sum(len(re.findall(p, text)) for p in FORWARD_REF_PATTERNS)


def count_comma_splices(text: str) -> int:
    """Heuristic: sentences with 3+ comma-separated independent-looking clauses."""
    count = 0
    for s in split_sentences(text):
        clauses = len(re.findall(r",\s+(?:and|but|or|so|yet|for|nor)\s+", s))
        comma_parts = s.split(",")
        if len(comma_parts) >= 4:
            verb_pattern = (
                r"\b(?:is|are|was|were|be|been|has|have|had|do|does|did|will|would|"
                r"can|could|should|may|might|must|pay|costs|grows|climbs|drops|wins|"
                r"fails|holds|takes|makes|keeps|means|shows|provides|enables|requires|"
                r"limits|constrains|narrows)\b"
            )
            verb_parts = sum(1 for p in comma_parts if re.search(verb_pattern, p, re.IGNORECASE))
            if verb_parts >= 3:
                count += 1
                continue
        if clauses >= 2:
            count += 1
    return count


def check_passive(text: str) -> int:
    """Count sentences with passive-voice constructions."""
    passive_re = re.compile(
        r"\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en|t)\b",
        re.IGNORECASE,
    )
    return sum(1 for s in split_sentences(text) if passive_re.search(s))


def tokenize(text: str) -> list:
    """Lowercase words, punctuation and stopwords removed."""
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


def ngrams(tokens: list, n: int) -> Counter:
    return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def jsd(p: Counter, q: Counter) -> float:
    """Jensen-Shannon divergence between two n-gram distributions."""
    all_keys = set(p.keys()) | set(q.keys())
    if not all_keys:
        return 0.0
    p_sum = sum(p.values()) or 1
    q_sum = sum(q.values()) or 1
    m = {
        k: (p.get(k, 0) / p_sum + q.get(k, 0) / q_sum) / 2
        for k in all_keys
    }
    kl_pm = kl_qm = 0.0
    for k, m_k in m.items():
        p_k = p.get(k, 0) / p_sum
        q_k = q.get(k, 0) / q_sum
        if p_k > 0:
            kl_pm += p_k * math.log2(p_k / m_k)
        if q_k > 0:
            kl_qm += q_k * math.log2(q_k / m_k)
    return (kl_pm + kl_qm) / 2


def vocab_overlap(paper_tokens: list, corpus_tokens: list) -> float:
    """Fraction of paper vocabulary that appears in the corpus."""
    paper_vocab = set(paper_tokens)
    corpus_vocab = set(corpus_tokens)
    if not paper_vocab:
        return 0.0
    return len(paper_vocab & corpus_vocab) / len(paper_vocab)


# ─── corpus baseline ───────────────────────────────────────────────────────

def compute_corpus_baseline(corpus: dict) -> dict:
    all_text = "\n".join(corpus_to_prose(t) for t in corpus.values())

    sentences = split_sentences(all_text)
    word_counts = [len(s.split()) for s in sentences if s.split()]
    word_counts_sorted = sorted(word_counts)
    n_words = len(all_text.split())

    tokens = tokenize(all_text)
    doc_tokens = []
    for text in corpus.values():
        doc_text = corpus_to_prose(text)
        doc_toks = re.findall(r"[a-z]+", doc_text.lower())
        doc_tokens.append([w for w in doc_toks if len(w) > 1])
    raw_tokens = [w for w in re.findall(r"[a-z]+", all_text.lower()) if len(w) > 1]

    return {
        "n_words": n_words,
        "n_sentences": len(sentences),
        "sentence_median": word_counts_sorted[len(word_counts_sorted) // 2] if word_counts_sorted else 0,
        "sentence_p90": word_counts_sorted[int(len(word_counts_sorted) * 0.9)] if word_counts_sorted else 0,
        "sentence_gt40_pct": round(
            sum(1 for c in word_counts if c > 40) / len(word_counts) * 100 if word_counts else 0, 1),
        "number_density": round(count_numbers(all_text) / n_words * 100, 1) if n_words else 0,
        "tokens": tokens,
        "2grams": ngrams(tokens, 2),
        "3grams": ngrams(tokens, 3),
        "doc_tokens": doc_tokens,
        "raw_tokens": raw_tokens,
        "corpus_sent_lengths": word_counts,
    }


# ─── section analysis ──────────────────────────────────────────────────────

def analyze_section(name, text, baseline, th, metaphor_re, terminology, is_main, is_abstract):
    """Analyze a single section against the reference corpus."""
    sentences = split_sentences(text)
    words = text.split()
    n_words = len(words) if words else 1

    # 1. Sentence length
    word_counts = [len(s.split()) for s in sentences] or [0]
    word_counts_sorted = sorted(word_counts)
    median_wc = word_counts_sorted[len(word_counts_sorted) // 2]
    p90_wc = word_counts_sorted[int(len(word_counts_sorted) * 0.9)]
    gt40_pct = sum(1 for c in word_counts if c > 40) / len(sentences) * 100 if sentences else 0

    # 2. Banned patterns (metaphors / neuroslop)
    metaphors = find_metaphors(text, metaphor_re)

    # 3. Terminology
    terms = check_terminology(text, terminology)

    # 4. Forward references
    fwd_ref_per_1k = count_forward_refs(text) / n_words * 1000 if n_words else 0

    # 5. Number density
    num_density = count_numbers(text) / n_words * 100 if n_words else 0

    # 6. Comma splices
    splice_pct = count_comma_splices(text) / len(sentences) * 100 if sentences else 0

    # 7. N-gram JSD (informational: short sections vs big corpus diverge by design)
    tokens = tokenize(text)
    sec_2grams = ngrams(tokens, 2)
    sec_3grams = ngrams(tokens, 3)
    jsd_2 = jsd(sec_2grams, baseline["2grams"]) if sec_2grams else 1.0
    jsd_3 = jsd(sec_3grams, baseline["3grams"]) if sec_3grams else 1.0
    jsd_avg = (jsd_2 + jsd_3) / 2

    # 8. Vocabulary overlap
    vocab_ov = vocab_overlap(tokens, baseline["tokens"])

    # 9. Passive voice
    passive_pct = check_passive(text) / len(sentences) * 100 if sentences else 0

    # 10-13. Stylometric similarity
    all_tokens = [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 1]
    fw_sim = function_word_similarity(all_tokens, baseline["raw_tokens"])
    cos_delta = burrows_cosine_delta(all_tokens, baseline["doc_tokens"])
    tfidf_sim = tfidf_cosine_similarity(text, baseline["doc_tokens"])
    sl_sim = sentence_length_similarity(text, baseline["corpus_sent_lengths"])

    # Failures
    failures = []
    if is_main:
        if median_wc > th["sentence_median_max"]:
            failures.append(f"sentence_median ({median_wc} > {th['sentence_median_max']})")
        if median_wc < th["sentence_median_min"]:
            failures.append(f"sentence_median ({median_wc} < {th['sentence_median_min']})")
        if p90_wc > th["sentence_p90_max"]:
            failures.append(f"sentence_p90 ({p90_wc} > {th['sentence_p90_max']})")
        if gt40_pct > th["sentence_gt40_pct_max"]:
            failures.append(f"sentence_gt40_pct ({gt40_pct:.1f}% > {th['sentence_gt40_pct_max']}%)")
        if fwd_ref_per_1k > th["forward_ref_per_1k_max"]:
            failures.append(f"forward_ref_per_1k ({fwd_ref_per_1k:.1f} > {th['forward_ref_per_1k_max']})")
        if num_density > th["number_density_max"]:
            failures.append(f"number_density ({num_density:.1f} > {th['number_density_max']})")
        if passive_pct > th["passive_pct_max"]:
            failures.append(f"passive_pct ({passive_pct:.1f}% > {th['passive_pct_max']}%)")

    if len(metaphors) > th["metaphor_max_per_section"]:
        failures.append(f"metaphor_count ({len(metaphors)} > {th['metaphor_max_per_section']})")

    for concept, info in terms.items():
        if info["count"] > th["terminology_names_max"]:
            failures.append(
                f"terminology_{concept} ({info['count']} > {th['terminology_names_max']})")

    if splice_pct > th["comma_splice_pct_max"]:
        failures.append(f"comma_splice_pct ({splice_pct:.1f}% > {th['comma_splice_pct_max']}%)")

    vocab_threshold = (
        th["vocab_overlap_min"] if is_main else th["vocab_overlap_appendix_min"]
    )
    if vocab_ov < vocab_threshold and n_words > 200:
        failures.append(f"vocab_overlap ({vocab_ov:.2f} < {vocab_threshold})")

    if is_abstract and count_numbers(text) > th["abstract_numbers_max"]:
        failures.append(
            f"abstract_numbers ({count_numbers(text)} > {th['abstract_numbers_max']})")

    long_sentences = [
        {"sentence": s[:300], "words": c}
        for s, c in zip(sentences, word_counts)
        if c > 40
    ]

    return {
        "name": name,
        "n_words": n_words,
        "n_sentences": len(sentences),
        "is_main": is_main,
        "metrics": {
            "sentence_median": median_wc,
            "sentence_p90": p90_wc,
            "sentence_gt40_pct": round(gt40_pct, 1),
            "metaphor_count": len(metaphors),
            "metaphors": metaphors,
            "terminology": terms,
            "forward_ref_per_1k": round(fwd_ref_per_1k, 1),
            "number_density": round(num_density, 1),
            "comma_splice_pct": round(splice_pct, 1),
            "jsd_avg": round(jsd_avg, 3),
            "vocab_overlap": round(vocab_ov, 3),
            "passive_pct": round(passive_pct, 1),
            "burrows_cosine_delta": round(cos_delta, 4),
            "tfidf_cosine_sim": round(tfidf_sim, 4),
            "function_word_sim": round(fw_sim, 4),
            "sentence_length_sim": round(sl_sim, 4),
        },
        "long_sentences": long_sentences,
        "failures": failures,
        "pass": len(failures) == 0,
    }


def generate_report(results: list, baseline: dict, input_name: str) -> tuple:
    ts = datetime.now().isoformat()
    passing = sum(1 for r in results if r["pass"])
    json_report = {
        "input": input_name,
        "timestamp": ts,
        "corpus_baseline": {
            k: baseline[k] for k in
            ("n_words", "n_sentences", "sentence_median", "sentence_p90",
             "sentence_gt40_pct", "number_density")
        },
        "sections": results,
        "summary": {
            "total_sections": len(results),
            "passing": passing,
            "failing": len(results) - passing,
        },
    }

    md = f"# Style Report — {input_name}\n\nGenerated: {ts}\n\n"
    md += "## Reference Corpus Baseline\n\n"
    md += "| Metric | Reference Corpus |\n|---|---|\n"
    for label, key in (
        ("Words", "n_words"), ("Sentences", "n_sentences"),
        ("Sentence median (words)", "sentence_median"),
        ("Sentence p90 (words)", "sentence_p90"),
        ("Sentences >40 words (%)", "sentence_gt40_pct"),
        ("Number density (per 100 words)", "number_density"),
    ):
        md += f"| {label} | {baseline[key]:,} |\n".replace(".0,", ",")

    md += "\n## Section Results\n\n"
    md += ("| Section | Words | Sent | Med | p90 | >40% | Banned | Vocab | Delta | TF-IDF | "
           "FuncWord | SentLen | Status |\n")
    md += "|---|" * 13 + "---|\n"
    for r in results:
        m = r["metrics"]
        status = "PASS" if r["pass"] else "FAIL"
        md += (
            f"| {r['name']} | {r['n_words']} | {r['n_sentences']} | {m['sentence_median']} "
            f"| {m['sentence_p90']} | {m['sentence_gt40_pct']}% | {m['metaphor_count']} "
            f"| {m['vocab_overlap']} | {m['burrows_cosine_delta']} | {m['tfidf_cosine_sim']} "
            f"| {m['function_word_sim']} | {m['sentence_length_sim']} | {status} |\n"
        )
    md += f"\n**Summary:** {passing}/{len(results)} sections pass\n\n"

    failing = [r for r in results if not r["pass"]]
    if failing:
        md += "## Detailed Failures\n\n"
        for r in failing:
            md += f"### {r['name']}\n\n**Failures:** {', '.join(r['failures'])}\n\n"
            m = r["metrics"]
            if m["metaphors"]:
                md += "**Banned patterns found:**\n"
                for met in m["metaphors"]:
                    md += f"- \"{met['phrase']}\" in: \"{met['context']}\"\n"
                md += "\n"
            if r["long_sentences"]:
                md += "**Long sentences (>40 words):**\n"
                for ls in r["long_sentences"][:10]:
                    md += f"- ({ls['words']} words) \"{ls['sentence']}...\"\n"
                md += "\n"
            for concept, info in m["terminology"].items():
                if info["count"] > 2:
                    md += (f"**Terminology ({concept}):** {info['count']} distinct names: "
                           f"{', '.join(info['names'])}\n\n")

    all_banned = [
        (r["name"], met["phrase"], met["context"])
        for r in results for met in r["metrics"]["metaphors"]
    ]
    if all_banned:
        md += "\n## All Banned-Pattern Hits\n\n"
        for sec, phrase, ctx in all_banned:
            md += f"- **{sec}**: \"{phrase}\" — \"{ctx}\"\n"

    return json_report, md


def main():
    ap = argparse.ArgumentParser(description="Style harness for prose (corpus-grounded)")
    ap.add_argument("--input", required=True, help="Paper dir: sections/*.tex, or *.tex/*.md/*.txt")
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS), help="Reference corpus dir")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="Config dir with thresholds etc.")
    ap.add_argument("--main-regex", default=r"^(0[1-8]|abstract)",
                    help="Regex matching 'main' section stems (others treated as appendix-like)")
    ap.add_argument("--section", default=None, help="Analyse a single section (substring match)")
    ap.add_argument("--out", default=None, help="Directory for report files (default: none saved)")
    ap.add_argument("--json", action="store_true", help="JSON report to stdout")
    ap.add_argument("--quiet", action="store_true", help="Only print failures")
    args = ap.parse_args()

    th = load_thresholds(args.config)
    metaphor_re = load_banned_patterns(args.config)
    terminology = load_terminology(args.config)

    corpus = load_corpus(args.corpus)
    if not corpus:
        err(f"ERROR: no reference corpus found in {args.corpus}")
    baseline = compute_corpus_baseline(corpus)

    cleaned, _raw, is_main = load_sections(args.input, args.main_regex)
    if args.section:
        cleaned = {k: v for k, v in cleaned.items() if args.section in k}
    if not cleaned:
        err(f"ERROR: no sections found in {args.input}")

    results = [
        analyze_section(name, text, baseline, th, metaphor_re, terminology,
                        is_main.get(name, False), name.lower() == "abstract")
        for name, text in sorted(cleaned.items())
    ]

    json_report, md_report = generate_report(
        results, baseline, Path(args.input).resolve().name)

    if args.json:
        print(json.dumps(json_report, indent=2))
    elif args.quiet:
        for r in results:
            if not r["pass"]:
                print(f"FAIL: {r['name']} — {', '.join(r['failures'])}")
    else:
        print(md_report)

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        name = Path(args.input).resolve().name
        (out / f"style_report_{name}.json").write_text(json.dumps(json_report, indent=2))
        (out / f"style_report_{name}.md").write_text(md_report)
        if not args.quiet:
            print(f"Reports saved to {out}/", file=sys.stderr)

    sys.exit(1 if any(not r["pass"] for r in results) else 0)


if __name__ == "__main__":
    main()
