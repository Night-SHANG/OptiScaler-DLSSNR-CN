from pathlib import Path
import json, unittest

ROOT=Path(__file__).resolve().parents[1]

class ForkContractTests(unittest.TestCase):
    def test_upstream_identity(self):
        cfg=json.loads((ROOT/'upstream.json').read_text(encoding='utf-8'))
        self.assertEqual(cfg['repository'], 'https://github.com/Dagherbou/OptiScaler_DLSSNR.git')
        self.assertEqual(cfg['branch'], 'dlss-neural-rendering')
        self.assertEqual(cfg['package_prefix'], 'OptiScaler-DLSSNR-CN')

    def test_builds_dlssnr_forwarder_before_solution(self):
        for name in ('build.yml','release.yml'):
            text=(ROOT/'.github/workflows'/name).read_text(encoding='utf-8')
            self.assertIn(r'OptiScaler\dlssnr\forwarder\dlssnr_forwarder.vcxproj', text)
            self.assertIn(r'OptiScaler.sln', text)

    def test_package_wrapper_uses_fork_packager_and_never_mentions_proprietary_runtime_as_payload(self):
        text=(ROOT/'tools/package.ps1').read_text(encoding='utf-8')
        self.assertIn('package_release.ps1',text)
        self.assertIn('-SkipBuild',text)
        self.assertNotIn('Copy-Item nvngx_dlssnr.dll',text)

    def test_scanner_covers_dlssnr_sources(self):
        rules=json.loads((ROOT/'Localization/scanner-rules.json').read_text(encoding='utf-8'))
        self.assertIn('OptiScaler/dlssnr/**/*.cpp',rules['include_globs'])
        self.assertIn('OptiScaler/dlssnr/**/*.cpp',rules['c_string_array_globs'])

if __name__=='__main__': unittest.main()
