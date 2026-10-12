# Models vs Code: computational results

Version: TSE-models-vs-code-2026-10-12-r11.

The capsule runs directly from its native folders: executable analysis and tests in `/code`, input evidence and reference results in `/data`, and regenerated outputs in `/results`.

Click **Reproducible Run** on Code Ocean. When the run finishes, open `/results/README.md` for a guide to the generated tables, plot and descriptions. The run window displays a short progress summary; detailed checks are saved in `REPRODUCTION_REPORT.json` and `RUN_DETAILS.txt`. Locally, run `python code/reproduce_results.py --data-dir data --results-dir results` from this directory's parent. Python 3.12 or compatible Python 3 and its standard library are sufficient. The entry point reads the unpacked files directly and verifies each checksum in `code/SHA256.json`.

Outputs are paired descriptive statistics, effects and sensitivities (CSV/JSON), the paired SVG plot, category profiles, the evidence matrix and per-run descriptions (CSV/JSON/Markdown), acceptance-report transcriptions (CSV), and `REPRODUCTION_REPORT.json`. All outputs are checked against the reference results; the run also executes 34 tests. CSV rows and JSON values match exactly; SVG and Markdown text comparisons normalize platform line endings only. Manuscript production is handled separately.

The statistical unit is one matched two-person team; the analysis contains seven pairs. Recorded time includes work through functional completion, with gaps of 45 minutes or longer excluded as breaks. Request definitions, fixed bootstrap seeds, thresholds and the IT/domain mapping are preserved. See `/data/request_counts/METHOD.md` and the evidence documentation for details.

The computation starts from distributed measurements, timing intervals and frozen annotations. It does not independently recode evidence, rerun participant applications, validate deployed security, repeat the empirical study or verify reviewer access. Acceptance outputs transcribe author reports. Full original-source validation requires separately authorized retained records. The data include 51 anonymized text exports; screenshots, credentials and identifying records are excluded. Category counts describe identified technical content, not effort, difficulty, complete skill repertoires or human necessity.
