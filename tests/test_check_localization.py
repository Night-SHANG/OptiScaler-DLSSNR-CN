import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import check_localization
from loclib import sha

class CheckLocalizationTests(unittest.TestCase):
    def test_stale_translation_is_warning_not_structural_error(self):
        cat={'entries':{'k':{'source':'New text','source_hash':sha('New text'),'obsolete':False}}}
        en={'locale':'en-US','entries':{'k':{'text':'New text','source_hash':sha('New text')}}}
        zh={'locale':'zh-CN','entries':{'k':{'text':'旧翻译','state':'reviewed','source_hash':sha('Old text')}}}
        result=check_localization.analyze(cat,en,zh)
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['stats']['stale'],1)
        self.assertTrue(result['warnings'])

    def test_placeholder_mismatch_is_structural_error(self):
        cat={'entries':{'k':{'source':'Value %s','source_hash':sha('Value %s'),'obsolete':False}}}
        en={'locale':'en-US','entries':{'k':{'text':'Value %s','source_hash':sha('Value %s')}}}
        zh={'locale':'zh-CN','entries':{'k':{'text':'值','state':'reviewed','source_hash':sha('Value %s')}}}
        result=check_localization.analyze(cat,en,zh)
        self.assertTrue(any('printf placeholders differ' in e for e in result['errors']))

if __name__=='__main__': unittest.main()
