from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / '.github' / 'workflows'


class RepositoryContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding='utf-8')

    def test_required_repository_files_exist(self):
        for relative in [
            'README.md', 'README.zh-CN.md', 'LICENSE', 'UPSTREAM.md',
            'TRANSLATION.md', 'CONTRIBUTING.md', 'upstream.json',
            'Localization/master/en-US.json', 'Localization/stable/en-US.json', 'Localization/zh-CN.json',
            'Localization/glossary.json', 'Localization/scanner-rules.json',
            '.github/workflows/upstream-sync.yml', '.github/workflows/build.yml',
            '.github/workflows/release.yml', '.github/workflows/localization-check.yml',
        ]:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_localization_check_requires_translation_memory_consistency(self):
        text = self.read('.github/workflows/localization-check.yml')
        self.assertIn('python tools/update_translation_memory.py --check', text)

    def test_upstream_sync_is_daily_and_manual(self):
        text = self.read('.github/workflows/upstream-sync.yml')
        self.assertIn('schedule:', text)
        self.assertIn('cron:', text)
        self.assertIn('workflow_dispatch:', text)
        self.assertIn('actions: write', text)

    def test_build_uses_upstream_release_solution_and_always_uploads_diagnostics(self):
        text = self.read('.github/workflows/build.yml')
        self.assertIn(r'msbuild _upstream\OptiScaler.sln', text)
        self.assertIn('if: always()', text)
        self.assertIn('build-diagnostics', text)

    def test_optional_machine_translation_failure_does_not_block_sync_or_release(self):
        for relative in ['.github/workflows/upstream-sync.yml', '.github/workflows/release.yml']:
            text=self.read(relative)
            with self.subTest(relative=relative):
                marker='- name: Optional incremental machine translation'
                start=text.index(marker)
                block=text[start:start+900]
                self.assertIn('continue-on-error: true',block)

    def test_release_records_stable_only_after_publish_step(self):
        text = self.read('.github/workflows/release.yml')
        publish = text.index('Publish or refresh GitHub Release')
        record = text.index('Record successfully published stable tag')
        self.assertLess(publish, record)

    def test_workflows_never_embed_translation_api_secret_values(self):
        for path in WF.glob('*.yml'):
            text = path.read_text(encoding='utf-8')
            with self.subTest(path=path.name):
                self.assertNotRegex(text, r'(?i)sk-[A-Za-z0-9_-]{16,}')
                self.assertNotRegex(text, r'(?i)TRANSLATION_API_KEY\s*:\s*["\']?[A-Za-z0-9_-]{20,}')


if __name__ == '__main__':
    unittest.main()

class DualLocalizationRepositoryContractTests(unittest.TestCase):
    def test_master_and_stable_catalog_directories_exist(self):
        for channel in ('master','stable'):
            for name in ('catalog.json','en-US.json','pending.json'):
                self.assertTrue((ROOT/'Localization'/channel/name).is_file(), f'{channel}/{name}')

    def test_sync_scans_and_persists_both_channels(self):
        text=(ROOT/'.github/workflows/upstream-sync.yml').read_text(encoding='utf-8')
        self.assertIn('--channel master',text)
        self.assertIn('--channel stable',text)
        self.assertIn('Materialize official stable for scan',text)

    def test_sync_bootstraps_empty_dual_channel_catalogs_without_upstream_change(self):
        text=(ROOT/'.github/workflows/upstream-sync.yml').read_text(encoding='utf-8')
        self.assertIn('Detect localization catalog bootstrap', text)
        self.assertIn('id: catalog_state', text)
        self.assertIn('steps.catalog_state.outputs.bootstrap_needed', text)

    def test_sync_runs_on_dual_channel_bootstrap_push(self):
        text=(ROOT/'.github/workflows/upstream-sync.yml').read_text(encoding='utf-8')
        self.assertIn('push:', text)
        self.assertIn('Localization/stable/**', text)
        self.assertIn('.github/workflows/upstream-sync.yml', text)

    def test_sync_refreshes_stable_release_when_shared_translation_changes(self):
        text=(ROOT/'.github/workflows/upstream-sync.yml').read_text(encoding='utf-8')
        self.assertIn('translation_changed=true', text)
        self.assertIn("steps.persist.outputs.translation_changed == 'true'", text)
        self.assertIn('Dispatch stable release build when needed', text)

    def test_build_and_release_use_matching_channel(self):
        build=(ROOT/'.github/workflows/build.yml').read_text(encoding='utf-8')
        release=(ROOT/'.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn('--channel master',build)
        self.assertIn('--channel stable',release)

class ReleaseRefreshContractTests(unittest.TestCase):
    def test_release_refreshes_when_shared_chinese_changes(self):
        text=(ROOT/'.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn('push:',text)
        self.assertIn('Localization/zh-CN.json',text)
