"""Guard scientific counting and evidence-boundary rules, not inferred competence."""
import copy, unittest
from generate import summarize,validate,involved,it_involved
TAX={'SK061':{'Skill':'JavaScript'},'SK144':{'Skill':'JavaScript'},'SK145':{'Skill':'JSON'}}
def row(i,skill='SK061',actor='AI',status='observed use',scope='common'):
    return dict(id=i,team='T01',strategy='Code',skill_id=skill,skill_name=TAX[skill]['Skill'] if skill in TAX else 'Python gap',
                actor=actor,status=status,scope=scope,sources=[{'path':'source'}],justification='Fixture activity',human_necessity='Not established')
class ScientificBoundaries(unittest.TestCase):
    def test_explicit_it_mapping_preserves_plus_exception_and_technical_facet(self):
        tax={'SK032':{'Skill':'+Lookup/Drop-down'},'SK113':{'Skill':'+Column Expressions'},'SK046':{'Skill':'Control Structures'}}
        mapping={'SK032':'domain','SK113':'IT','SK046':'IT'}
        rows=[]
        for actor in ['human','AI','joint','uncertain']:
            for strategy in ['Code','Model']:
                for skill in tax:
                    r=row(str(len(rows)));r.update(actor=actor,strategy=strategy,skill_id=skill,skill_name=tax[skill]['Skill'])
                    rows.append(r)
        profiles,_=it_involved(rows,tax,mapping)
        for p in profiles[:2]:
            self.assertEqual(p['involved_labels'],2)
            self.assertIn('+Column Expressions',p['labels'])
            self.assertIn('Control Structures',p['labels'])
            self.assertNotIn('+Lookup/Drop-down',p['labels'])
        self.assertEqual(involved(rows,tax)[0][0]['involved_labels'],3)
    def test_involved_union_includes_requirements_once_across_actors(self):
        p,m=involved([row('1'),row('2','SK144','human','supported requirement'),row('3','SK145',status='supported requirement')],TAX)
        self.assertEqual(p[0]['involved_labels'],2)
        self.assertEqual(p[0]['observed_labels'],1)
        self.assertEqual(p[0]['requirement_only_labels'],1)
        self.assertEqual(next(x for x in m if x['team']=='T01' and x['strategy']=='Code' and x['skill_label']=='JavaScript')['state'],'O/R')
    def test_involved_union_excludes_unknowns_and_outside_scope(self):
        p,m=involved([row('1',status='unresolved'),row('2',scope='additional-preview'),row('3',scope='outside-Role-Call'),row('4',status='excluded')],TAX)
        self.assertEqual(p[0]['involved_labels'],0)
        self.assertTrue(all(x['state']=='?' for x in m))
    def test_union_deduplicates_contexts_and_actors(self):
        profiles,matrix=summarize([row('1'),row('2','SK144','human'),row('3','SK061','joint')],TAX)
        self.assertEqual(profiles[0]['selected_observed_labels'],1)
        self.assertEqual(next(x for x in matrix if x['team']=='T01' and x['strategy']=='Code' and x['skill_label']=='JavaScript')['actors'],'AI;human;joint')
    def test_unknown_is_not_absence(self):
        _,matrix=summarize([row('1')],TAX)
        self.assertTrue(all(x['state']=='not established / unknown' for x in matrix if x['skill_label']=='JSON'))
    def test_requirement_unresolved_preview_and_rolecall_do_not_enter_observed_common_set(self):
        rows=[row('1',status='supported requirement'),row('2',status='unresolved'),row('3',scope='additional-preview'),row('4',scope='outside-Role-Call')]
        self.assertEqual(summarize(rows,TAX)[0][0]['selected_observed_labels'],0)
    def test_python_gap_not_silently_counted_as_validated_taxonomy_skill(self):
        profile=summarize([row('1','GAP04')],TAX)[0][0]
        self.assertEqual(profile['selected_observed_labels'],0)
        self.assertEqual(profile['observed_gap_categories'],'GAP04')
        self.assertEqual(profile['human_necessary_skills'],'Not established')
    def test_duplicate_id_and_wrong_skill_name_rejected(self):
        with self.assertRaises(AssertionError):validate([row('1'),row('1')],TAX)
        bad=row('1');bad['skill_name']='Python'
        with self.assertRaises(AssertionError):validate([bad],TAX)
if __name__=='__main__':unittest.main()
