"""Describe documented skills and their users in each of the seven paired runs."""
import argparse,csv,json,hashlib
from pathlib import Path
from generate import loadcsv,validate,COMMON

def build(rows,taxonomy):
    validate(rows,taxonomy)
    records=[];md=['# Skills documented in the seven Code and seven Model runs','',
        'AI and human users are classified by the same activity taxonomy. Entries describe recorded activity in these runs. Actor combinations combine distinct annotations; joint means a jointly coded activity. Proposed taxonomy gaps remain separate.','']
    for i in range(1,8):
        team=f'T{i:02}'
        md += ['## '+team,'']
        for strategy in ('Code','Model'):
            rr=[r for r in rows if r['team']==team and r['strategy']==strategy and r['scope'] in COMMON]
            md+=['### '+strategy,'']
            for status,category,title in [('observed use','taxonomy','Observed skills'),('observed use','gap','Additional technical activities / proposed gaps'),
                                          ('supported requirement','taxonomy','Implementation-supported facets (R)'),('supported requirement','gap','Implementation-supported proposed gaps')]:
                subset=[r for r in rr if r['status']==status and (r['skill_id'] in taxonomy)==(category=='taxonomy')]
                if not subset:continue
                md+=['**'+title+'**','']
                names=sorted({r['skill_name'] for r in subset},key=str.casefold)
                for name in names:
                    group=[r for r in subset if r['skill_name']==name]
                    ids=', '.join(sorted({r['skill_id'] for r in group}))
                    actors=', '.join(a for a in ('human','AI','joint','uncertain') if any(r['actor']==a for r in group))
                    evidence=', '.join(r['id'] for r in group)
                    records.append(dict(team=team,strategy=strategy,status=status,category=category,skill=name,
                        skill_ids=ids,users=actors,evidence_ids=evidence))
                    md.append('- **'+name+'** ('+ids+'): '+actors+'. Evidence: '+evidence+'.')
                md.append('')
            unresolved=[r for r in rr if r['status']=='unresolved']
            if unresolved:
                refs=', '.join(r['id'] for r in unresolved)
                md+=['Unresolved record references (not counted as observed skills): '+refs+'.','']
    return records,'\n'.join(md)+'\n'

def main():
    cap=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,default=cap/'data/skill_extension')
    p.add_argument('--outputs',type=Path,default=cap/'results/skill_extension');a=p.parse_args()
    for n,h in json.loads((a.inputs/'INPUT_SHA256.json').read_text(encoding='utf-8')).items():assert hashlib.sha256((a.inputs/n).read_bytes()).hexdigest()==h
    rows=json.loads((a.inputs/'annotations.json').read_text(encoding='utf-8'))
    taxonomy={r['Skill_ID']:r for r in loadcsv(a.inputs/'taxonomy_reference.csv')}
    records,md=build(rows,taxonomy)
    a.outputs.mkdir(parents=True,exist_ok=True)
    with (a.outputs/'per_run_skills.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (a.outputs/'per_run_skills.md').write_text(md,encoding='utf-8')
    assert len({(r["team"],r["strategy"]) for r in records})==14
    print("Generated per-run category CSV and Markdown descriptions for 14 runs.")
if __name__=="__main__":main()
