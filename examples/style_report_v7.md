# Style Report — v7

Generated: 2026-08-22T17:01:00.474576

## Reference Corpus Baseline

| Metric | Reference Corpus |
|---|---|
| Words | 141,541 |
| Sentences | 5,117 |
| Sentence median (words) | 21 |
| Sentence p90 (words) | 45 |
| Sentences >40 words (%) | 13.0% |
| Metaphors found | 6 |
| Number density (per 100 words) | 9.6 |

## Section Results

| Section | Words | Sent | Med | p90 | >40% | Metaphor | JSD | Vocab | Delta | TF-IDF | FuncWord | SentLen | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01_introduction | 877 | 45 | 18 | 32 | 0.0% | 1 | 0.992 | 0.774 | 0.7401 | 0.6159 | 0.8878 | 0.6109 | PASS |
| 02_cost_laws | 694 | 42 | 16 | 26 | 2.4% | 1 | 0.995 | 0.818 | 0.7015 | 0.5857 | 0.7886 | 0.5225 | PASS |
| 03_deployment | 707 | 34 | 20 | 32 | 2.9% | 1 | 0.998 | 0.809 | 0.6992 | 0.4531 | 0.8057 | 0.5086 | PASS |
| 04_deployment_losses | 451 | 26 | 15 | 37 | 3.8% | 0 | 0.999 | 0.793 | 0.7162 | 0.4658 | 0.811 | 0.4442 | PASS |
| 05_survives | 915 | 50 | 18 | 27 | 4.0% | 1 | 0.996 | 0.793 | 0.6895 | 0.4934 | 0.852 | 0.5966 | PASS |
| 06_related_work | 255 | 14 | 20 | 30 | 0.0% | 0 | 0.996 | 0.819 | 0.7353 | 0.422 | 0.8134 | 0.246 | PASS |
| 07_threats | 1137 | 57 | 20 | 31 | 0.0% | 0 | 0.996 | 0.819 | 0.6357 | 0.6194 | 0.8598 | 0.6462 | PASS |
| 08_conclusion | 277 | 18 | 16 | 22 | 0.0% | 1 | 0.998 | 0.855 | 0.7697 | 0.4921 | 0.8117 | 0.3778 | PASS |
| 09_appendix_defects | 693 | 45 | 12 | 27 | 4.4% | 0 | 1.0 | 0.728 | 0.7383 | 0.5048 | 0.8156 | 0.5215 | PASS |
| 10_appendix_decomp | 111 | 5 | 27 | 37 | 0.0% | 0 | 1.0 | 0.756 | 0.765 | 0.3898 | 0.8065 | 0.1046 | PASS |
| 11_appendix_batching | 116 | 5 | 23 | 39 | 0.0% | 0 | 1.0 | 0.755 | 0.7337 | 0.4473 | 0.721 | 0.0836 | PASS |
| 12_appendix_refuted | 115 | 7 | 12 | 33 | 0.0% | 0 | 1.0 | 0.765 | 0.7311 | 0.4339 | 0.7742 | 0.1325 | PASS |
| 13_appendix_input_canvas | 248 | 12 | 22 | 37 | 0.0% | 1 | 0.999 | 0.8 | 0.7248 | 0.4592 | 0.7527 | 0.2439 | PASS |
| 14_appendix_quality | 47 | 3 | 17 | 17 | 0.0% | 0 | 0.999 | 0.833 | 0.7066 | 0.1912 | 0.4674 | 0.0702 | PASS |
| 15_appendix_distributions | 57 | 3 | 22 | 29 | 0.0% | 0 | 1.0 | 0.731 | 0.7413 | 0.1712 | 0.5222 | 0.0715 | PASS |
| 16_appendix_forced | 183 | 8 | 22 | 48 | 12.5% | 0 | 0.999 | 0.768 | 0.6487 | 0.4426 | 0.7346 | 0.1857 | PASS |
| 17_appendix_batching_arch | 160 | 6 | 26 | 44 | 16.7% | 0 | 0.994 | 0.821 | 0.6802 | 0.5091 | 0.7582 | 0.1591 | PASS |
| 18_appendix_humaneval | 367 | 18 | 18 | 37 | 0.0% | 0 | 0.997 | 0.811 | 0.5583 | 0.4056 | 0.7469 | 0.3467 | PASS |
| 19_neurips_checklist | 493 | 33 | 13 | 26 | 3.0% | 0 | 0.998 | 0.787 | 0.7644 | 0.4671 | 0.8617 | 0.4585 | PASS |
| abstract | 142 | 11 | 13 | 17 | 0.0% | 0 | 0.997 | 0.899 | 0.653 | 0.4431 | 0.7176 | 0.2533 | PASS |

**Summary:** 20/20 sections pass

## All Metaphors Found

- **01_introduction**: "metered" — "This is the decoding equivalent of a metered taxi: the fare
climbs with every token"
- **02_cost_laws**: "metered" — "AR is a metered taxi: the fare climbs with every token; DG is a
subway with a flat fare per station"
- **03_deployment**: "knob" — "The X knob is the difference: drop X from 8 to 4
and the model still fills every field, just with slightly less
precision, instead of cutting the JSON in half mid-key"
- **05_survives**: "knob" — "[/FIGURE] 

The X knob need not be fixed"
- **08_conclusion**: "taxi" — "The taxi fare climbs with every token; the subway charges per
station"
- **13_appendix_input_canvas**: "knob" — "A full X grid (canvas X, X, X per cell) confirms the single-knob finding
holds across all X values, not just X"
