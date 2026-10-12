"""Reproduce statistical and documentary results from distributed inputs."""
from pathlib import Path
import argparse,io,csv,hashlib,json,os,statistics,subprocess,sys,unittest
sys.dont_write_bytecode=True

CODE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--data-dir',type=Path,default=CODE.parent/'data')
p.add_argument('--results-dir',type=Path,default=CODE.parent/'results');a=p.parse_args()
D=a.data_dir.resolve()
manifest_path=CODE/'SHA256.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
assert manifest['version']=='TSE-models-vs-code-2026-10-12-r11'
for rel,expected in manifest['files'].items():
 scope,name=rel.split('/',1);assert scope in {'code','data'}
 base=CODE if scope=='code' else D;path=(base/name).resolve()
 assert path.is_relative_to(base) and hashlib.sha256(path.read_bytes()).hexdigest()==expected,'File hash mismatch: '+rel
print('Models vs Code: reproducing the study results\n',flush=True)
print('[1/4] Input and code checks passed.',flush=True)
out=a.results_dir.resolve();out.mkdir(parents=True,exist_ok=True)
assert out!=D and not out.is_relative_to(D) and out!=CODE and not out.is_relative_to(CODE), 'Results must be separate from code and input data'
sys.path.insert(0,str(CODE))
import phase2_analysis as pa,request_analysis as ra,portable_timing as pt
import reproduce_acceptance as acceptance

def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
details=[]
def run(args):
 result=subprocess.run(args,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 details.append(Path(args[1]).name+'\n'+result.stdout+result.stderr)
 (out/'RUN_DETAILS.txt').write_text('\n'.join(details),encoding='utf-8')
 if result.returncode:
  print('An analysis step failed. Details:\n'+result.stdout+result.stderr,flush=True)
  result.check_returncode()

phase=D/'reference_results/phase2';pairs=read(phase/'paired_analysis_input.csv')
verified=ra.attach_counts(pairs,ra.read(D/'request_counts/counts.csv'))
for old,new in zip(pairs,verified):
 for key in new:
  assert key in old,'Missing request field: '+key
  if 'request' in key:assert float(old[key])==float(new[key]),key
stats=out/'paired_statistics';stats.mkdir(exist_ok=True)
desc,effects,structured=ra.paired_statistics(pairs)
for name,rows in [('paired_descriptive_statistics.csv',desc),('paired_effects.csv',effects),
                  ('maximum_observation_sensitivity.csv',ra.maximum_sensitivity(pairs))]:
 pa.write_csv(stats/name,rows);assert read(stats/name)==read(phase/name),name
assert structured==json.loads((phase/'paired_statistics.json').read_text())
(stats/'paired_statistics.json').write_text(json.dumps(structured,indent=2)+'\n',encoding='utf-8')
threshold_rows,threshold_summaries=pt.regenerate(D/'timing_components/intervals.json',stats)
for name in ['threshold_sensitivity.csv','threshold_sensitivity_summary.csv']:
 assert read(stats/name)==read(phase/name),name
assert all(float(r['code_source_observed_minutes'])==float(next(p['code_source_observed_minutes'] for p in pairs if p['team_id']==r['team_id'])) and float(r['model_source_observed_minutes'])==float(next(p['model_source_observed_minutes'] for p in pairs if p['team_id']==r['team_id'])) for r in threshold_rows if r['is_primary']=='Yes')
figure=pa.effort_figure(ra.estimator_inputs(pairs)).replace('Paired recorded work events','Paired recorded requests').replace('Within-team event differences','Within-team request differences').replace('(events)','(requests)').replace('>events<','>requests<')
(stats/'paired_effort_plots.svg').write_text(figure,encoding='utf-8')
assert (stats/'paired_effort_plots.svg').read_text(encoding='utf-8')==(phase/'paired_effort_plots.svg').read_text(encoding='utf-8')

print('[2/4] Paired statistics, sensitivity analyses and plot reproduced.',flush=True)
tests=0
for folder in [CODE,CODE/'skills']:
 suite=unittest.TestLoader().discover(str(folder),pattern='test*.py')
 test_output=io.StringIO()
 result=unittest.TextTestRunner(stream=test_output,verbosity=1).run(suite)
 details.append('Tests: '+folder.name+'\n'+test_output.getvalue())
 (out/'RUN_DETAILS.txt').write_text('\n'.join(details),encoding='utf-8')
 if not result.wasSuccessful():print('Automated checks failed:\n'+test_output.getvalue(),flush=True)
 assert result.wasSuccessful();tests+=result.testsRun
print(f'[3/4] All {tests} automated checks passed.',flush=True)
skill=CODE/'skills';profiles=out/'skill_profiles'
run([sys.executable,str(skill/'generate.py'),'--outputs',str(profiles),'--inputs',str(D/'skill_extension'),'--classification',str(D/'skill_classification')])
for name in ['profiles.csv','coverage_matrix.csv','involved_profiles.csv','involved_coverage_matrix.csv','it_involved_profiles.csv','it_involved_coverage_matrix.csv']:
 assert read(profiles/name)==read(D/'reference_results/skill_extension'/name),name
assert json.loads((profiles/'summary.json').read_text())==json.loads((D/'reference_results/skill_extension/summary.json').read_text())
run([sys.executable,str(skill/'describe_runs.py'),'--outputs',str(profiles),'--inputs',str(D/'skill_extension')])
assert read(profiles/'per_run_skills.csv')==read(D/'reference_results/skill_extension/per_run_skills.csv')
assert (profiles/'per_run_skills.md').read_text(encoding='utf-8')==(D/'reference_results/skill_extension/per_run_skills.md').read_text(encoding='utf-8')
run([sys.executable,str(skill/'reproduce_matrix.py'),'--output-dir',str(profiles),'--inputs',str(D/'skill_extension')])
assert read(profiles/'skills_matrix_cells.csv')==read(D/'reference_results/skill_extension/skills_matrix_cells.csv')
acceptance_out=out/'acceptance';acceptance_out.mkdir(exist_ok=True);acceptance.generate(acceptance_out,D)
for name in ['reported_checks.csv','reported_checklist.csv','run_by_scenario_matrix.csv','endpoint_evidence.csv']:
 assert read(acceptance_out/name)==read(D/'supplement/acceptance'/name),name
it=read(profiles/'it_involved_profiles.csv')
counts={c:[int(r['involved_labels']) for r in it if r['strategy']==c] for c in ['Code','Model']}
report=dict(version=manifest['version'],tests_passed=tests,paired_statistics_match=True,
 skill_profiles_match=True,threshold_sensitivity_match=True,paired_plot_match=True,
 acceptance_transcriptions_match=True,category_evidence_matrix_match=True,n_pairs=len(pairs),
 time_median=statistics.median([float(r['code_source_observed_minutes'])-float(r['model_source_observed_minutes']) for r in pairs]),
 IT_counts=counts,capsule_version=manifest['version'],manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),files_verified=len(manifest['files']),acceptance_reports=14,raw_history_extraction_performed=False,application_reexecution_performed=False,reviewer_access_verified_by_run=False,raw_extraction=False,independent_semantic_validation=False,
 comparison_policy='CSV rows and JSON values match exactly; SVG and Markdown text match exactly after universal newline decoding.',
 scope='Paired statistics, gap-threshold and maximum-observation sensitivities from distributed measurements and intervals, category profiles, paired plot and author-report transcriptions. No independent recoding, application re-execution or security validation.')
