"""Invented metadata only: current questions and changing plans stay distinct."""
import copy
import json
import subprocess
import sys
import unittest
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from coach import build_brief

VERIFIED = {'speaker_verified': True, 'text_legible': True}


def bubble(ident, sender='other', **facts):
    return {'id': ident, 'sender': sender, 'facts': facts}


def brief(screens, **facts):
    return build_brief({'facts': VERIFIED | {'screens': screens} | facts})


class CurrentArrangements(unittest.TestCase):
    def test_later_cancellation_applies_while_an_earlier_question_is_answered(self):
        screens = [[bubble(1,'user'), bubble(2,function='question'),
                    bubble(3,function='logistics',invitation='cancelled_without_repair')]]
        request = {'facts': VERIFIED | {'screens': screens, 'reply_to_id': 2,
                                        'invitation': 'settled', 'goal': 'invite'}}
        original = copy.deepcopy(request)
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['screen_window']['last_id'], 3)
        self.assertEqual(result['screen_window']['reply_to_id'], 2)
        self.assertEqual(result['screen_window']['plan_update'],
                         {'invitation': 'cancelled_without_repair', 'bubble_ids': [3]})
        self.assertTrue(any('没有替代安排' in x for x in result['current_limits']))
        self.assertFalse(any('双方已确认这项安排' in x for x in result['current_limits']))
        self.assertIn('invitation', result['fact_adjustments'])
        self.assertEqual(request, original)

    def test_question_after_cancellation_does_not_restore_old_arrangement(self):
        result = brief([[bubble(7,invitation='cancelled_without_repair',function='logistics'),
                         bubble(4,function='question')]], invitation='settled')
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['screen_window']['plan_update']['bubble_ids'], [7])
        self.assertTrue(any('没有替代安排' in x for x in result['current_limits']))

    def test_changed_time_is_pending_until_it_is_reconfirmed(self):
        proposed = brief([[bubble(1,function='logistics',invitation='accepted')]],
                         invitation='settled')
        self.assertEqual(proposed['decision']['route_id'], 'R09')
        self.assertEqual(proposed['decision']['action'], 'draft')
        self.assertIn('before_drafting', proposed)
        confirmed = brief([[bubble(1,function='logistics',invitation='accepted'),
                            bubble(2,function='closing',invitation='settled')]],
                          invitation='settled')
        self.assertEqual(confirmed['decision']['route_id'], 'R09C')
        self.assertEqual(confirmed['output_contract']['max_candidates'], 0)

    def test_counterproposal_and_will_update_replace_old_state_without_new_inference(self):
        for invitation, expected in [('alternative','R08'), ('cancelled_with_repair','R08'),
                                     ('will_update','R10W')]:
            with self.subTest(invitation=invitation):
                result = brief([[bubble(1,function='logistics',invitation=invitation)]],
                               invitation='settled')
                self.assertEqual(result['decision']['route_id'], expected)
        result = brief([[bubble(1,function='question'),
                         bubble(2,function='logistics',invitation='will_update')]],
                       invitation='settled',reply_to_id=1)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertTrue(any('先把确认留给她' in x for x in result['current_limits']))

    def test_plan_update_does_not_merge_a_neighbor_role_or_question_function(self):
        result = brief([[bubble(1,function='question'),
                         bubble(2,function='banter',roleplay_shared=True,
                                current_scope_relation='different',invitation='alternative')]],
                       reply_to_id=1,reciprocity='mutual')
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['primary_method']['id'], 'M04')
        self.assertEqual(result['screen_window']['plan_update']['invitation'], 'alternative')
        self.assertEqual(len(result['read']), 2)

    def test_old_turn_update_does_not_overwrite_current_outer_state(self):
        result = brief([[bubble(1,invitation='cancelled_without_repair'),
                         bubble(2,'user'),bubble(3,function='question')]],invitation='settled')
        self.assertNotIn('plan_update',result['screen_window'])
        self.assertEqual(result['screen_window']['current_turn_ids'],[3])
        self.assertTrue(any('双方已确认这项安排' in x for x in result['current_limits']))

    def test_conflicting_unordered_updates_are_not_resolved_by_upload_order_or_focus(self):
        cancel = bubble(40,invitation='cancelled_without_repair')
        alternative = bubble(2,invitation='alternative')
        question = bubble(8,function='question')
        for views in permutations([[cancel,question],[alternative,question]]):
            for focus in [{},{'reply_to_id':8}]:
                result = brief(list(views),invitation='settled',**focus)
                self.assertEqual(result['decision']['route_id'],'R00T')
                self.assertEqual(result['screen_window']['turn_gap'],'order')
                self.assertNotIn('plan_update',result['screen_window'])
                self.assertIsNone(result['screen_window']['reply_to_id'])
                self.assertEqual(result['output_contract']['max_candidates'],0)
                self.assertEqual(result['clarification']['recipient'],'user')
                self.assertEqual(result['clarification']['field'],'invitation')
                self.assertIn('最后提出',result['clarification']['question'])

    def test_explicit_order_resolves_plan_updates_independently_of_numeric_ids(self):
        a = bubble(40,invitation='cancelled_without_repair')
        b = bubble(2,invitation='alternative')
        question = bubble(8,function='question')
        for views in permutations([[a,question],[b,question]]):
            result = brief(list(views),invitation='settled',screen_links=[[40,2]])
            self.assertEqual(result['decision']['route_id'],'R18')
            self.assertEqual(result['screen_window']['plan_update'],
                             {'invitation':'alternative','bubble_ids':[2]})

    def test_identical_unordered_updates_and_overlap_do_not_invent_a_conflict(self):
        a = bubble(40,invitation='cancelled_without_repair')
        b = bubble(2,invitation='cancelled_without_repair')
        question = bubble(8,function='question')
        result = brief([[a,question],[b,question],[a,question]],invitation='settled')
        self.assertEqual(result['decision']['route_id'],'R18')
        self.assertEqual(set(result['screen_window']['plan_update']['bubble_ids']),{40,2})
        self.assertEqual(result['screen_window']['distinct_sent'],3)

    def test_potential_old_turn_update_requires_order_until_the_barrier_is_resolved(self):
        update = bubble(4,invitation='cancelled_without_repair')
        question = bubble(2,function='question')
        views = [[update,question],[bubble(9,'user'),question]]
        for order in permutations(views):
            result = brief(list(order),invitation='settled')
            self.assertEqual(result['decision']['route_id'],'R00T')
            self.assertIn('最近一次回复之前还是之后',result['clarification']['question'])
            resolved = brief(list(order),invitation='settled',screen_links=[[9,4]])
            self.assertEqual(resolved['decision']['route_id'],'R18')
            self.assertEqual(resolved['screen_window']['plan_update']['bubble_ids'],[4])

    def test_cropped_tail_and_waiting_never_authorize_new_plan_confirmation(self):
        result = brief([[bubble(1,invitation='alternative',function='logistics')]],
                       turn_gap='missing',invitation='settled')
        self.assertEqual(result['decision']['route_id'],'R00T')
        self.assertNotIn('plan_update',result['screen_window'])
        self.assertEqual(result['screen_window']['current_turn_content'],[])
        result = brief([[bubble(1,invitation='alternative'),bubble(2,'user')]],
                       invitation='settled')
        self.assertEqual(result['decision']['route_id'],'R04')
        self.assertNotIn('turn_coverage',result)

    def test_specific_refusals_survive_and_contact_stop_wins_over_updates(self):
        views = [[bubble(1,function='logistics',invitation='accepted')]]
        result = brief(views,refusal_scope='activity',invitation='settled')
        self.assertEqual(result['decision']['route_id'],'R00S')
        result = brief(views,refusal_scope='contact')
        self.assertEqual(result['decision']['action'],'stop')
        self.assertEqual(result['output_contract']['max_candidates'],0)
        result = brief(views,refusal_scope='physical')
        self.assertEqual(result['decision']['route_id'],'R09')
        self.assertTrue(any('身体' in x for x in result['current_limits']))

    def test_multiple_requests_remain_visible_under_one_method_and_one_candidate(self):
        result = brief([[bubble(1,function='question'),
                         bubble(2,function='advice_request'),
                         bubble(3,function='sharing')]],reply_to_id=2)
        self.assertEqual(result['decision']['route_id'],'R16')
        self.assertEqual(result['turn_coverage'],{
            'primary_id':2,'context_ids':[1,3],'additional_request_ids':[1],
            'instruction':'主内容只决定一个方法；核同轮其余问题是否仍待答，必要时在同一条中简短照顾。'
                          '明确撤回或已解决的内容不重答，不拼接原话，不按气泡逐条补发。'})
        self.assertEqual(result['output_contract']['max_candidates'],1)
        self.assertEqual(result['output_contract']['max_lines'],2)
        self.assertEqual(result['output_contract']['max_questions'],1)

    def test_explicitly_chosen_closure_and_nonreply_tasks_do_not_force_answers(self):
        screens = [[bubble(1,function='question'),bubble(2,function='closing')]]
        result = brief(screens,reply_to_id=2)
        self.assertEqual(result['decision']['route_id'],'R13C')
        self.assertNotIn('turn_coverage',result)
        for task in ['meaning','analysis','review','training']:
            result = build_brief({'task':task,'facts':VERIFIED|{'screens':screens,'reply_to_id':1}})
            self.assertNotIn('turn_coverage',result)
            self.assertEqual(result['output_contract']['recipient'],'user')

    def test_ordinary_content_cannot_clear_an_invitation_by_setting_none(self):
        with self.assertRaises(ValueError):
            brief([[bubble(1,function='question',invitation='none')]],
                  invitation='no_alternative')
        result = brief([[bubble(1,function='question')]],invitation='no_alternative')
        self.assertEqual(result['decision']['route_id'],'R18')
        self.assertTrue(any('不换日期追问' in x for x in result['current_limits']))

    def test_only_the_selected_case_supplies_arrangement_updates(self):
        request = {'cases':{
            'not_selected':VERIFIED|{'screens':[[bubble(1,invitation='accepted')]]},
            'current':VERIFIED|{'screens':[[bubble(1,function='question')]],
                                'invitation':'no_alternative'}},'case_key':'current'}
        result = build_brief(request)
        self.assertNotIn('plan_update',result['screen_window'])
        self.assertTrue(any('没有替代安排' in x for x in result['current_limits']))
        self.assertNotIn('not_selected',json.dumps(result))

    def test_cli_errors_and_success_never_echo_raw_content_or_the_candidate(self):
        command = [sys.executable,str(ROOT/'scripts/coach.py'),'--request','-']
        screens = [[bubble(1,function='question',invitation='alternative')]]
        request = {'facts':VERIFIED|{'screens':screens},'candidate':'SYNTHETIC_PRIVATE_DRAFT'}
        run = subprocess.run(command,input=json.dumps(request),text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertNotIn('SYNTHETIC_PRIVATE_DRAFT',run.stdout+run.stderr)
        self.assertTrue(json.loads(run.stdout)['candidate_check']['ok'])
        for key,value in [('invitation','SYNTHETIC_PRIVATE_MARKER'),
                          ('invitation','none'),('raw_text','SYNTHETIC_PRIVATE_MARKER')]:
            request['facts']['screens'][0][0]['facts'] = {key:value}
            run = subprocess.run(command,input=json.dumps(request),text=True,capture_output=True)
            self.assertEqual(run.returncode,2)
            self.assertNotIn('SYNTHETIC_PRIVATE_MARKER',run.stdout+run.stderr)
            self.assertNotIn('Traceback',run.stderr)


if __name__ == '__main__':
    unittest.main()
