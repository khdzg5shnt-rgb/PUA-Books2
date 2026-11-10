"""Behavioral checks against synthetic conversations; no private user cases."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from route import select_route
from search_knowledge import search
from validate_os import validate


class RoutingScenarios(unittest.TestCase):
    def test_synthetic_dialogues(self):
        cases=json.loads((ROOT/'tests/synthetic_scenarios.json').read_text(encoding='utf-8'))
        for case in cases:
            with self.subTest(case=case['id'],context=case['context']):
                value=select_route(case['facts'])
                self.assertEqual(value['route_id'],case['expect_route'])
                self.assertEqual(value['action'],case['expect_action'])
                self.assertTrue(all((ROOT/p).is_file() for p in value['read']))

    def test_missing_identity_does_not_assume(self):
        self.assertEqual(select_route({})['action'],'clarify')

    def test_reject_unknown_facts(self):
        with self.assertRaises(ValueError):select_route({'likes_me':0.9})

    def test_type_and_range_validation(self):
        for facts in [{'speaker_verified':'yes'},{'consecutive_low_rounds':-1},
                      {'consecutive_low_rounds':True},{'refusal_scope':'fake_resistance'}]:
            with self.subTest(facts=facts):
                with self.assertRaises(ValueError):select_route(facts)

    def test_search_is_local_and_returns_usable_paths(self):
        hits=search('Callback 共同话题')
        self.assertTrue(hits)
        self.assertTrue(all((ROOT/hit['path']).is_file() for hit in hits))
        self.assertEqual(search('   '),[])

    def test_integrity_and_references(self):
        result=validate()
        self.assertTrue(result['ok'],result['errors'])
        # Original library and TOP30 are different populations, even when both
        # are checked during the same validation run.
        statistics=json.loads((ROOT/'system/sources.json').read_text())['statistics']
        self.assertEqual(result['book_text_complete'],statistics['current_book_files_text_complete'])

    def test_reading_claims_reject_wrong_breakpoint_and_reused_page(self):
        # A reading claim must fail if its recovery point or reused content differs.
        with tempfile.TemporaryDirectory(prefix='books2-reading-claims-') as folder:
            copied=Path(folder)/'repo'
            shutil.copytree(ROOT,copied,ignore=shutil.ignore_patterns('__pycache__','.git'))
            path=copied/'knowledge/provenance/core_reading_ledger.json'
            original=path.read_text(encoding='utf-8')
            ledger=json.loads(original)
            unit=next(u for u in ledger['units'] if u['id']=='E06')
            # Build a partial-reading fixture independently of the live book status.
            unit['reading_status']='supplied_text_partial'
            unit['read_ranges']=[[0,unit['characters']-1]]
            unit['next_character']=unit['characters']
            path.write_text(json.dumps(ledger,ensure_ascii=False),encoding='utf-8')
            self.assertIn('Partial source has no accurate next breakpoint: E06',validate(copied)['errors'])
            path.write_text(original,encoding='utf-8')
            path=copied/'knowledge/provenance/S22_top30_equivalence.json'
            proof=json.loads(path.read_text(encoding='utf-8'))
            proof['pages'][2]['pdf_normalized_sha256']='0'*64
            path.write_text(json.dumps(proof,ensure_ascii=False),encoding='utf-8')
            self.assertIn('Claimed reused pages do not match: S22',validate(copied)['errors'])


if __name__=='__main__':unittest.main()
