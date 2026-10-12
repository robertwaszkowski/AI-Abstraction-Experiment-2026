"""Syntax-only audit of retained Code deliveries; never executes application code.
Requires Python 3.12, Node.js and @babel/parser 7.28.5.
"""
from pathlib import Path
import argparse, ast, csv, hashlib, json, re, subprocess, sys
from collections import Counter
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

class Scripts(HTMLParser):
    def __init__(self): super().__init__(); self.active=None; self.parts=[]; self.scripts=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='script':
            a=dict(attrs); typ=a.get('type','').lower()
            if 'src' not in a and typ in ('','module','text/javascript','application/javascript'):
                self.active='module' if typ=='module' else 'script'; self.parts=[]
    def handle_data(self,data):
        if self.active: self.parts.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=='script' and self.active:
            self.scripts.append((''.join(self.parts),self.active)); self.active=None

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir',type=Path,required=True)
    ap.add_argument('--results-dir',type=Path,required=True)
    ap.add_argument('--node',required=True)
    ap.add_argument('--parser-module',type=Path,required=True)
    a=ap.parse_args(); out=a.results_dir; out.mkdir(parents=True,exist_ok=True)
    results=[]; queue=[]; ignored={'.git','node_modules','__pycache__','.venv','venv','prompt_backup'}
    for n in range(1,8):
        candidates=[p for p in (a.data_dir/'code_generation').iterdir() if re.fullmatch(fr'code_{n:02d}(?: \(1\))?',p.name)]
        if len(candidates)!=1: raise ValueError(f'Expected one artifact set for T{n:02d}')
        base=candidates[0]/'code'
        for f in sorted(base.rglob('*')):
            if not f.is_file() or ignored.intersection(f.relative_to(base).parts): continue
            rel=f.relative_to(base).as_posix()
            if f.name.startswith('.env'): continue
            ext=f.suffix.lower()
            if ext not in {'.py','.js','.mjs','.cjs','.jsx','.ts','.tsx','.json','.html','.css','.prisma','.yaml','.yml','.sql','.sh'}:continue
            row={'team_id':f'T{n:02d}','relative_path':rel,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'kind':ext,'status':'not_checked','diagnostic':''}
            results.append(row)
            raw=f.read_bytes()
            encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
            try: text=raw.decode(encoding)
            except UnicodeError as e:
                row.update(status='fail',diagnostic=str(e));continue
            if ext in {'.py','.json'}:
                try:
                    if ext=='.py': compile(text,rel,'exec')
                    else:json.loads(text)
                    row['status']='pass'
                except (SyntaxError,ValueError) as e:row.update(status='fail',diagnostic=str(e))
            elif ext in {'.js','.mjs','.cjs','.jsx','.ts','.tsx'}:
                queue.append({'id':len(results)-1,'source':text,'ext':ext,'sourceType':'module' if ext=='.mjs' else 'commonjs' if ext=='.cjs' else 'unambiguous'})
            elif ext=='.html':
                h=Scripts();h.feed(text);row.update(status='embedded_scripts_only',diagnostic=f'{len(h.scripts)} inline JavaScript blocks; markup not validated')
                for j,(source,source_type) in enumerate(h.scripts,1):
                    results.append(dict(row,relative_path=rel+f'#script-{j}',kind='inline_javascript',status='not_checked',diagnostic=''))
                    queue.append({'id':len(results)-1,'source':source,'ext':'.js','sourceType':source_type})
    run=subprocess.run([a.node,str(Path(__file__).with_name('parse_code_sources.cjs')),str(a.parser_module.resolve())],input=json.dumps(queue),capture_output=True,text=True,encoding='utf-8')
    if run.returncode:raise RuntimeError(run.stderr)
    parsed=json.loads(run.stdout)
    if parsed['parser_version']!='7.28.5':raise ValueError('Use the pinned @babel/parser version 7.28.5')
    for r in parsed['result']:results[r['id']].update(status=r['status'],diagnostic=r['diagnostic'])
    with (out/'per_file.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    model_checks=[]
    for n in range(1,8):
        folders=[p for p in (a.data_dir/'model_generation').iterdir() if re.fullmatch(fr'model_{n:02d}(?: \(1\))?',p.name)]
        if len(folders)!=1: raise ValueError(f'Expected one Model artifact set for T{n:02d}')
        base=folders[0]/'code'; files=[p for p in base.rglob('*') if p.is_file() and not ignored.intersection(p.relative_to(base).parts)]
        bp=[p for p in files if p.suffix=='.bpmn']; jp=[p for p in files if p.suffix=='.json']
        if len(bp)!=3 or len(jp)!=6:raise ValueError(f'Unexpected Model file counts for T{n:02d}')
        for f in jp:json.loads(f.read_text(encoding='utf-8-sig'))
        for f in bp:
            tree=ET.parse(f).getroot()
            if tree.tag.rsplit('}',1)[-1]!='definitions' or not any(e.tag.rsplit('}',1)[-1]=='process' for e in tree.iter()) or f.stem not in {q.stem for q in jp}:raise ValueError(f'Model structure check failed for T{n:02d}')
        model_checks.append({'team_id':f'T{n:02d}','bpmn_parsed':3,'json_parsed':6,'bpmn_structure_and_same_stem_matches':3,'inputs_sha256':{f.relative_to(base).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in bp+jp}})
    (out/'model_crosscheck.json').write_text(json.dumps(model_checks,indent=2)+'\n',encoding='utf-8')
    summary={'scope':'All retained .py/.js/.mjs/.cjs/.jsx/.ts/.tsx/.json files and inline JavaScript blocks; CSS/Prisma/YAML/SQL/shell and HTML markup not validated. No builds, typechecking, dependency resolution or behavioral tests.', 'tools':{'python':sys.version.split()[0],'node':subprocess.check_output([a.node,'--version'],text=True).strip(),'babel_parser':parsed['parser_version']},'teams':{f'T{n:02d}':dict(Counter(r['status'] for r in results if r['team_id']==f'T{n:02d}')) for n in range(1,8)},'kinds':dict(Counter(r['kind'] for r in results if r['status'] in {'pass','fail'})),'failures':[r for r in results if r['status']=='fail']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 1 if summary['failures'] else 0
if __name__=='__main__':raise SystemExit(main())
