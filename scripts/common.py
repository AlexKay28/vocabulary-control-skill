#!/usr/bin/env python3
"""Shared utilities for the vocabulary-control-skill harness scripts.

Pure stdlib. Everything project-specific lives in config/, so agents can
retarget the harness to any paper without touching code.
"""

import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_ROOT / "config"
DEFAULT_CORPUS = SKILL_ROOT / "reference_corpus"

# Fallback thresholds used when a key is missing from thresholds.json.
# These match the reference-corpus-derived values from the original harness.
THRESHOLD_DEFAULTS = {
    "sentence_median_max": 28,
    "sentence_median_min": 10,
    "sentence_p90_max": 45,
    "sentence_gt40_pct_max": 15.0,
    "metaphor_max_per_section": 1,
    "terminology_names_max": 2,
    "forward_ref_per_1k_max": 8.0,
    "number_density_max": 4.0,
    "comma_splice_pct_max": 10.0,
    "vocab_overlap_min": 0.65,
    "vocab_overlap_appendix_min": 0.55,
    "passive_pct_max": 25.0,
    "abstract_numbers_max": 3,
    "flesch_main_min": 18,
    "flesch_main_max": 55,
    "flesch_appendix_min": 20,
    "median_sentence_min": 10,
    "median_sentence_max": 28,
    "sentences_gt40_max": 2,
    "sentences_gt60_max": 0,
    "passive_cluster_max": 3,
    "hedge_per_sentence_max": 0.5,
    "number_density_main_max": 4.0,
    "number_density_abs_max": 5.0,
    "bracket_density_main_max": 1.5,
    "words_per_number_min": 25,
    "match_tolerance_pct": 0.05,
}


