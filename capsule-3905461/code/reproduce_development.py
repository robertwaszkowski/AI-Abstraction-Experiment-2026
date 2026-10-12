"""Reproduce seven-team recorded development time to functional completion."""
from pathlib import Path
import argparse,csv,hashlib,json,shutil,statistics,subprocess,sys,tempfile
import calculate_metrics as cm
import phase2_analysis as pa
import development_durations as dd
REVISION='P9-recorded-development-time-2026-09-30'

def run_dir(data,condition,run):
    root=data/cm.CONDITION_DIR[condition]
    if (root/run).is_dir():return root/run
    matches=list(root.glob(run+' (*)'))
    if len(matches)!=1:raise ValueError(f'Expected one retained directory for {run}')
    return matches[0]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--results-dir',type=Path,required=True)
    a=p.parse_args()
    data,out=a.data_dir.resolve(),a.results_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    phase=out/'phase2';evidence=out/'timing_evidence';evidence.mkdir(exist_ok=True)
    specs=cm.read_specs(data/'experiments.csv')
    source_locations=json.loads(Path(__file__).with_name('timing_source_locations.json').read_text(encoding='utf-8'))
    hashes,timing,table_rows,reviews,model_checks=[],[],[],[],[]
    for spec in specs:
        prompt=run_dir(data,spec.condition,spec.experiment_id)/'prompt'
        paths=cm.prompt_text_files(prompt);minutes,events,*_=cm.measure_prompts(spec,prompt,45)
        locators=[]
        for path in paths:
            rel=path.relative_to(data).as_posix()
            hashes.append(dict(run_id=spec.experiment_id,source=rel,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            if spec.time_method=='duration_rows':
                detail=dd.measure(path)
                for row in detail['duration_rows']:
                    table_rows.append(dict(run_id=spec.experiment_id,source=rel,**row))
                    locators.append(f"{path.name}:table:{row['table']}:row:{row['row']}:paragraph:{row['paragraph']}")
                reviews.extend(dict(run_id=spec.experiment_id,source=rel,**row) for row in detail['review_intervals'])
        if spec.condition=='Model':
            stamps=sorted(set(t for path in paths for t in cm.json_conversation(path)[0]))
            for threshold in [15,30,45,60]:
                value=round(cm.sessionized_seconds(stamps,threshold)/60,2);assert value==minutes
                model_checks.append(dict(run_id=spec.experiment_id,threshold_minutes=threshold,minutes=value,maximum_gap_minutes=max((b-a).total_seconds()/60 for a,b in zip(stamps,stamps[1:]))))
        timing.append(dict(team_id=spec.team_id,run_id=spec.experiment_id,condition=spec.condition,
            recorded_development_minutes=minutes,recorded_events=events,record_type=spec.time_method,
            source_files=';'.join(p.relative_to(data).as_posix() for p in paths),
            scope='Three study workflows including starter adaptation' if spec.experiment_id=='code_05' else 'Study development including effective requirements',source_locations=source_locations[spec.experiment_id],table_locations=';'.join(locators)))
    for name,rows in [('per_run.csv',timing),('source_manifest.csv',hashes),('duration_rows.csv',table_rows),('review_intervals.csv',reviews),('model_break_checks.csv',model_checks)]:pa.write_csv(evidence/name,rows)
    with tempfile.TemporaryDirectory(prefix='p9-current-') as tmp:
        canonical=Path(tmp)/'data';canonical.mkdir();shutil.copy2(data/'experiments.csv',canonical/'experiments.csv')
        for spec in specs:shutil.copytree(run_dir(data,spec.condition,spec.experiment_id),canonical/cm.CONDITION_DIR[spec.condition]/spec.experiment_id,ignore=shutil.ignore_patterns('.git','__pycache__'))
        subprocess.run([sys.executable,str(Path(__file__).with_name('phase2_analysis.py')),'--data-dir',str(canonical),'--results-dir',str(phase)],check=True)
        cm.write_results(out,cm.analyze(canonical,specs,45),45)
    metadata=dict(revision=REVISION,independent_unit='two-person team',n_pairs=7,construct='Recorded development time to functional completion',break_rule='Exclude gaps equal to or longer than 45 minutes in full; include review gaps shorter than 45 minutes',t04_recorded_minutes=next(r['recorded_development_minutes'] for r in timing if r['run_id']=='code_04'))
    (out/'CURRENT_REVISION.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (out/'README.md').write_text('# Current results\n\n'+REVISION+'\n\nSeven matched two-person teams; recorded development time to functional completion. Paired statistics and sensitivities are in phase2/. Source locators, duration rows and review intervals are in timing_evidence/. Gaps equal to or longer than 45 minutes are breaks. T05 includes starter adaptation for the three study workflows. Skills remain descriptive.\n')
    import request_analysis as ra
    ra.regenerate(phase, Path(__file__).resolve().parents[1]/"data/request_counts/counts.csv")
    print(json.dumps(dict(revision=REVISION,code_minutes=[r['recorded_development_minutes'] for r in timing if r['condition']=='Code']),indent=2))

if __name__=='__main__':main()