assert not any(path.suffix.lower() in {'.pdf','.tex','.aux','.log','.cls','.sty'} for path in out.rglob('*') if path.is_file())
guide=f"""# Study results reproduced

The run completed successfully for {len(pairs)} matched two-person teams. All {tests} automated checks passed, and all regenerated outputs match the supplied reference results.

## Where to find the results

| Folder | Contents |
| --- | --- |
| `paired_statistics/` | Development-time and recorded-request comparisons, sensitivity analyses, and the paired plot (`paired_effort_plots.svg`). |
| `skill_profiles/` | Technical-category summaries, the evidence matrix, and descriptions of each team's two runs (`per_run_skills.md`). |
| `acceptance/` | Tables transcribed from the authors' functional acceptance reports. |

CSV files contain tables that can be opened in a spreadsheet application. The SVG file is the study plot. Markdown files provide readable descriptions.

## What this run establishes

It reproduces the analyses from the supplied measurements, timing intervals and annotations. The study contains seven matched teams, each using both development approaches.

Acceptance tables reproduce the authors' reports; the run does not execute the participant applications or independently reassess the evidence. Technical-category counts describe identified technical content rather than effort, difficulty or complete human skill requirements.

## Detailed verification

`REPRODUCTION_REPORT.json` records the file checks and exact result comparisons. `RUN_DETAILS.txt` contains the test output and analysis diagnostics. A successful run verifies computational reproduction within this scope; reviewer access is checked separately.
"""
(out/'README.md').write_text(guide,encoding='utf-8')
(out/'REPRODUCTION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('[4/4] Category profiles, evidence matrix and acceptance tables reproduced.',flush=True)
print('\nSUCCESS: All reproduced results match the supplied reference results.',flush=True)
print(f'Study: {len(pairs)} matched teams, each using both development approaches.',flush=True)
print('\nOpen /results/README.md for a guide to the results.\n'
      '  paired_statistics/  Statistics, sensitivity analyses and plot\n'
      '  skill_profiles/     Category summaries and evidence matrix\n'
      '  acceptance/         Tables from author acceptance reports\n'
      '\nVerification details: REPRODUCTION_REPORT.json and RUN_DETAILS.txt.\n'
      'Scope: Reanalysis of supplied study data; participant applications are not rerun.',flush=True)
