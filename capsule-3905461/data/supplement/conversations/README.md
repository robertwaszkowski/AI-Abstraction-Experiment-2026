# Anonymized conversation text

This directory supplies text exports of the retained development reports and AI conversations for the seven matched teams. There are 51 records: nine Code report/conversation files and six Model histories for each of seven Model implementations (42 histories). The two T05 files are DOCX and Markdown versions of the same report, not independent observations. All records are grouped by the final team and approach identifiers.

## Reading the records

Each JSON export identifies its team, approach, original source filename, source format and source SHA-256 hash. DOCX text is represented as an ordered paragraph array. `paragraph_index` counts all WordprocessingML paragraphs, including table paragraphs, starting at zero; empty paragraphs are retained. These indices support the paragraph locators in the request ledger. Markdown records retain line order inside `content.text`. Model records retain their original JSON structure under `content`, including conversation order and recorded timestamps.

## Privacy transformations and coverage

Exports were prepared from the previously sanitized publication corpus. Additional filters replace email addresses, local user-directory names, personal home-directory prefixes, URLs, credential values and explicit author/contact fields. Redacted strings contain visible placeholders. No original identifiers or redaction mappings are included. Nontext DOCX contents, document properties, comments, tracked-document revisions and embedded media are not distributed in these exports.

The Code sources contain 274 embedded media files, which are omitted pending separate visual privacy review. Drawing counts are retained per paragraph where available. These text exports do not include image-only requests or responses, and do not replace the screenshot evidence supporting the two inferred T04 requests. The manifest reports omissions and redaction counts for each file. Dates and development timestamps are retained because they support the timing analysis.

## Reproduction and evidence boundaries

The normal package build recalculates results from the distributed measurements and annotations; it does not automatically re-extract these JSON exports. The text exports permit inspection of the retained textual evidence. Exact reconstruction of the original reports, screenshot inspection and source-byte validation require the preserved original records. Sanitized text has different hashes from its source; the manifest records both separately. The records do not repeat application development or demonstrate a new application execution.

`manifest.json` lists every export and its source and export hash. The supplied `capsule-3905461/code/export_conversation_text.py` regenerates exports from an authorized copy of the sanitized source corpus, using `--source <corpus/data> --output <new-directory>`. It reads the source without modification. Source files are not shipped unredacted. Existing consent/identity records remain outside this package. The source corpus data license is retained in `LICENSE`.
