import json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import localize_source
from loclib import key_for_source

RULES=json.loads((ROOT/'Localization/scanner-rules.json').read_text(encoding='utf-8'))

CURRENT_MENU='''#include "pch.h"\n#include "menu_common.h"\n\nvoid MenuCommon::Init(HWND InHwnd, bool isUWP)\n{\n    ImGuiIO& io = ImGui::GetIO();\n    if (io.Fonts->Fonts.empty() && Config::Instance()->UseHQFont.value_or_default())\n    {\n        ImFontAtlas* atlas = io.Fonts;\n        atlas->Clear();\n        ImFontConfig fontConfig;\n        if (Config::Instance()->FontSize.has_value())\n            fontSize = Config::Instance()->FontSize.value();\n        if (Config::Instance()->TTFFontPath.has_value())\n        {\n            io.FontDefault =\n                atlas->AddFontFromFileTTF(wstring_to_string(Config::Instance()->TTFFontPath.value()).c_str(), fontSize,\n                                          &fontConfig, io.Fonts->GetGlyphRangesDefault());\n        }\n        else\n        {\n            io.FontDefault = atlas->AddFontFromMemoryCompressedBase85TTF(hack_compressed_compressed_data_base85,\n                                                                         fontSize, &fontConfig);\n        }\n    }\n}\n'''

