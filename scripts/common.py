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


# ─── settings (YAML) ─────────────────────────────────────────────────────────
#
# The single source of truth for skill behavior is config/settings.yaml.
# Pure stdlib: a small YAML-subset parser below handles the file; PyYAML is
# used automatically if available. Supported subset:
#   comments (#), blank lines, `key: scalar`, nested maps (2-space indent),
#   block lists ("- item"), inline lists ([a, b]), quoted strings,
#   integers/floats, true/false/null. Multi-line strings are NOT supported.


def _yaml_scalar(tok: str):
    tok = tok.strip()
    if tok == "" or tok == "~" or tok.lower() == "null":
        return None
    if tok.lower() in ("true", "yes"):
        return True
    if tok.lower() in ("false", "no"):
        return False
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    if tok.startswith("'") and tok.endswith("'"):
        return tok[1:-1].replace("''", "'")
    if tok.startswith("[") and tok.endswith("]"):
        inner = tok[1:-1].strip()
        if not inner:
            return []
        return [_yaml_scalar(p) for p in _yaml_split_inline(inner)]
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?\d*\.\d+([eE][-+]?\d+)?", tok) or re.fullmatch(r"-?\d+[eE][-+]?\d+", tok):
        return float(tok)
    return tok


def _yaml_split_inline(inner: str):
    """Split 'a, [b, c], "d, e"' on top-level commas."""
    parts, depth, cur, quote = [], 0, [], None
    for ch in inner:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch == "[":
            depth += 1
            cur.append(ch)
        elif ch == "]":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return parts


def parse_yaml(text: str) -> dict:
    """Parse the YAML subset described above into nested dicts/lists."""
    # Strip comments and blank lines, keep (indent, content)
    lines = []
    for raw in text.splitlines():
        # remove comments outside quotes
        out, quote = [], None
        for ch in raw:
            if quote:
                out.append(ch)
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
        line = "".join(out).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if "\t" in line[:indent]:
            raise ValueError("YAML: tabs in indentation are not supported")
        lines.append((indent, line.strip()))

    def parse_block(i: int, indent: int):
        """Parse lines at >= indent starting at i. Returns (value, next_i)."""
        # decide list vs map by first line
        if i >= len(lines) or lines[i][0] < indent:
            return {}, i
        if lines[i][1].startswith("- ") or lines[i][1] == "-":
            items = []
            while i < len(lines) and lines[i][0] == indent and \
                    (lines[i][1].startswith("- ") or lines[i][1] == "-"):
                content = lines[i][1][1:].strip()
                if content == "":
                    val, i = parse_block(i + 1, indent + 2)
                    items.append(val)
                elif ":" in content and not content.startswith(('"', "'")):
                    # inline map start: "- key: value"
                    submap, i = _parse_map_item(i, indent, content)
                    items.append(submap)
                else:
                    items.append(_yaml_scalar(content))
                    i += 1
            return items, i
        # map
        result = {}
        while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("-"):
            content = lines[i][1]
            if ":" not in content:
                raise ValueError(f"YAML: expected 'key: value', got: {content!r}")
            key, _, rest = content.partition(":")
            key = key.strip().strip("\"'")
            rest = rest.strip()
            if rest:
                result[key] = _yaml_scalar(rest)
                i += 1
            else:
                val, i = parse_block(i + 1, indent + 2)
                result[key] = val
        return result, i

    def _parse_map_item(i: int, indent: int, first: str):
        """Handle '- key: value' plus following deeper-indented keys."""
        key, _, rest = first.partition(":")
        submap = {key.strip().strip("\"'"): _yaml_scalar(rest.strip()) if rest.strip() else {}}
        i += 1
        while i < len(lines) and lines[i][0] > indent:
            content = lines[i][1]
            if ":" not in content:
                raise ValueError(f"YAML: expected 'key: value', got: {content!r}")
            k2, _, rest2 = content.partition(":")
            k2 = k2.strip().strip("\"'")
            rest2 = rest2.strip()
            if rest2:
                submap[k2] = _yaml_scalar(rest2)
                i += 1
            else:
                val, i = parse_block(i + 1, lines[i][0] + 2)
                submap[k2] = val
        return submap, i

    if not lines:
        return {}
    value, _i = parse_block(0, lines[0][0])
    if not isinstance(value, dict):
        raise ValueError("YAML: top level must be a map")
    return value


def load_settings(config_dir) -> dict:
    """Load config/settings.yaml (single source of truth).

    Uses PyYAML if installed, else the built-in subset parser. Legacy split
    JSON configs (thresholds.json etc.) are still read when settings.yaml is
    absent, for backward compatibility.
    """
    config_dir = Path(config_dir)
    for name in ("settings.yaml", "settings.yml"):
        path = config_dir / name
        if path.exists():
            text = path.read_text()
            try:
                if __import__("os").environ.get("VCS_NO_PYYAML"):
                    raise ImportError
                import yaml  # type: ignore
                return yaml.safe_load(text) or {}
            except ImportError:
                return parse_yaml(text)
    # legacy fallback
    legacy = {}
    for key, fname in (("thresholds", "thresholds.json"),
                       ("terminology", "terminology.json"),
                       ("prose_quality", "prose_quality.json")):
        p = config_dir / fname
        if p.exists():
            legacy[key] = json.loads(p.read_text())
    if legacy:
        if (config_dir / "banned_patterns.txt").exists():
            patterns = [l.strip() for l in (config_dir / "banned_patterns.txt")
                        .read_text().splitlines()
                        if l.strip() and not l.strip().startswith("#")]
            legacy["banned_patterns"] = patterns
    return legacy


def _settings(config_dir) -> dict:
    return load_settings(config_dir)


def load_thresholds(config_dir) -> dict:
    """Thresholds from settings.yaml merged over corpus-derived defaults."""
    th = dict(THRESHOLD_DEFAULTS)
    s = _settings(config_dir)
    if isinstance(s.get("thresholds"), dict):
        th.update(s["thresholds"])
    return th


def load_banned_patterns(config_dir):
    """Compile banned patterns (metaphors / neuroslop) from settings.yaml.

    Returns a case-insensitive regex; never matches when no patterns set.
    """
    s = _settings(config_dir)
    patterns = s.get("banned_patterns") or []
    patterns = [p for p in patterns if isinstance(p, str) and p.strip()]
    if not patterns:
        return re.compile(r"(?!x)x")
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def load_terminology(config_dir) -> dict:
    """Terminology consistency map from settings.yaml."""
    s = _settings(config_dir)
    term = s.get("terminology")
    if isinstance(term, dict):
        return term.get("concepts", {}) or {}
    return {}


def load_prose_quality(config_dir) -> dict:
    """Prose-quality settings (acronyms, caveats, exemptions) from settings.yaml."""
    s = _settings(config_dir)
    pq = s.get("prose_quality")
    return pq if isinstance(pq, dict) else {}


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
    """Flatten a JSON object into a set of normalized numeric strings.

    Numeric string values (e.g. "23" or "0.812") are flattened too — a number
    stored as a string in an artifact is still a known number.
    """
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out |= number_set_from_json(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for v in obj:
            out |= number_set_from_json(v, prefix)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        # normalize: 2.5 and 2.50 and 2.5x should compare equal
        out.add(f"{float(obj):.6g}")
        if isinstance(obj, int):
            out.add(f"{obj}")
    elif isinstance(obj, str):
        if re.fullmatch(r"-?\d+\.?\d*", obj.strip()):
            out.add(f"{float(obj):.6g}")
    return out