def err(msg: str, code: int = 2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load_thresholds(config_dir: Path) -> dict:
    """Load thresholds.json merged over defaults."""
    th = dict(THRESHOLD_DEFAULTS)
    path = Path(config_dir) / "thresholds.json"
    if path.exists():
        th.update(json.loads(path.read_text()))
    return th


def load_banned_patterns(config_dir: Path):
    """Load banned_patterns.txt -> compiled case-insensitive regex.

    One pattern per line; blank lines and #-comments ignored.
    """
    patterns = []
    path = Path(config_dir) / "banned_patterns.txt"
    if not path.exists():
        return re.compile(r"(?!x)x")  # never matches
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    if not patterns:
        return re.compile(r"(?!x)x")
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def load_terminology(config_dir: Path) -> dict:
    """Load terminology.json -> {concept: {canonical, patterns[], groups{}}}."""
    path = Path(config_dir) / "terminology.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("concepts", {})


def load_prose_quality(config_dir: Path) -> dict:
    """Load prose_quality.json (project-specific R5/R6/R7-style patterns)."""
    path = Path(config_dir) / "prose_quality.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


# ─── text cleaning ─────────────────────────────────────────────────────────

def strip_latex(text: str) -> str:
    """Remove LaTeX commands, comments, math, and environments for prose analysis."""
    for env in ("equation", "align", "table", "tabular", "tabularx",
                "figure", "itemize", "enumerate", "abstract"):
        text = re.sub(
            rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}",
            " ",
            text,
            flags=re.DOTALL,
        )
    text = re.sub(r"\\footnote\{[^}]*\}", "", text)
    text = re.sub(r"\$[^$]*\$", "X", text)
    text = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?", "", text)
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_latex_keep_structure(text: str) -> str:
    """Strip LaTeX but keep paragraph/sentence structure for prose analysis."""
    for env in ("equation", "align", "tabular", "tabularx"):
        text = re.sub(
            rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}",
            " ",
            text,
            flags=re.DOTALL,
        )
    text = re.sub(r"\\begin\{table\*?\}", " [TABLE] ", text)
    text = re.sub(r"\\end\{table\*?\}", " [/TABLE] ", text)
    text = re.sub(r"\\begin\{figure\*?\}", " [FIGURE] ", text)
    text = re.sub(r"\\end\{figure\*?\}", " [/FIGURE] ", text)
    text = re.sub(r"\\begin\{(itemize|enumerate)\*?\}", "", text)
    text = re.sub(r"\\end\{(itemize|enumerate)\*?\}", "", text)
    text = re.sub(r"\\item\s*", "- ", text)
    text = re.sub(r"\\footnote\{[^}]*\}", "", text)
    text = re.sub(r"\$[^$]*\$", "X", text)
    for cmd in ("texttt", "emph", "textbf", "textsc", "textit"):
        text = re.sub(rf"\\{cmd}\{{([^}}]*)\}}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?\{[^}]*\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_markdown(text: str) -> str:
    """Light cleaning for .md/.txt inputs: drop code blocks, keep prose."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " [FIGURE] ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^[#>\-]+\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*?([^*]*)\*\*?", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text(raw: str, suffix: str) -> str:
    """Dispatch cleaning by file type."""
    if suffix == ".tex":
        return strip_latex_keep_structure(raw)
    return strip_markdown(raw)


# ─── section loading ────────────────────────────────────────────────────────

def load_sections(input_dir: Path, main_regex: str = r"^(0[1-8]|abstract)"):
    """Load text sections from a directory.

    Accepts:
      - <dir>/sections/*.tex  (+ <dir>/main.tex abstract extracted)
      - <dir>/*.tex
      - <dir>/*.md or *.txt (flat)
    Returns (cleaned: {name: text}, raw: {name: text}, is_main: {name: bool}).

    A section counts as "main" if its name matches `main_regex`
    (default: stems starting 01–08 or 'abstract' — mirrors the original
    paper layout: numbered main sections first, appendices after 09).
    """
    input_dir = Path(input_dir)
    main_re = re.compile(main_regex, re.IGNORECASE)
    cleaned, raw, is_main = {}, {}, {}

    candidates = []
    sections_dir = input_dir / "sections"
    if sections_dir.is_dir():
        candidates = sorted(sections_dir.iterdir())
    else:
        candidates = sorted(
            p for p in input_dir.iterdir()
            if p.suffix in (".tex", ".md", ".txt") and p.stem != "main"
        )
    if not candidates:
        err(f"ERROR: no section files (.tex/.md/.txt) found in {input_dir}")

    for f in candidates:
        if f.suffix not in (".tex", ".md", ".txt") or not f.is_file():
            continue
        content = f.read_text()
        raw[f.stem] = content
        cleaned[f.stem] = clean_text(content, f.suffix)
        is_main[f.stem] = bool(main_re.match(f.stem)) or f.stem.lower() == "abstract"

    main_tex = input_dir / "main.tex"
    if main_tex.exists() and "abstract" not in cleaned:
        content = main_tex.read_text()
        m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
        if m:
            raw["abstract"] = m.group(1)
            cleaned["abstract"] = strip_latex_keep_structure(m.group(1))
            is_main["abstract"] = True
    return cleaned, raw, is_main


# ─── corpus loading ────────────────────────────────────────────────────────

def load_corpus(corpus_dir: Path) -> dict:
    """Load reference-corpus texts. Returns {id: text}."""
    corpus_dir = Path(corpus_dir)
    texts = {}
    manifest = corpus_dir / "MANIFEST.json"
    if manifest.exists():
        for paper in json.loads(manifest.read_text()).get("papers", []):
            p = corpus_dir / paper["file"]
            if p.exists():
                texts[paper["id"]] = p.read_text()
    else:
        for p in sorted(corpus_dir.glob("*.txt")):
            texts[p.stem] = p.read_text()
    return texts


def corpus_to_prose(text: str) -> str:
    """Strip '# ...' metadata header from corpus file, return prose only."""
    lines = text.split("\n")
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            start = i + 1
        elif line.strip() and start > 0:
            break
    return "\n".join(lines[start:])


# ─── generic text utils ────────────────────────────────────────────────────

def split_sentences(text: str) -> list:
    """Split text into sentences (fragments under 4 words dropped)."""
    text = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if len(s.split()) > 3]


def count_words(text: str) -> int:
    return len(text.split())


def count_numbers(text: str) -> int:
    """Count numeric tokens in text."""
    return len(re.findall(r"\b\d[\d,.]*\b", text))


def number_set_from_json(obj, prefix: str = "") -> set:
    """Flatten a JSON object into a set of normalized numeric strings."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out |= number_set_from_json(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for v in obj:
            out |= number_set_from_json(v, prefix)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        # normalize: 2.5 and 2.50 and 2.5x should compare equal
        out.add(f"{float(obj):.6g}")
        if isinstance(obj, int):
            out.add(f"{obj}")
    return out
