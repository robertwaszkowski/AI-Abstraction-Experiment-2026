"""Recalculate timing sensitivity from de-identified recorded interval inputs."""
from pathlib import Path
import json, math, statistics
import phase2_analysis as pa

THRESHOLDS = (15, 30, 45, 60)

def validate(records):
    expected = {f'{condition}_{i:02d}' for condition in ('code', 'model') for i in range(1, 8)}
    if len(records) != 14 or {r['run_id'] for r in records} != expected:
        raise ValueError('Require exactly seven matched Code/Model pairs')
    for r in records:
        if not math.isfinite(r['fixed_seconds']) or r['fixed_seconds'] < 0:
            raise ValueError('Invalid fixed duration')
        for stream in r['streams']:
            if not all(math.isfinite(gap) for gap in stream['gap_seconds']):
                raise ValueError('Invalid recorded interval')

def minutes(record, threshold):
    if threshold <= 0:
        raise ValueError('Break threshold must be positive')
    # Keep recorded streams separate. Negative gaps mark session boundaries.
    seconds = record['fixed_seconds']
    seconds += sum(gap for stream in record['streams'] for gap in stream['gap_seconds']
                   if 0 <= gap < threshold * 60)
    return round(seconds / 60, 2)

def regenerate(inputs: Path, output: Path):
    payload = json.loads(inputs.read_text(encoding='utf-8'))
    records = payload['runs']; validate(records)
    index = {r['run_id']: r for r in records}
    rows, summaries = [], []
    for threshold in THRESHOLDS:
        differences = []
        for i in range(1, 8):
            code, model = index[f'code_{i:02d}'], index[f'model_{i:02d}']
            c, m = minutes(code, threshold), minutes(model, threshold)
            difference = c - m; differences.append(difference)
            rows.append(dict(threshold_minutes=threshold, is_primary='Yes' if threshold == 45 else 'No',
                team_id=f'T{i:02d}', code_run_id=code['run_id'], code_time_method=code['time_method'],
                code_source_observed_minutes=c, model_source_observed_minutes=m,
                difference_code_minus_model_minutes=round(difference, 2)))
        summaries.append(dict(threshold_minutes=threshold, is_primary='Yes' if threshold == 45 else 'No',
            n_pairs=7, positive_differences=sum(d > 0 for d in differences),
            mean_difference_code_minus_model_minutes=pa.fmt(statistics.fmean(differences)),
            median_difference_code_minus_model_minutes=pa.fmt(statistics.median(differences)),
            matched_pairs_rank_biserial=pa.fmt(pa.matched_rank_biserial(differences)),
            exact_sign_flip_two_sided_p_exploratory=pa.fmt(pa.exact_sign_flip_p(differences))))
    output.mkdir(parents=True, exist_ok=True)
    pa.write_csv(output/'threshold_sensitivity.csv', rows)
    pa.write_csv(output/'threshold_sensitivity_summary.csv', summaries)
    return rows, summaries
