"""Analyze source-linked AI requests using the established paired estimators.

Legacy parser-event fields are preserved. A separate request measure occupies
the interaction outcome's existing bootstrap seed offset; time and footprint
inputs, estimators and seeds are unchanged.
"""
from pathlib import Path
import csv,json
import phase2_analysis as pa

OLD='recorded_interaction_events'
NEW='recorded_ai_requests'

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def attach_counts(pairs, counts):
    index={r['run_id']:r for r in counts}
    assert len(index)==14 and len(pairs)==7
    rows=[]
    for source in pairs:
        row=dict(source)
        for condition in ['code','model']:
            record=index[row[condition+'_run_id']]
            total=int(record[NEW]);direct=int(record['directly_recorded_requests']);inferred=int(record['response_inferred_requests'])
            assert total==direct+inferred and min(direct,inferred)>=0
            row[condition+'_'+NEW]=total
            row[condition+'_response_inferred_requests']=inferred
        c,m=row['code_'+NEW],row['model_'+NEW]
        row['request_difference_code_minus_model']=c-m
        row['request_ratio_code_over_model']=c/m
        rows.append(row)
    return rows

def estimator_inputs(pairs):
    # The legacy estimator is reused through an explicit adapter, never by
    # overwriting the preserved source-event columns in the distributed input.
    mapped=[]
    for source in pairs:
        row=dict(source)
        for c in ['code','model']:row[c+'_'+OLD]=row[c+'_'+NEW]
        mapped.append(row)
    return mapped

def relabel(value):
    if isinstance(value,dict):return {k.replace(OLD,NEW):relabel(v) for k,v in value.items()}
    if isinstance(value,list):return [relabel(v) for v in value]
    if isinstance(value,str):return value.replace(OLD,NEW).replace('Recorded interaction/work events','Recorded requests to AI')
    return value

def paired_statistics(pairs):
    return tuple(relabel(x) for x in pa.paired_statistics(estimator_inputs(pairs)))

def maximum_sensitivity(pairs):
    return relabel(pa.maximum_sensitivity(estimator_inputs(pairs)))

def regenerate(phase, counts):
    phase=Path(phase)
    pairs=attach_counts(read(phase/'paired_analysis_input.csv'),read(counts))
    desc,effects,structured=paired_statistics(pairs)
    maximum=maximum_sensitivity(pairs)
    for name,rows in [('paired_analysis_input.csv',pairs),('paired_descriptive_statistics.csv',desc),('paired_effects.csv',effects),('maximum_observation_sensitivity.csv',maximum)]:pa.write_csv(phase/name,rows)
    (phase/'paired_statistics.json').write_text(json.dumps(structured,indent=2)+'\n',encoding='utf-8')
    figure=pa.effort_figure(estimator_inputs(pairs)).replace('Paired recorded work events','Paired recorded requests').replace('Within-team event differences','Within-team request differences').replace('(events)','(requests)')
    (phase/'paired_effort_plots.svg').write_text(figure,encoding='utf-8')
    report=pa.analysis_report(effects,read(phase/'threshold_sensitivity_summary.csv'),maximum)
    start=report.index('Timing measures ');end=report.index('\n\n## Paired results',start)
    report=report[:start]+('Timing measures recorded team development to functional completion, with the established gap rules applied to all seven matched teams. Requests use a common user-message counting rule; T04 includes two response-inferred requests and T05 uses directly reported interactions, including starter adaptation. Identical wording alone is not deduplicated. Runtime-test markers, pure acknowledgments, summary rows and command approvals are excluded. Counts describe retained evidence, with unequal completeness and no independent second coding. See data/request_counts/METHOD.md for rules and source locators.')+report[end:]
    (phase/'paired_analysis_report.md').write_text(report,encoding='utf-8')
    return effects

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase2-dir',type=Path,required=True)
    parser.add_argument('--counts',type=Path,required=True)
    args=parser.parse_args()
    effects=regenerate(args.phase2_dir,args.counts)
    print(json.dumps(next(r for r in effects if r['measure']==NEW),indent=2))
