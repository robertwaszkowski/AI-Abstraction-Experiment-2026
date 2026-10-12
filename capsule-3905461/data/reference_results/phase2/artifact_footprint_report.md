# Marginal application-specific artifact-footprint report

The primary footprint includes submitted application implementation/model artifacts, application tests, and application assets. It excludes project/dependency configuration, development-support utilities, documentation and supplied task inputs, runtime data, generated build output, dependency directories, and the reusable Aurea 2026.01.0 platform.

| Condition | Runs | Primary files | Primary text lines | Primary bytes |
|---|---:|---:|---:|---:|
| Code | 7 | 188 | 28744 | 1120356 |
| Model | 7 | 63 | 9808 | 408130 |

The file-level inventory exposes every classification decision. Categories with zero files remain present in the by-type table so exclusions are explicit. Dependency directories and generated build output were removed from the publication corpus and are therefore not silently included as zero-cost generated artifacts.

Lines and bytes measure retained representation size only. Different languages and formats do not assign equal meaning to a line, and the counts do not measure complexity, maintainability, quality, productivity, or total system size. Aurea is reusable infrastructure outside the marginal per-application boundary; its exclusion is both a mechanism of reuse and a treatment confound.
