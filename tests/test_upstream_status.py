import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import upstream_status

class UpstreamStatusTests(unittest.TestCase):
    def test_select_latest_stable_ignores_draft_and_prerelease(self):
        releases=[
            {'tag_name':'v10-beta','draft':False,'prerelease':True},
            {'tag_name':'v0.9.5-draft','draft':True,'prerelease':False},
            {'tag_name':'v0.9.4','draft':False,'prerelease':False},
        ]
        self.assertEqual(upstream_status.select_latest_stable(releases),'v0.9.4')

    def test_compute_status_detects_branch_and_stable_release_changes(self):
        cfg={'last_scanned_commit':'aaa','last_released_upstream_tag':'v0.9.3'}
        s=upstream_status.compute_status(cfg,'bbb','v0.9.4')
        self.assertTrue(s['branch_changed'])
        self.assertTrue(s['stable_release_changed'])
        self.assertEqual(s['stable_tag'],'v0.9.4')

    def test_recording_release_updates_current_stable_and_release_marker(self):
        cfg={'stable_release':'v0.9.3','last_released_upstream_tag':'v0.9.3'}
        out=upstream_status.update_tracking(cfg,released='v0.9.4')
        self.assertEqual(out['stable_release'],'v0.9.4')
        self.assertEqual(out['last_released_upstream_tag'],'v0.9.4')

    def test_no_change_is_reported(self):
        cfg={'last_scanned_commit':'bbb','last_released_upstream_tag':'v0.9.4'}
        s=upstream_status.compute_status(cfg,'bbb','v0.9.4')
        self.assertFalse(s['branch_changed'])
        self.assertFalse(s['stable_release_changed'])

if __name__=='__main__': unittest.main()
