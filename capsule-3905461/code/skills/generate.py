"""Reproduce descriptive skill summaries from explicit, provisional annotations.

Standard library only. No study applications, network calls, or AI recoding.
Optional source checking verifies separately supplied canonical evidence.
"""
import argparse, collections, csv, hashlib, json
from pathlib import Path

ACTORS={'human','AI','joint','uncertain'}
STATUSES={'observed use','supported requirement','unresolved','excluded'}
GAPS={'GAP01','GAP02','GAP03','GAP04'}
COMMON={'common','starter-adaptation'}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def loadcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def validate(rows,taxonomy):
    seen=set()
    for r in rows:
        assert r['id'] not in seen, 'Duplicate annotation ID'
        seen.add(r['id'])
        assert r['actor'] in ACTORS and r['status'] in STATUSES
        assert r['skill_id'] in taxonomy or r['skill_id'] in GAPS
        if r['skill_id'] in taxonomy: assert r['skill_name']==taxonomy[r['skill_id']]['Skill']
        assert r['sources'] and r['justification'] and r['human_necessity']
def summarize(rows,taxonomy):
    validate(rows,taxonomy)
    all_labels=sorted({r['Skill'] for r in taxonomy.values()})
    profiles=[];matrix=[]
    for team in (f'T{i:02}' for i in range(1,8)):
        for strategy in ('Code','Model'):
            rr=[r for r in rows if r['team']==team and r['strategy']==strategy]
            obs=[r for r in rr if r['status']=='observed use' and r['scope'] in COMMON]
            native=[r for r in obs if r['skill_id'] in taxonomy]
            labels=sorted({r['skill_name'] for r in native})
            profiles.append(dict(team=team,strategy=strategy,annotation_rows=len(rr),
                selected_observed_labels=len(labels),labels='; '.join(labels),
                observed_gap_categories='; '.join(sorted({r['skill_id'] for r in obs if r['skill_id'] in GAPS})),
                human_observed_labels='; '.join(sorted({r['skill_name'] for r in native if r['actor']=='human'})),
                human_necessary_skills='Not established',complete_repertoire=False))
            for name in all_labels:
                hits=[r for r in native if r['skill_name']==name]
                matrix.append(dict(team=team,strategy=strategy,skill_label=name,
                    state='observed in selected evidence' if hits else 'not established / unknown',
                    evidence_ids=';'.join(r['id'] for r in hits),actors=';'.join(sorted({r['actor'] for r in hits}))))
    return profiles,matrix
def verify_sources(manifest,source_root):
    source_root=source_root.resolve();checked=0
    for row in manifest:
        # Both locators identify the same canonical data-relative layout. Restored
        # originals use the current capsule locator; earlier evidence keeps its
        # frozen staging locator. The caller explicitly supplies the data root.
        markers=['/staged_capsule/data/','/capsule-3905461/data/']
        marker=next((m for m in markers if m in row['path']),None)
        if row['path'].startswith(('code_generation/','model_generation/')):
            rel=row['path']
        else:
            assert marker is not None, 'Noncanonical source needs an explicit separate mapping'
            rel=row['path'].split(marker,1)[1]
        p=(source_root/rel).resolve()
        assert p.is_relative_to(source_root), 'Source path escaped canonical root'
        assert p.is_file() and digest(p)==row['sha256'], 'Source missing or hash differs: '+rel
        checked+=1
    return checked
def involved(rows,taxonomy):
    """Union of observed and implementation-supported facets; no duplicated labels."""
    profiles=[];matrix=[]
    for team in (f'T{i:02}' for i in range(1,8)):
        for strategy in ('Code','Model'):
            rr=[r for r in rows if r['team']==team and r['strategy']==strategy and r['scope'] in COMMON and r['status'] in {'observed use','supported requirement'}]
            native=[r for r in rr if r['skill_id'] in taxonomy]
            observed={r['skill_name'] for r in native if r['status']=='observed use'}
            required={r['skill_name'] for r in native if r['status']=='supported requirement'}
            profiles.append(dict(team=team,strategy=strategy,involved_labels=len(observed|required),
                observed_labels=len(observed),supported_requirement_labels=len(required),
                requirement_only_labels=len(required-observed),labels='; '.join(sorted(observed|required)),
                proposed_gaps='; '.join(sorted({r['skill_id'] for r in rr if r['skill_id'] in GAPS}))))
            for name in sorted({r['Skill'] for r in taxonomy.values()}):
                hit=[r for r in native if r['skill_name']==name]
                o=any(r['status']=='observed use' for r in hit);q=any(r['status']=='supported requirement' for r in hit)
                matrix.append(dict(team=team,strategy=strategy,skill_label=name,state='O/R' if o and q else 'O' if o else 'R' if q else '?',
                    evidence_ids=';'.join(r['id'] for r in hit),actors=';'.join(sorted({r['actor'] for r in hit}))))
    return profiles,matrix
