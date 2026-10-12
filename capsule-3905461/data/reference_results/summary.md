# Reproducibility Capsule Results

The capsule contains seven matched two-person teams, represented by 7 code-generation and 7 model-generation team-condition runs.
Condition order was counterbalanced 4:3: T01/T03/T05/T07 completed Code then Model, and T02/T04/T06 completed Model then Code.
All retained team-condition runs are documented as successful and all retained artifact sets pass structural validation.

| Condition | N | Mean time (min) | Median time (min) | Mean recorded events | Success | Mean recognized source/config/model files | Mean recognized lines | Mean recognized KiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Code generation | 7 | 274.01 | 240.00 | 31.71 | 100% | 31.6 | 4261.4 | 148.6 |
| Model generation | 7 | 25.77 | 26.37 | 10.29 | 100% | 9.0 | 1401.1 | 56.9 |

## Base artifact-inventory diagnostic

- Every model experiment contains exactly 3 valid BPMN files and 6 valid JSON artifacts; each BPMN file has a same-stem source JSON file.
- The source/config/model columns above are broad structural diagnostics. The publication measure is the refined marginal application-specific footprint under `results/phase2/`, where configuration, dependency metadata, support utilities, documentation/task inputs, runtime data, generated output, and reusable platform code are reported separately or excluded.

## Measurement boundary

Time is recorded team development time to functional completion, not person-hours.
Explicit duration tables include between-entry review gaps shorter than 45 minutes. Gaps equal to or longer than the threshold are excluded in full. Participant-reported totals are used where supplied.
Model histories form one merged chronological team timeline through the final runtime-test marker. The same break rule applies using each recorded event once; no observed Model gap exceeds 15 minutes.
The runtime-testing marker closes the time interval and is counted as a recorded user work event because runtime testing is part of task completion.
Success records independent cross-team scenario evaluation followed by the manuscript author's separate execution check and final acceptance; artifact completeness is validated separately by this script.

Turn and time extraction methods for every experiment are included in `experiment_metrics.csv`.
No missing values are replaced with synthetic minutes-per-turn estimates.
