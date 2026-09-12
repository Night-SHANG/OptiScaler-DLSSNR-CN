import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import generate_cpp
from loclib import sha

class GenerateCppTests(unittest.TestCase):
    def test_utf8_is_emitted_as_ascii_byte_escapes(self):
        out = generate_cpp.c_bytes('中文')
        self.assertTrue(out.isascii())
        self.assertNotIn('中', out)
        self.assertIn('\\', out)

    def test_render_header_uses_only_fresh_approved_translation(self):
        catalog = {'entries': {
            'a': {'source':'Quality','source_hash':sha('Quality'),'obsolete':False},
            'b': {'source':'Changed','source_hash':sha('Changed'),'obsolete':False},
            'c': {'source':'Old','source_hash':sha('Old'),'obsolete':True},
        }}
        zh = {'entries': {
            'a': {'text':'质量','source_hash':sha('Quality'),'state':'reviewed'},
            'b': {'text':'已过期','source_hash':sha('Earlier'),'state':'reviewed'},
            'c': {'text':'旧','source_hash':sha('Old'),'state':'reviewed'},
        }}
        text = generate_cpp.render_header(catalog, zh)
        self.assertIn('Quality', text)
        self.assertIn('\\350\\264\\250', text) # beginning of UTF-8 for 质量
        self.assertIn('{"b", "Changed", ""}', text)
        self.assertNotIn('"Old"', text)
        self.assertTrue(text.isascii())

if __name__ == '__main__':
    unittest.main()
