"""Explicit development durations plus investigator-confirmed review intervals.

Raw DOCX files are read only. Short gaps between consecutive table entries are
review work; gaps at or above the agreed threshold are breaks. A backward
clock between valid rows starts a new recorded session, without inventing a date.
Internally inconsistent rows require a source-specific factual adjudication.
"""
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
import hashlib

NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
CLOCK = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?$')
DURATION = re.compile(r'^(\d+(?:[.,]\d+)?)\s*(?:min|minutes?|minut|minuty)\.?$', re.I)
SUMMARY = re.compile(r'SUMA|SUM|TOTAL|RAZEM|ŁĄCZNIE', re.I)


def clock_minutes(value):
    match = CLOCK.fullmatch(value.strip())
    if not match:
        raise ValueError(f'Invalid recorded clock: {value!r}')
    hour, minute, second = match.groups()
    return int(hour) * 60 + int(minute) + int(second or 0) / 60


def read_duration_table(path: Path):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    paragraph_index = {id(p): i for i, p in enumerate(root.iter(NS+'p'), 1)}
    text = lambda element: ''.join(n.text or '' for n in element.iter(NS+'t')).strip()
    rows = []
    for table_number, table in enumerate(root.iter(NS+'tbl'), 1):
        for row_number, row in enumerate(table.findall(NS+'tr'), 1):
            cells = [text(cell) for cell in row.findall(NS+'tc')]
            if any(SUMMARY.fullmatch(cell) for cell in cells):
                continue
            durations = [(p, DURATION.fullmatch(text(p))) for p in row.iter(NS+'p')]
            durations = [(p, m) for p, m in durations if m]
            if not durations:
                continue
            if len(durations) != 1 or len(cells) < 3:
                raise ValueError(f'Ambiguous duration row: {path.name}, table {table_number}, row {row_number}')
            paragraph, match = durations[0]
            rows.append(dict(table=table_number, row=row_number, paragraph=paragraph_index[id(paragraph)],
                             start=cells[0], end=cells[1], minutes=float(match.group(1).replace(',', '.'))))
    if not rows:
        raise ValueError(f'No duration-table records in {path}')
    return rows


def measure_rows(rows, threshold=45):
    if threshold <= 0:
        raise ValueError('Break threshold must be positive')
    constituents = review = 0.0
    previous = None
    intervals = []
    for row in rows:
        start, end = clock_minutes(row['start']), clock_minutes(row['end'])
        if end < start or abs(end-start-row['minutes']) > 1e-8:
            raise ValueError(f"Clock/duration clarification required: table {row['table']}, row {row['row']}, "
                             f"{row['start']}--{row['end']}, {row['minutes']} minutes")
        constituents += row['minutes']
        if previous is not None and previous['table'] == row['table']:
            gap = start - clock_minutes(previous['end'])
            included = 0 <= gap < threshold
            review += gap if included else 0
            intervals.append(dict(table=row['table'], from_row=previous['row'], to_row=row['row'],
                                  gap_minutes=gap, review_minutes=gap if included else 0,
                                  classification='review' if included else ('break' if gap >= threshold else 'session boundary')))
        previous = row
    return dict(constituent_minutes=constituents, review_minutes=review,
                recorded_development_minutes=round(constituents+review, 2), review_intervals=intervals)


def measure(path, threshold=45):
    path = Path(path)
    rows = read_duration_table(path)
    # Investigator-supplied clock corrections, applied only to the identified
    # immutable source. Duration is calculated from the corrected endpoints.
    if path.name == 'team04-prompting-logs.docx':
        expected = 'c7da11273ad909d7fa4e90d192b7a5fbf4136cd3199a4d410878a19362e6957e'
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('T03 source hash changed: recheck the timestamp correction mapping')
        for row in rows:
            if row['table'] == 1 and row['row'] == 35:
                assert (row['start'], row['end'], row['minutes']) == ('20:21', '20:02', 0)
                row.update(start='20:21', end='21:02', minutes=41.0)
            elif row['table'] == 1 and row['row'] == 36:
                assert (row['start'], row['end'], row['minutes']) == ('20:13', '20:14', 1)
                row.update(start='21:13', end='21:14', minutes=1.0)
    result = measure_rows(rows, threshold)
    result['duration_rows'] = rows
    return result
