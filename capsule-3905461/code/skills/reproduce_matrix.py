"""Reproduce category-by-team evidence cells as CSV, without document output."""
import argparse,csv,hashlib,json
from pathlib import Path
from generate import validate,loadcsv,COMMON

def build(rows,taxonomy):
 validate(rows,taxonomy)
 eligible=[r for r in rows if r['status'] in {'observed use','supported requirement'} and r['scope'] in COMMON]
 native=sorted({r['skill_name'] for r in eligible if r['skill_id'] in taxonomy},key=str.casefold)
 gaps=sorted({r['skill_id'] for r in eligible if r['skill_id'] not in taxonomy})
 gaplabels={'GAP01':'Validation / diagnosis','GAP02':'Role / access binding','GAP03':'Dependency integration','GAP04':'Python programming'}
 keys=[('taxonomy',x) for x in native]+[('gap',x) for x in gaps]
 code={'human':'H','AI':'A','joint':'J','uncertain':'U'};cells=[]
 for kind,key in keys:
  group=[r for r in eligible if (r['skill_name']==key if kind=='taxonomy' else r['skill_id']==key)]
  ids=', '.join(sorted({r['skill_id'] for r in group}));label=key if kind=='taxonomy' else gaplabels[key]+' (gap)'
  for j in range(14):
   team=f'T{j//2+1:02}';strategy='Code' if j%2==0 else 'Model'
   hits=[r for r in group if r['team']==team and r['strategy']==strategy];parts=[]
   for status,tag in [('observed use','O'),('supported requirement','R')]:
    actors=[a for a in code if any(r['actor']==a and r['status']==status for r in hits)]
    if actors:parts.append(tag+':'+''.join(code[a] for a in actors))
   cells.append(dict(row_label=label,category=kind,contextual_skill_ids=ids,team=team,strategy=strategy,
    symbol='/'.join(parts) if parts else '?',state='observed and/or implementation-supported' if hits else 'not established / unknown',
    actors=';'.join(a for a in code if any(r['actor']==a for r in hits)),evidence_ids=';'.join(r['id'] for r in hits)))
 return cells

def main():
 cap=Path(__file__).resolve().parents[2]
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,default=cap/'data/skill_extension')
 p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 for name,expected in json.loads((a.inputs/'INPUT_SHA256.json').read_text(encoding='utf-8')).items():
  assert hashlib.sha256((a.inputs/name).read_bytes()).hexdigest()==expected
 rows=json.loads((a.inputs/'annotations.json').read_text(encoding='utf-8'))
 taxonomy={r['Skill_ID']:r for r in loadcsv(a.inputs/'taxonomy_reference.csv')}
 cells=build(rows,taxonomy);a.output_dir.mkdir(parents=True,exist_ok=True)
 with (a.output_dir/'skills_matrix_cells.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(cells[0]));w.writeheader();w.writerows(cells)
 print(json.dumps(dict(rows=len(cells)//14,cells=len(cells),supported_cells=sum(c['symbol']!='?' for c in cells),unknown_cells=sum(c['symbol']=='?' for c in cells))))
if __name__=='__main__':main()
