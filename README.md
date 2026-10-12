# Models vs Code: reproducibility materials

This repository accompanies **Are Executable Models Faster to Develop Than Code? A Matched-Team Comparison of Application Development** by Robert Waszkowski.

The current reproducibility materials are in [`capsule-3905461/`](capsule-3905461/), version **TSE-models-vs-code-2026-10-12-r11**. They match the code, data, environment and metadata exported from Code Ocean capsule 3905461. The study contains **seven matched two-person teams**, each using both application code and executable BPMN/JSON models on Aurea, with AI assistance available in both approaches.

The three personnel workflows are leave requests, decorations and medals, and changes of employment conditions. Results concern recorded development time through functional completion, recorded AI requests, application-specific file size, documentary/static capability evidence and identified technical content.

## Reproduce the results

Python 3.12 and its standard library are sufficient. From the repository root, run:

```sh
python capsule-3905461/code/reproduce_results.py
```

On Code Ocean, click **Reproducible Run**. The run window displays a short progress summary. Open [`capsule-3905461/results/README.md`](capsule-3905461/results/README.md) for a guide to the tables, plot and descriptions. Detailed checks are in `REPRODUCTION_REPORT.json` and `RUN_DETAILS.txt`.

| Folder | Contents |
| --- | --- |
| `capsule-3905461/code/` | Analysis scripts, tests and run instructions. |
| `capsule-3905461/data/` | Measurements, timing intervals, annotations, anonymized textual evidence and reference results. |
| `capsule-3905461/environment/` | The Code Ocean environment specification. |
| `capsule-3905461/metadata/` | Capsule title, description and author metadata. |
| `capsule-3905461/results/` | Outputs from the verified r10 analysis, including the readable results guide. |

The runner checks 223 code/data files against its checksum manifest, runs 34 tests, and compares regenerated analyses with the supplied reference results. It runs directly from unpacked folders and produces tables, descriptions and an SVG plot. Manuscript and supplement document production is handled separately.

## Scope and evidence

This reproduces analyses from supplied measurements and frozen annotations. It does not independently recode evidence, rerun participant applications, validate deployed security or repeat the empirical study. Acceptance tables transcribe author reports. Technical-category counts describe identified technical content rather than effort, difficulty or complete human skill requirements.

The capsule includes 51 anonymized conversation/report text exports. Embedded screenshots, credentials, identifying records and restricted originals are excluded from the capsule. See its data documentation for coverage and source hashes. Code and data licenses are in `capsule-3905461/code/LICENSE` and `capsule-3905461/data/LICENSE`.

Earlier repository directories are historical study material; use `capsule-3905461/` for the current seven-team analyses. GitHub provides version history and an additional source copy. It is not a dependency of the capsule. The Code Ocean capsule remains private pending the author's publication decision; no public capsule DOI is claimed here.
