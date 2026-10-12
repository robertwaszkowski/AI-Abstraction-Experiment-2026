from pathlib import Path
import argparse,json,re,hashlib,zipfile,xml.etree.ElementTree as ET
from collections import Counter

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
patterns=[
 ('email',r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}','[EMAIL_REDACTED]'),
 ('local_user_path',r'(?i)([A-Z]:[\\/]+Users[\\/]+)[^\\/\s\"\']+',r'\1[USER_REDACTED]'),
 ('unix_user_path',r'/(?:Users|home)/[^/\s\"\']+','/[LOCAL_USER_REDACTED]'),
 ('url',r'https?://[^\s<>\"\)\]\}]+','[URL_REDACTED]'),
 ('api_key',r'\b(?:AIza[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9_-]{20,})','[KEY_REDACTED]'),
 ('jwt',r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}','[TOKEN_REDACTED]'),
 ('credential_value',r'(?i)((?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*[\"\'])([^\"\'\r\n]+)([\"\'])',r'\1[VALUE_REDACTED]\3'),
 ('attributed_identity',r'(?im)^((?:author|autor|participant|uczestnik|student|prepared by|opracowa[lł])\s*:\s*)[^\r\n]+',r'\1[IDENTITY_REDACTED]'),
 ('contact_value',r'(?i)((?:phone|telefon|mobile|PESEL)\s*[=:]\s*[\"\']?)[+0-9][0-9 ()-]{5,}',r'\1[CONTACT_REDACTED]')]

def export(source,dest):
 assert not dest.exists();dest.mkdir(parents=True)
 entries=[];totals=Counter()
 for kind,strategy in [('code_generation','Code'),('model_generation','Model')]:
  for run in sorted((source/kind).iterdir()):
   if not run.is_dir():continue
   team='T'+re.search(r'_(\d\d)',run.name).group(1)
   for index,p in enumerate(sorted((run/'prompt').iterdir()),1):
    if p.suffix not in ['.docx','.md','.txt','.json']:continue
    counts=Counter();omitted=0
    def clean(s):
     for label,pattern,replacement in patterns:
      s,n=re.subn(pattern,replacement,s);counts[label]+=n
     return s
    def walk(x):
     if isinstance(x,str):return clean(x)
     if isinstance(x,list):return [walk(v) for v in x]
     if isinstance(x,dict):return {k:('[IDENTITY_REDACTED]' if k.lower() in ['username','author','creator','lastmodifiedby'] else walk(v)) for k,v in x.items()}
     return x
    if p.suffix=='.docx':
     with zipfile.ZipFile(p) as z:
      root=ET.fromstring(z.read('word/document.xml'))
      omitted=len([n for n in z.namelist() if n.startswith('word/media/')])
      paragraphs=[]
      for i,el in enumerate(v for v in root.iter() if v.tag.endswith('}p')):
       text=''.join((v.text or '') if v.tag.endswith('}t') else ('\n' if v.tag.endswith('}br') else '') for v in el.iter())
       paragraphs.append({'paragraph_index':i,'text':clean(text),'drawing_elements':sum(v.tag.endswith('}drawing') or v.tag.endswith('}pict') for v in el.iter())})
      content={'paragraphs':paragraphs}
    elif p.suffix=='.json':content=walk(json.loads(p.read_text(encoding='utf-8-sig')))
    else:content={'text':clean(p.read_text(encoding='utf-8-sig'))}
    record={'team':team,'approach':strategy,'source_filename':p.name,'source_format':p.suffix,'source_sha256':sha(p),'embedded_media_files_omitted':omitted,'content':content}
    out=dest/team/strategy/f'record_{index:02d}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    entries.append({'team':team,'approach':strategy,'record':out.relative_to(dest).as_posix(),'source_filename':p.name,'source_format':p.suffix,'source_sha256':sha(p),'export_sha256':sha(out),'embedded_media_files_omitted':omitted,'redactions':dict(counts)})
    totals.update(counts)
 (dest/'manifest.json').write_text(json.dumps({'records':entries,'redaction_totals':dict(totals),'record_count':len(entries)},indent=2)+'\n',encoding='utf-8')
 assert len(entries)==51
 for team in [f'T{i:02d}' for i in range(1,8)]:assert sum(e['team']==team and e['approach']=='Model' for e in entries)==6
 print(json.dumps({'records':len(entries),'teams':7,'model_histories':42,'omitted_embedded_media_files':sum(e['embedded_media_files_omitted'] for e in entries),'redactions':dict(totals)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.source,a.output)
