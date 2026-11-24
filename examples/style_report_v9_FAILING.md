# Style Report — v9

Generated: 2026-11-24T22:18:21.723666

## Reference Corpus Baseline

| Metric | Reference Corpus |
|---|---|
| Words | 141,541 |
| Sentences | 5,117 |
| Sentence median (words) | 21 |
| Sentence p90 (words) | 45 |
| Sentences >40 words | 13.0% |
| Number density (per 100 words) | 9.6 |

## Section Results

| Section | Words | Sent | Med | p90 | >40% | Banned | Vocab | Delta | TF-IDF | FuncWord | SentLen | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01_introduction | 533 | 31 | 16 | 25 | 0.0% | 0 | 0.894 | 0.7598 | 0.5173 | 0.9189 | 0.4528 | PASS |
| 02_cost_laws | 248 | 16 | 16 | 28 | 0.0% | 0 | 0.881 | 0.6643 | 0.4397 | 0.7828 | 0.3469 | PASS |
| 03_deployment | 251 | 13 | 19 | 29 | 0.0% | 0 | 0.842 | 0.8128 | 0.4126 | 0.856 | 0.2419 | PASS |
| 04_deployment_losses | 177 | 12 | 13 | 21 | 0.0% | 0 | 0.932 | 0.6968 | 0.3537 | 0.6065 | 0.2771 | PASS |
| 05_survives | 424 | 24 | 16 | 25 | 4.2% | 0 | 0.856 | 0.6736 | 0.5713 | 0.8905 | 0.4249 | PASS |
| 06_related_work | 87 | 6 | 15 | 25 | 0.0% | 0 | 0.852 | 0.7536 | 0.3805 | 0.7212 | 0.146 | FAIL |
| 07_threats | 180 | 14 | 14 | 17 | 0.0% | 0 | 0.883 | 0.7699 | 0.4026 | 0.7726 | 0.317 | PASS |
| 08_conclusion | 150 | 9 | 17 | 25 | 0.0% | 0 | 0.852 | 0.779 | 0.4452 | 0.8713 | 0.2158 | PASS |
| 09_appendix_compact | 964 | 68 | 14 | 22 | 0.0% | 0 | 0.827 | 0.7101 | 0.5217 | 0.8173 | 0.5614 | PASS |
| abstract | 160 | 9 | 18 | 27 | 0.0% | 0 | 0.87 | 0.7992 | 0.3842 | 0.726 | 0.188 | FAIL |

**Summary:** 8/10 sections pass

## Detailed Failures

### 06_related_work

**Failures:** forward_ref_per_1k (11.5 > 8.0)

### abstract

**Failures:** abstract_numbers (5 > 3)

