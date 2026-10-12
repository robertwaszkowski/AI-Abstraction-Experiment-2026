"""Transcribe preserved author acceptance reports and endpoint evidence inputs."""
from pathlib import Path
import csv, hashlib, json, re

DEFAULT_DATA=Path(__file__).resolve().parents[1]/'data'

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def generate(output,data_dir=DEFAULT_DATA):
    data_dir=Path(data_dir).resolve()
    EVIDENCE=data_dir/'supplement/acceptance'
    output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((EVIDENCE/'report_manifest.json').read_text())
    checks=[];matrix=[];canonical={}
    for record in manifest['reports']:
        p=EVIDENCE/record['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],p.name
        text=p.read_text(encoding='utf-8')
        run=p.name.split('_author_')[0];condition='Code' if run.startswith('code') else 'Model'
        team='T'+run[-2:]
        for n,line in enumerate(text.splitlines(),1):
            if not line.startswith('| **') or '| **PASS** |' not in line:continue
            cells=[v.strip() for v in line.strip('|').split('|')]
            assert len(cells)==5 if re.match(r'^\| \*\*[123]\.\d+',line) else len(cells)==4
            label=cells[0].strip('*')
            scenario=bool(re.fullmatch(r'[123]\.\d+',label))
            process={'1':'Leave Request','2':'Change of Employment Conditions','3':'Decorations and Medals'}.get(label[0],'Technical checks') if scenario else 'Technical checks'
            role=cells[1] if scenario else ''
            action=cells[2] if scenario else cells[1]
            note=cells[4] if scenario else cells[3]
            check={'run_id':run,'team_id':team,'condition':condition,'process':process,'check_id':label,'persona_or_role':role,'required_action_or_verification_method':action,'reported_result':'PASS','notes':note,'evidence_basis':'author acceptance report','source':'reports/'+p.name,'source_sha256':record['sha256'],'source_line':n,'scope':'approved path' if scenario else 'reported technical check','independent_reexecution':'not performed by this capsule'}
            checks.append(check)
            if scenario:
                key=(label,role,action)
                canonical[key]={'step_id':label,'process':process,'persona_or_role':role,'required_action_and_expected_outcome':action,'scope':'approved path explicitly listed in reports'}
        runchecks=[x for x in checks if x['run_id']==run]
        assert len(runchecks)==33 and sum(x['scope']=='approved path' for x in runchecks)==29,run
        for process,expected in [('Leave Request',9),('Change of Employment Conditions',10),('Decorations and Medals',10)]:
            selected=[x for x in runchecks if x['process']==process]
            assert len(selected)==expected
            matrix.append({'run_id':run,'team_id':team,'condition':condition,'process':process,'reported_pass_steps':expected,'reported_completion':'PASS for listed approved path','source':'reports/'+p.name,'source_sha256':record['sha256'],'source_line_start':selected[0]['source_line'],'source_line_end':selected[-1]['source_line'],'independent_reexecution':'not performed by this capsule'})
    assert len(checks)==462 and len(matrix)==42 and len(canonical)==29
    write(output/'reported_checks.csv',checks)
    write(output/'reported_checklist.csv',sorted(canonical.values(),key=lambda r:(int(r['step_id'].split('.')[0]),int(r['step_id'].split('.')[1]))))
    write(output/'run_by_scenario_matrix.csv',matrix)
    endpoints=read(EVIDENCE/'endpoint_inputs.csv');assert len(endpoints)==14
    confirmation=json.loads((EVIDENCE/'author_confirmation.json').read_text())
    assert confirmation['reports_completed_during_evaluation'] is True
    assert confirmation['required_code_team_repairs_after_recorded_endpoints'] is False
    pairs=read(data_dir/'reference_results/phase2/paired_analysis_input.csv')
    for row in endpoints:
        pair=next(p for p in pairs if p['team_id']==row['team_id'])
        row['reported_development_minutes']=row['recorded_development_minutes']
        row['recorded_development_minutes']=pair[row['condition'].lower()+'_source_observed_minutes']
    write(output/'endpoint_evidence.csv',endpoints)

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--results-dir",type=Path,required=True);p.add_argument("--data-dir",type=Path,default=DEFAULT_DATA);a=p.parse_args()
    generate(a.results_dir,a.data_dir)
