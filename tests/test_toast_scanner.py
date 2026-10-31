import json,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from loclib import find_candidates,key_for_source
from localize_source import instrument_file
RULES=json.loads((ROOT/'Localization/scanner-rules.json').read_text())
class ToastScannerTests(unittest.TestCase):
    def test_inline_and_named_toast_content_only(self):
        text='ImGui::InsertNotification({ ImGuiToastType::Error, 10000, "Shader " "failed!" }); ImGuiToast note({ ImGuiToastType::Warning, 2000, "Warning!" }); ImGuiToast direct { ImGuiToastType::Info, 2000, "Hello" }; LOG_ERROR("not UI");'
        got=find_candidates(text,'OptiScaler/shaders/Test.cpp',RULES)
        self.assertEqual([c.source for c in got],['Shader failed!','Warning!','Hello'])
    def test_nested_format_rewrites_runtime_format_call_not_literal(self):
        text='ImGui::InsertNotification({ ImGuiToastType::Warning, 20000, std::format("{} is unavailable", name).c_str() });'
        got=find_candidates(text,'OptiScaler/hooks/Test.cpp',RULES)
        self.assertEqual([(c.source,c.callee) for c in got],[('{} is unavailable','nested:std::format')])
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.cpp';p.write_text(text)
            instrument_file(p,'OptiScaler/hooks/Test.cpp',RULES,{'{} is unavailable':key_for_source('{} is unavailable')})
            out=p.read_text()
            self.assertIn('OptiScalerCN::Loc::F(',out)
            self.assertNotIn('std::format(OptiScalerCN',out)
    def test_no_content_or_variable_is_not_invented(self):
        text='ImGuiToast note { ImGuiToastType::Warning, 1000 }; ImGui::InsertNotification(note); ImGui::InsertNotification({ ImGuiToastType::Warning, 1000, toastMsg.c_str() });'
        self.assertEqual(find_candidates(text,'OptiScaler/hooks/Test.cpp',RULES),[])
