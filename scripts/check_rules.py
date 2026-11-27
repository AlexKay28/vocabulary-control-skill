#!/usr/bin/env python3
"""Declarative text-rule engine: project-specific criteria as YAML recipes.

The original DLLM-as-Service `verify_numbers.py` encoded hard-won editorial
rules in bespoke Python (A1 "no backwards advantage claim", I3 "punchline
must not be buried", A7 "precision policy", ...). This engine turns that
class of check into declarative YAML so agents can port the recipes to any
paper without writing code.

Rule types (each entry in settings.yaml `rules:`):
  forbidden   — pattern must not appear. Options: sections, message.
  required    — every matching section must contain at least one of
                `pattern` / `any_of` (a punchline that must not be buried).
  max_count   — pattern occurs at most `max` times per matching section.
  proximity   — every match of `pattern` must have `near` within
                `window_words` words (e.g. every ratio must name its arm).
  first_use   — the FIRST occurrence of `pattern` per section must have
                `near` within `window_words` (disclosure at first use).
  precision   — the number following `metric` within 6 words must have
                exactly `decimals` decimal places (numeric precision policy).

Common options: id (required), message (quoted on violation),
sections (regex on section name; default all), enabled (default true).

Usage:
  python3 check_rules.py --input <paper-dir> [--config <dir>]
  python3 check_rules.py --input mypaper --json

Exit codes: 0 = pass or no rules configured; 1 = violations; 2 = input error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_CONFIG, load_sections, load_settings  # noqa: E402


def _window(text: str, start: int, end: int, n_words: int) -> str:
    """Text window of n_words around match [start, end)."""
    before = text[:start].split()
    after = text[end:].split()
    return " ".join(before[-n_words:] + [text[start:end]] + after[:n_words])


def _sentence(text: str, pos: int) -> str:
    # split on ". " rather than "." so decimals (0.81) don't truncate context
    idx = text.rfind(". ", 0, pos)
    start = idx + 2 if idx != -1 else 0
    end = text.find(". ", pos)
    return text[start:end if end != -1 else len(text)].strip()[:250]


def run_rule(rule: dict, name: str, text: str) -> list:
    """Return list of violation dicts for one rule in one section."""
    out = []
    rid = rule["id"]
    rtype = rule["type"]
    msg = rule.get("message", rtype)

    def hit(pos, detail):
        out.append({"rule": rid, "section": name, "message": msg,
                    "detail": detail, "context": _sentence(text, pos)})

    if rtype == "forbidden":
        for m in re.finditer(rule["pattern"], text, re.IGNORECASE):
            hit(m.start(), f"forbidden pattern: {m.group()!r}")

    elif rtype == "required":
        alternatives = rule.get("any_of") or [rule["pattern"]]
        found = any(re.search(p, text, re.IGNORECASE) for p in alternatives)
        if not found:
            out.append({"rule": rid, "section": name, "message": msg,
                        "detail": f"none of {alternatives} present",
                        "context": "(section-level requirement)"})

    elif rtype == "max_count":
        matches = list(re.finditer(rule["pattern"], text, re.IGNORECASE))
        if len(matches) > rule.get("max", 0):
            for m in matches[rule.get("max", 0):]:
                hit(m.start(),
                    f"occurrence {len(matches)} > max {rule.get('max', 0)}: {m.group()!r}")

    elif rtype in ("proximity", "first_use"):
        near = re.compile(rule["near"], re.IGNORECASE)
        window = rule.get("window_words", 30)
        matches = list(re.finditer(rule["pattern"], text, re.IGNORECASE))
        if rtype == "first_use":
            matches = matches[:1]
        for m in matches:
            ctx = _window(text, m.start(), m.end(), window)
            if not near.search(ctx):
                hit(m.start(),
                    f"{m.group()!r} without {rule['near']!r} within {window} words")

    elif rtype == "precision":
        metric = re.compile(rule["metric"], re.IGNORECASE)
        decimals = rule["decimals"]
        for m in metric.finditer(text):
            after = text[m.end():]
            num = re.match(r"\s*(?:is|=|of|:)?\s*\$?(\d+\.\d+|\d+)", after)
            if not num:
                continue
            token = num.group(1)
            actual = len(token.split(".")[1]) if "." in token else 0
            if actual != decimals:
                hit(m.start(),
                    f"{m.group()!r} value {token} has {actual} dp, expected {decimals}")

    return out


def main():
    ap = argparse.ArgumentParser(description="Declarative text-rule engine")
    ap.add_argument("--input", required=True)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--main-regex", default=r"^(0[1-8]|abstract)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    settings = load_settings(args.config)
    rules = settings.get("rules") or []
    rules = [r for r in rules if r.get("enabled", True)]
    if not rules:
        print("[skip] no `rules:` configured in settings.yaml")
        sys.exit(0)

    sections, _raw, _is_main = load_sections(args.input, args.main_regex)

    violations = []
    for rule in rules:
        sec_re = re.compile(rule.get("sections", "."), re.IGNORECASE)
        for name, text in sorted(sections.items()):
            if not sec_re.search(name):
                continue
            violations.extend(run_rule(rule, name, text))

    if args.json:
        print(json.dumps({"rules": len(rules), "violations": violations,
                          "total_violations": len(violations)}, indent=2))
    else:
        if not violations:
            print(f"ALL {len(rules)} RULE(S) PASS")
        else:
            print(f"{len(violations)} RULE VIOLATION(S):")
            for v in violations:
                print(f"  [{v['rule']}] {v['section']}: {v['message']}")
                print(f"      {v['detail']}")
                print(f"      in: \"{v['context']}\"")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
