# Agent-friendly recipes

Declarative, runnable encodings of the checks that were **actually applied
in the DLLM-as-Service arXiv paper** — originally bespoke Python in
`verify_numbers.py`, now YAML rules executed by `scripts/check_rules.py`.

Every recipe has the same shape, designed for agents:

```
settings.yaml    # the rules (copy into your project's settings)
input/           # a FAILING fixture — run the gate, see the quoted violations
input_fixed/     # the same text fixed — gate exits 0
README.md        # the story, the rules, the commands, expected exit codes
```

## The six rule types

| Type | Question it answers | Paper criterion |
|---|---|---|
| `forbidden` | Did a retracted number or phrase resurface? | A1, A2, R9 |
| `required` | Did the punchline/caveat/headline survive the refactor? | I3, I5, S1 |
| `max_count` | Is a caveat repeated past its budget? | R6 |
| `proximity` | Does every ratio name its arm nearby? | A3 |
| `first_use` | Is the asymmetry disclosed at first use, inline? | A6 |
| `precision` | Is every metric printed at its fixed decimals? | A7 |

## The recipes

| # | Recipe | From the paper |
|---|---|---|
| 01 | [No backwards claims](01-no-backwards-claims/) | 15.6× was the defective harness; corrected to 2.5× — §1 must never resurrect it. "Wins at every length" header contradicted a 0.7× table row. |
| 02 | [Punchlines not buried](02-punchline-not-buried/) | "3.21× breaks a batch-1 SLA" belonged in Results, not only Limits; the input-length caveat belonged next to L*, not in §4.4. |
| 03 | [No editorializing](03-no-editorializing/) | "The arm we were not rooting for" — advocacy removed, facts kept. |
| 04 | [Every ratio names its arm](04-arm-attribution/) | Quality arm (dense AR-3B) ≠ latency arm (AR-30B MoE); ratios must attribute, asymmetry disclosed at first use. |
| 05 | [Precision policy](05-precision-policy/) | Latency 1 dp, F1 3 dp, ratios 1 dp — no silent precision drift between sections. |
| 06 | [Abstract structure](06-abstract-structure/) | Claim + comparison + headline number + regime, reconstructable from the abstract alone. |

## Using a recipe in your project

Copy the `rules:` block from the recipe's `settings.yaml` into your
project's `settings.yaml`, adapt the patterns to your numbers/sections, and
run the gate — `check_rules.py` runs automatically as part of `run_all.py`
whenever `rules:` is non-empty:

```bash
python3 scripts/run_all.py --input your-paper --config your-config
```

Rules compose with the other harnesses: `check_claims.py` proves the number
*exists*, `precision` proves it is *printed correctly*, `forbidden` proves
the *old* number is gone, `required` proves the *right* sentence survived.
