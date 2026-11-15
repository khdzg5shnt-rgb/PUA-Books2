"""Reading continuity checks with tiny synthetic source records."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_os import validate_reading_cursor


class ReadingCursor(unittest.TestCase):
    def fixture(self, complete=False, partial=False):
        books = [{'id':'SYNTHETIC_A', 'path':'a.pdf', 'git_blob_sha':'a',
                  'reading_status':'provided_file_text_complete' if complete else
                                   'supplied_text_partial' if partial else 'unread'},
                 {'id':'SYNTHETIC_B', 'path':'b.epub', 'git_blob_sha':'b',
                  'reading_status':'provided_file_text_complete' if complete else 'unread'}]
        cursor = None if complete else copy.deepcopy(books[0])
        state = {'unfinished_file_queue':['SYNTHETIC_A'] if partial else [],
                 'reading_bookmark':copy.deepcopy(cursor),
                 'original_book_queue_complete':complete}
        if complete:
            state['last_completed_reading_unit'] = copy.deepcopy(books[-1])
        return books, {b['id']:b for b in books}, state, {'next_work_unit':cursor}

    def test_active_and_finished_queues_have_valid_distinct_states(self):
        for complete, partial in [(False,False),(False,True),(True,False)]:
            with self.subTest(complete=complete,partial=partial):
                self.assertEqual(validate_reading_cursor(*self.fixture(complete,partial)), [])

    def test_finished_queue_rejects_a_stale_cursor(self):
        books, originals, state, sources = self.fixture(True)
        sources['next_work_unit'] = state['reading_bookmark'] = dict(books[-1])
        self.assertIn('Completed original queue must not retain a next reading cursor',
                      validate_reading_cursor(books, originals, state, sources))

    def test_pending_queue_rejects_premature_completion_and_missing_cursor(self):
        books, originals, state, sources = self.fixture()
        sources['next_work_unit'] = state['reading_bookmark'] = None
        state['original_book_queue_complete'] = True
        errors = validate_reading_cursor(books, originals, state, sources)
        self.assertIn('Original queue cannot be complete while a book is pending', errors)
        self.assertIn('Active reading queue requires a cursor', errors)

    def test_cursor_cannot_skip_an_unread_or_partial_file(self):
        for partial in [False,True]:
            books, originals, state, sources = self.fixture(partial=partial)
            sources['next_work_unit'] = state['reading_bookmark'] = dict(books[1])
            error = ('Finish the current unfinished file before opening another book'
                     if partial else 'Next reading unit is not the first pending book')
            self.assertIn(error, validate_reading_cursor(books, originals, state, sources))

    def test_active_cursor_identity_and_bookmark_must_match(self):
        books, originals, state, sources = self.fixture()
        sources['next_work_unit']['git_blob_sha'] = 'changed'
        errors = validate_reading_cursor(books, originals, state, sources)
        self.assertIn('Runtime reading bookmark does not match source state', errors)
        self.assertIn('Next reading unit identity mismatch', errors)

    def test_finished_queue_requires_explicit_completion_and_last_identity(self):
        books, originals, state, sources = self.fixture(True)
        state.pop('original_book_queue_complete')
        state['last_completed_reading_unit']['git_blob_sha'] = 'changed'
        errors = validate_reading_cursor(books, originals, state, sources)
        self.assertIn('Completed original queue needs an explicit completion state', errors)
        self.assertIn('Completed queue needs a valid last completed reading unit', errors)

    def test_partial_file_cannot_disappear_from_unfinished_queue(self):
        books, originals, state, sources = self.fixture(partial=True)
        state['unfinished_file_queue'] = []
        self.assertIn('Unfinished-file queue does not match source records',
                      validate_reading_cursor(books, originals, state, sources))


if __name__ == '__main__':
    unittest.main()