class LocalizeSourceTests(unittest.TestCase):
    def test_dlssnr_diagnostic_translation_is_ui_only_and_idempotent(self):
        text = 'const char* reason = DlssNr::FailureReason();\nconst char* why = DlssNr::ExposureScan::Status();\n'
        td,p=self.temp_file(text)
        try:
            localize_source.patch_dlssnr_diagnostics(p)
            once=p.read_text()
            self.assertIn('OptiScalerCN::Loc::TL(DlssNr::FailureReason())', once)
            self.assertIn('reasonText.c_str()', once)
            self.assertIn('whyText.c_str()', once)
            localize_source.patch_dlssnr_diagnostics(p)
            self.assertEqual(p.read_text(), once)
        finally: td.cleanup()

    def test_keybind_display_keeps_internal_name_and_widget_id(self):
        text = 'Keybind(std::string name, int id) : name(name), id(id) {}\nImGui::Button(name.c_str());\n'
        td,p=self.temp_file(text)
        try:
            localize_source.patch_dynamic_helpers(p)
            once=p.read_text()
            self.assertIn('name(name), id(id)', once)
            self.assertIn('OptiScalerCN::Loc::TL(name) + "###" + name', once)
            localize_source.patch_dynamic_helpers(p)
            self.assertEqual(p.read_text(), once)
        finally: td.cleanup()

    def test_dlssnr_diagnostic_anchor_change_fails_closed(self):
        td,p=self.temp_file('const char* reason = ChangedApi();')
        try:
            with self.assertRaisesRegex(RuntimeError, 'diagnostic anchor changed'):
                localize_source.patch_dlssnr_diagnostics(p)
        finally: td.cleanup()

    def test_tooltip_dynamic_translation_after_literal_instrumentation(self):
        text = 'ImGui::SetTooltip("%s", opt.tooltip.c_str());\nImGui::SetTooltip("%s", flag.description.c_str());\n'
        td,p=self.temp_file(text)
        try:
            localize_source.instrument_file(p,'OptiScaler/menu/menu_common.cpp',RULES,{'%s':key_for_source('%s')})
            localize_source.patch_dynamic_helpers(p)
            once=p.read_text()
            self.assertIn('OptiScalerCN::Loc::TL(opt.tooltip).c_str()', once)
            self.assertIn('OptiScalerCN::Loc::TL(flag.description).c_str()', once)
            localize_source.patch_dynamic_helpers(p)
            self.assertEqual(p.read_text(), once)
        finally: td.cleanup()

    def test_common_composed_display_formats_keep_range_lifetime_and_ids(self):
        text = ('auto joined = upscalers | std::views::join_with(std::string { " or " });\n'
                'ImGui::SliderFloat("Size##mag", &size, 5.0f, 50.0f, "%.1f%% of screen");\n'
                'ImGui::SliderFloat("Border Size", &border, 0.0f, 2.0f, "%.2f%% of screen");\n'
                'Keybind("Toggle overlay", VK_HOME); upscalers.push_back("DLSS");\n'
                'ImGui::SliderFloat("DLAA", &v, 0, 1, "%.3f");\n')
        sources = [' or ', 'Size##mag', 'Border Size', '%.1f%% of screen', '%.2f%% of screen']
        td,p=self.temp_file(text)
        try:
            localize_source.instrument_file(p,'OptiScaler/menu/menu_common.cpp',RULES,
                                            {x:key_for_source(x) for x in sources})
            out=p.read_text()
            for source in sources:
                self.assertIn(f'OptiScalerCN::Loc::T("{key_for_source(source)}", "{source}")', out)
            self.assertIn('std::views::join_with(std::string { OptiScalerCN::Loc::T(', out)
            self.assertIn('Keybind("Toggle overlay", VK_HOME)', out)
            self.assertIn('upscalers.push_back("DLSS")', out)
            self.assertIn('ImGui::SliderFloat("DLAA", &v, 0, 1, "%.3f")', out)
        finally: td.cleanup()

    def temp_file(self,text):
        td=tempfile.TemporaryDirectory(); p=Path(td.name)/'menu_common.cpp'; p.write_text(text,encoding='utf-8'); return td,p

    def test_current_master_font_block_is_patched_and_idempotent(self):
        td,p=self.temp_file(CURRENT_MENU)
        try:
            localize_source.patch_font_and_init(p)
            once=p.read_text(encoding='utf-8')
            self.assertIn('#include "localization/Localization.h"',once)
            self.assertEqual(once.count('OptiScalerCN::Loc::Initialize();'),1)
            self.assertIn('OptiScalerCN::Loc::IsChineseRequested()',once)
            self.assertIn('OptiScalerCN::Loc::ResolveChineseFont',once)
            self.assertIn('OptiScalerCN::Loc::BuildGlyphRanges(atlas)',once)
            localize_source.patch_font_and_init(p)
            self.assertEqual(p.read_text(encoding='utf-8'),once)
        finally: td.cleanup()

    def test_font_patch_fails_closed_if_upstream_semantic_block_disappears(self):
        broken=CURRENT_MENU.replace('AddFontFromFileTTF','SomeNewFontLoader')
        td,p=self.temp_file(broken)
        try:
            with self.assertRaisesRegex(RuntimeError,'font-loading block changed'):
                localize_source.patch_font_and_init(p)
        finally: td.cleanup()

    def test_dynamic_strfmt_literal_is_instrumented(self):
        text='#include "pch.h"\nvoid f(){ auto x=StrFmt("Disable##%d", 4); }\n'
        td,p=self.temp_file(text)
        try:
            key=key_for_source('Disable##%d')
            count=localize_source.instrument_file(p,'OptiScaler/menu/menu_common.cpp',RULES,{'Disable##%d':key})
            out=p.read_text(encoding='utf-8')
            self.assertEqual(count,1)
            self.assertIn(f'OptiScalerCN::Loc::T("{key}", "Disable##%d")',out)
        finally: td.cleanup()

    def test_dynamic_menu_option_sites_use_source_lookup(self):
        text='''preview = opt.label;\nImGui::Selectable(opt.label.c_str(), isSelected);\nImGui::SetTooltip("%s", opt.tooltip.c_str());\nreturn it->label;\nImGui::Text("%s", splashMessage.c_str());\n'''
        td,p=self.temp_file(text)
        try:
            localize_source.patch_dynamic_helpers(p)
            out=p.read_text(encoding='utf-8')
            self.assertIn('preview = OptiScalerCN::Loc::TL(opt.label);',out)
            self.assertIn('TL(opt.tooltip)',out)
            self.assertIn('TL(splashMessage)',out)
        finally: td.cleanup()



    def test_nested_std_format_uses_runtime_format_helper(self):
        text='#include "pch.h"\nvoid f(){ ImGui::TextColored(color, std::format("ON {}x", count + 1).c_str()); }\n'
        td,p=self.temp_file(text)
        try:
            key=key_for_source('ON {}x')
            count=localize_source.instrument_file(p,'OptiScaler/menu/menu_common.cpp',RULES,{'ON {}x':key})
            out=p.read_text(encoding='utf-8')
            self.assertEqual(count,1)
            self.assertIn(f'OptiScalerCN::Loc::F("{key}", "ON {{}}x", count + 1).c_str()',out)
            self.assertNotIn('std::format("ON {}x"',out)
        finally: td.cleanup()


    def test_runtime_header_has_vformat_helper_for_localized_format_strings(self):
        header=(ROOT/'overlay'/'OptiScaler'/'localization'/'Localization.h').read_text(encoding='utf-8')
        self.assertIn('std::string F(std::string_view key, const char* englishFallback',header)
        self.assertIn('std::vformat(T(key, englishFallback)',header)

    def test_flag_definition_sites_use_source_lookup(self):
        text='''ImGui::CheckboxFlags(flag.name.c_str(), &temp_flags, flag.mask);
ImGui::SetTooltip("%s", flag.description.c_str());
'''
        td,p=self.temp_file(text)
        try:
            localize_source.patch_dynamic_helpers(p)
            out=p.read_text(encoding='utf-8')
            self.assertIn('TL(flag.name)',out)
            self.assertIn('TL(flag.description)',out)
        finally: td.cleanup()


    def test_localization_header_is_added_to_precompiled_header(self):
        td=tempfile.TemporaryDirectory(); p=Path(td.name)/'pch.h'
        try:
            p.write_text('#pragma once\n#include <Windows.h>\ninline int marker = 1;\n',encoding='utf-8')
            localize_source.patch_precompiled_header(p)
            out=p.read_text(encoding='utf-8')
            self.assertIn('#include "localization/Localization.h"',out)
            self.assertGreater(out.index('#include "localization/Localization.h"'), out.index('inline int marker = 1;'))
            localize_source.patch_precompiled_header(p)
            self.assertEqual(p.read_text(encoding='utf-8').count('#include "localization/Localization.h"'),1)
        finally:
            td.cleanup()

    def test_cp1252_source_file_is_instrumented_without_reencoding_failure(self):
        td=tempfile.TemporaryDirectory(); p=Path(td.name)/'legacy.cpp'
        try:
            raw=b'#include "pch.h"\n// legacy dash: \x97\nvoid f(){ auto x=StrFmt("Disable##%d", 4); }\n'
            p.write_bytes(raw)
            key=key_for_source('Disable##%d')
            count=localize_source.instrument_file(p,'OptiScaler/menu/legacy.cpp',RULES,{'Disable##%d':key})
            self.assertEqual(count,1)
            out=p.read_bytes()
            self.assertIn(b'\x97',out)
            self.assertIn(f'OptiScalerCN::Loc::T("{key}", "Disable##%d")'.encode('ascii'),out)
        finally:
            td.cleanup()

if __name__=='__main__': unittest.main()
