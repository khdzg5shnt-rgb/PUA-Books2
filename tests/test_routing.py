"""Behavioral checks against synthetic conversations; no private user cases."""
import json
import sys
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


if __name__=='__main__':unittest.main()
