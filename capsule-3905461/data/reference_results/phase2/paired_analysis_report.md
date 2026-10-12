# Phase 2 paired-analysis report

## Design and interpretation

The analysis contains seven matched two-person teams. Each difference is Code minus Model. The four Code-first and three Model-first teams are preserved as a counterbalanced repeated-measures design.

Timing measures recorded team development to functional completion, with the established gap rules applied to all seven matched teams. Requests use a common user-message counting rule; T04 includes two response-inferred requests and T05 uses directly reported interactions, including starter adaptation. Identical wording alone is not deduplicated. Runtime-test markers, pure acknowledgments, summary rows and command approvals are excluded. Counts describe retained evidence, with unequal completeness and no independent second coding. See data/request_counts/METHOD.md for rules and source locators.

## Paired results

| Measure | +/−/0 | Median difference | Mean difference (paired bootstrap 95% interval) | Rank-biserial | Median ratio | Exploratory exact p |
|---|---:|---:|---:|---:|---:|---:|
| Source-specific log-observed time (minutes) | 7/0/0 | 209.55 | 248.2357142857143 [143.42714285714285, 359.4657142857142] | 1.0 | 7.8817733990147785 | 0.015625 |
| Recorded requests to AI | 7/0/0 | 13.0 | 22.857142857142858 [10.142857142857142, 38.142857142857146] | 1.0 | 2.3 | 0.015625 |
| Marginal application-specific files | 5/2/0 | 3.0 | 17.857142857142858 [0.7142857142857143, 36.285714285714285] | 0.7142857142857143 | 1.3333333333333333 | 0.125 |
| Marginal application-specific text lines | 7/0/0 | 3374.0 | 2705.1428571428573 [1582.0, 3746.5714285714284] | 1.0 | 3.3137384412153237 | 0.015625 |
| Marginal application-specific bytes | 7/0/0 | 74844.0 | 101746.57142857143 [62418.571428571435, 144148.0] | 1.0 | 2.2532933714365373 | 0.015625 |

## Sensitivity findings

- With a 15-minute session threshold, all 7/7 time differences remain positive; the median Code-minus-Model difference is 123.63 minutes.
- With a 30-minute session threshold, all 7/7 time differences remain positive; the median Code-minus-Model difference is 209.55 minutes.
- With a 45-minute session threshold, all 7/7 time differences remain positive; the median Code-minus-Model difference is 209.55 minutes.
- With a 60-minute session threshold, all 7/7 time differences remain positive; the median Code-minus-Model difference is 209.55 minutes.
- For source_observed_minutes, excluding the union of teams containing either condition maximum leaves n=5; all 5/5 differences remain positive and the median difference is 209.55.
- For recorded_ai_requests, excluding the union of teams containing either condition maximum leaves n=5; all 5/5 differences remain positive and the median difference is 13.0.

## Statistical boundaries

- Quartiles use Hyndman–Fan Type 7 interpolation.
- Bootstrap intervals use 100,000 paired team resamples with a fixed seed.
- Exact sign-flip calculations enumerate all assignments and are exploratory, not confirmatory.
- The primary Code session threshold is 45 minutes: gaps below it count as work; gaps at or above it are excluded in full as breaks.
- The 15/30/45/60-minute threshold analysis changes between-entry review and timestamped gaps under the same boundary rule; explicit within-entry durations and reported totals remain fixed. Model histories are merged into one team timeline and their observed values are unchanged across these thresholds.
- Maximum-observation exclusions remove whole matched teams. Independent deletion of one condition's value would break pairing and is not used.
- Marginal application-specific footprint includes implementation/model artifacts, application tests, and application assets. Dependency/build configuration, support utilities, documentation/task inputs, runtime data, generated output, and the reusable Aurea platform are reported separately or excluded.
- Files, lines, and bytes are syntactic footprint measures; a line in one language or format is not semantically equivalent to a line in another, and no maintainability or quality inference is made.
