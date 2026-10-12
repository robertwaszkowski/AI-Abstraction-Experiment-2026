# Supplementary Code syntax audit

This audit parses retained Code source without executing submitted applications. It is separate from functional acceptance, footprint measurement and the default numerical analysis. All seven Code deliveries were audited: 160 JavaScript/TypeScript files, 31 Python files, 19 JSON files and one inline JavaScript block passed. File counts include configuration and support files as well as application implementation files; they are not footprint counts. Python compilation produces no bytecode files. Explicit UTF-8 and BOM-marked UTF-16 inputs are decoded without modifying evidence. No syntax failures were found.

The audit also repeats the existing Model file-count, JSON/XML parsing, BPMN definitions/process-element and same-stem JSON checks, recording all 63 input hashes. All seven Model sets passed (21 BPMN and 42 JSON files).

## Reproduction

Requires the retained `data/code_generation` and `data/model_generation` corpus, Python 3.12.14, Node.js 24.19.0 and `@babel/parser` 7.28.5. The reproducibility archive contains results and scripts; it does not supply the full retained artifact corpus needed to rerun this additional audit. Use the corresponding source corpus from the private study capsule or obtain it from the author through the agreed access arrangement.

Install the parser into a separate tools directory, with npm:

    npm install --prefix tools --ignore-scripts --no-audit --no-fund @babel/parser@7.28.5

Run from the capsule root, with the Node executable on PATH:

    python code/audit_code_syntax.py --data-dir data --results-dir results/code_syntax --node node --parser-module tools/node_modules/@babel/parser/lib/index.js

`per_file.csv` reports Code statuses and SHA-256 hashes; `summary.json` records counts and tool versions; `model_crosscheck.json` records Model outcomes and hashes. Syntax failures return a nonzero exit status. The corpus is read only; output paths must be separate from evidence.

## Scope

JavaScript/TypeScript (including JSX/TSX), Python, JSON and inline JavaScript are checked. CSS, Prisma schemas, YAML, SQL, shell scripts, HTML markup, dependencies, type checking, builds and runtime behavior are not checked. HTML records therefore report only extraction of inline scripts, not markup validity. Environment files, dependency directories and version-control/bytecode directories are excluded. This audit is not a comparative correctness score.
