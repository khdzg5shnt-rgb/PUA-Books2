"""Synthetic current-status pages must not silently drift from source counts."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_os import validate_reading_displays


class CurrentStatusDocuments(unittest.TestCase):
    def fixture(self, root):
        current = ('<!-- CURRENT_READING_STATUS -->\n当前完成70/119份任务，阅读暂停。\n'
                   '<!-- END_CURRENT_READING_STATUS -->\n')
        for path in ['README.md','KNOWLEDGE_INDEX.md']:
            (root/path).write_text(current+'\n历史记录：完成61/119，不作为当前断点。\n')
        (root/'CURRENT_STATE.md').write_text('## 完成进度：70/119（阅读暂停）\n')

    def test_current_status_matches_counts_while_explicit_history_remains(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            self.assertEqual(validate_reading_displays(root,70,119),[])
            errors=validate_reading_displays(root,71,119)
            self.assertEqual(len(errors),3)
            for name in ['README.md','KNOWLEDGE_INDEX.md','CURRENT_STATE.md']:
                self.assertTrue(any(name in e for e in errors))

    def test_a_second_stale_current_line_and_missing_marker_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            with (root/'KNOWLEDGE_INDEX.md').open('a') as handle:
                handle.write('当前完成61/119份任务，下一份还没读。\n')
            self.assertIn('Unmarked current reading display may be stale: KNOWLEDGE_INDEX.md',
                          validate_reading_displays(root,70,119))
            (root/'README.md').write_text('当前完成70/119份任务。\n')
            self.assertIn('Expected one current reading status block: README.md',
                          validate_reading_displays(root,70,119))

    def test_duplicate_current_blocks_and_a_stale_resume_heading_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            p=root/'README.md';p.write_text(p.read_text()+p.read_text())
            (root/'CURRENT_STATE.md').write_text('## 完成进度：61/119\n')
            errors=validate_reading_displays(root,70,119)
            self.assertIn('Expected one current reading status block: README.md',errors)
            self.assertIn('Current reading display does not match source state: CURRENT_STATE.md',errors)


if __name__=='__main__':
    unittest.main()
