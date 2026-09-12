import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import release_notes
from loclib import sha

class ReleaseNotesTests(unittest.TestCase):
    def test_release_tag_is_safe_and_stable(self):
        self.assertEqual(release_notes.release_tag_name('v0.9.4','abcdef123456'),'cn-v0.9.4-abcdef12')
        self.assertEqual(release_notes.release_tag_name('refs/heads/master','ABCDEF123456'),'cn-refs-heads-master-abcdef12')

    def test_translation_stats_count_only_fresh_usable_entries(self):
        cat={'entries':{
          'a':{'source':'A','source_hash':sha('A'),'obsolete':False},
          'b':{'source':'B','source_hash':sha('B'),'obsolete':False},
          'old':{'source':'Old','source_hash':sha('Old'),'obsolete':True},
        }}
        zh={'entries':{
          'a':{'text':'甲','source_hash':sha('A'),'state':'reviewed'},
          'b':{'text':'乙','source_hash':sha('before'),'state':'machine_translated'},
        }}
        stats=release_notes.translation_stats(cat,zh)
        self.assertEqual(stats,{'total':2,'effective':1,'reviewed':1,'machine':0,'missing':0,'stale':1,'coverage':50.0})

    def test_change_stats_report_current_scan_and_newly_effective_translations(self):
        cat={'entries':{
          'new':{'source':'New','source_hash':sha('New'),'obsolete':False},
          'changed':{'source':'Changed','source_hash':sha('Changed'),'obsolete':False},
        }}
        zh={'entries':{
          'new':{'text':'新增','source_hash':sha('New'),'state':'machine_translated'},
          'changed':{'text':'旧译','source_hash':sha('Old'),'state':'reviewed'},
        }}
        pending={'scan':{'added':['new'],'changed':['changed'],'removed':['gone']}}
        self.assertEqual(release_notes.change_stats(pending,cat,zh),{
            'added':1,'changed':1,'removed':1,'newly_effective':1
        })

    def test_release_notes_include_this_scan_translation_count(self):
        cat={'entries':{'new':{'source':'New','source_hash':sha('New'),'obsolete':False}}}
        zh={'entries':{'new':{'text':'新增','source_hash':sha('New'),'state':'machine_translated'}}}
        pending={'scan':{'added':['new'],'changed':[],'removed':[]}}
        notes=release_notes.render_notes('v1','abc12345',cat,zh,pending)
        self.assertIn('本次新增/更新有效中文：1',notes)
        self.assertIn('本次扫描新增 UI：1',notes)
        self.assertIn('未覆盖或待复核的项目会显示官方英文', notes)
        self.assertNotIn('未覆盖或待复核的项目会显示官方中文', notes)

if __name__=='__main__': unittest.main()