def writecsv(p,items):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)

def load_classification(directory,taxonomy):
    provenance=json.loads((directory/'PROVENANCE.json').read_text(encoding='utf-8'))
    assert digest(directory/'p2_category_mapping.csv')==provenance['mapping_sha256']
    rows=loadcsv(directory/'p2_category_mapping.csv')
    mapping={r['Skill_ID']:r['category'] for r in rows}
    assert len(rows)==len(mapping)==len(taxonomy) and set(mapping)==set(taxonomy)
    assert all(r['source_label']==taxonomy[r['Skill_ID']]['Skill'] for r in rows)
    assert collections.Counter(mapping.values())=={'IT':163,'domain':46}
    return mapping

def it_involved(rows,taxonomy,classification):
    """Apply the explicit ID classification before deduplicating labels/actors."""
    assert set(classification)==set(taxonomy)
    assert set(classification.values()) <= {'IT','domain'}
    it_taxonomy={k:v for k,v in taxonomy.items() if classification[k]=='IT'}
    eligible=[r for r in rows if r['skill_id'] in it_taxonomy or r['skill_id'] in GAPS]
    return involved(eligible,it_taxonomy)
def main():
    capsule=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,default=capsule/'data/skill_extension')
    p.add_argument('--outputs',type=Path,default=capsule/'results/skill_extension')
    p.add_argument('--classification',type=Path,default=capsule/'data/skill_classification')
    p.add_argument('--source-data-dir',type=Path,help='Optional original canonical study data; verified read-only')
    a=p.parse_args();inputs=a.inputs.resolve();out=a.outputs.resolve()
    assert out!=inputs and not out.is_relative_to(inputs), 'Outputs must be separate from annotation inputs'
    if a.source_data_dir:
        assert not out.is_relative_to(a.source_data_dir.resolve()), 'Outputs cannot overwrite raw source tree'
    for name,expected in json.loads((inputs/'INPUT_SHA256.json').read_text(encoding='utf-8')).items():
        f=(inputs/name).resolve();assert f.is_relative_to(inputs) and digest(f)==expected,'Annotation input hash mismatch: '+name
    rows=json.loads((inputs/'annotations.json').read_text(encoding='utf-8'))
    taxonomy={r['Skill_ID']:r for r in loadcsv(inputs/'taxonomy_reference.csv')}
    assert len(taxonomy)==209 and len({r['Skill'] for r in taxonomy.values()})==137
    assert {(r['team'],r['strategy']) for r in rows}=={(f'T{i:02}',s) for i in range(1,8) for s in ('Code','Model')}
    profiles,matrix=summarize(rows,taxonomy)
    fullprofiles,fullmatrix=involved(rows,taxonomy)
    classification=load_classification(a.classification,taxonomy)
    itprofiles,itmatrix=it_involved(rows,taxonomy,classification)
    source_checked=verify_sources(json.loads((inputs/'source_manifest.json').read_text(encoding='utf-8')),a.source_data_dir) if a.source_data_dir else None
    summary=dict(teams=7,conditions=14,annotation_rows=len(rows),
        statuses=dict(collections.Counter(r['status'] for r in rows)),taxonomy_ids=209,exact_taxonomy_labels=137,
        independent_coding=False,complete_repertoires=False,human_necessity_established=False,
        weighted_analysis=False,source_files_verified=source_checked,
        primary_profile='it_involved_profiles.csv: IT-only union of observed and implementation-supported category labels',
        complete_profile='involved_profiles.csv: complete union including domain categories',
        classification_version='P6-IT-classification-2026-10-02',
        IT_taxonomy_ids=163,domain_taxonomy_ids=46,
        warning='Technical-content inventory with overlapping taxonomy levels, not an effort/difficulty scale or activity frequency; unknown is not absence.')
    out.mkdir(parents=True,exist_ok=True)
    writecsv(out/'profiles.csv',profiles);writecsv(out/'coverage_matrix.csv',matrix)
    writecsv(out/'involved_profiles.csv',fullprofiles);writecsv(out/'involved_coverage_matrix.csv',fullmatrix)
    writecsv(out/'it_involved_profiles.csv',itprofiles);writecsv(out/'it_involved_coverage_matrix.csv',itmatrix)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
