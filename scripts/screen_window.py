"""Locate the last sent bubble across annotated views of one conversation."""
from graphlib import CycleError, TopologicalSorter

from runtime_io import validate_fact_values


# These describe the particular bubble the reader is answering.
BUBBLE_FIELDS = {'function', 'closed_answer_complete', 'current_turn_low',
                'advice_requested', 'urgent_practical_need', 'roleplay_shared',
                'current_scope_relation'}

# A new arrangement update applies to the turn, even when an earlier question
# is the selected primary content. Other bubble observations remain separate.
STATE_FIELDS = {'invitation'}


def read_bubble(item, config):
    if not isinstance(item, dict):
        raise ValueError('Each screen item must be an object')
    kind = item.get('kind', 'sent')
    if kind in ('draft', 'quote', 'notice'):
        if set(item) != {'kind'}:
            raise ValueError('A non-message marker takes only its kind')
        return None
    if kind != 'sent' or set(item) - {'kind', 'id', 'sender', 'facts', 'resolves'}:
        raise ValueError('Use a sent bubble or a draft, quote or notice marker')
    ident, sender = item.get('id'), item.get('sender')
    if type(ident) is not int or ident < 1 or sender not in ('user', 'other', 'unknown'):
        raise ValueError('A sent bubble needs a positive local ID and a sender')
    facts = item.get('facts', {})
    if not isinstance(facts, dict) or set(facts) - (BUBBLE_FIELDS | STATE_FIELDS):
        raise ValueError('Use current-bubble observations or an explicit invitation update')
    validate_fact_values(facts, config)
    if facts.get('invitation') == 'none':
        raise ValueError('Omit invitation on ordinary content; an update needs a verified arrangement event')
    resolved = item.get('resolves')
    if 'resolves' in item and (
            sender != 'other' or not isinstance(resolved, list) or not resolved or
            any(type(target) is not int or target < 1 or target == ident for target in resolved) or
            len(resolved) != len(set(resolved))):
        raise ValueError('resolves needs distinct earlier request IDs on a verified other-sender bubble')
    return ident, sender, facts, resolved


def _needs_answer(facts):
    return (facts.get('function') in {'question', 'advice_request'} or
            facts.get('advice_requested', False) or facts.get('urgent_practical_need', False))


def _help_priority(facts):
    """Existing explicit help facts only; this is not a score of relationship interest."""
    if facts.get('urgent_practical_need', False):
        return 2
    return int(facts.get('advice_requested', False) or
               facts.get('function') == 'advice_request')


def _precedes(older, newer, predecessors):
    pending = list(predecessors[newer])
    seen = set()
    while pending:
        ident = pending.pop()
        if ident == older:
            return True
        if ident not in seen:
            seen.add(ident)
            pending.extend(predecessors[ident])
    return False


def _request_resolutions(messages, updates, predecessors, possible, current, ordered):
    """Apply only explicitly read later same-turn withdrawals/solutions."""
    resolved = {}
    for resolver in ordered:
        if resolver not in updates or resolver not in possible:
            continue
        for target in updates[resolver]:
            if (target not in messages or messages[target][0] != {'other'} or
                    not _needs_answer(messages[target][1])):
                raise ValueError('resolves must identify a marked request from the same selected conversation')
            if target not in possible:
                raise ValueError('resolves cannot reopen or change an earlier conversation turn')
            if target not in current or resolver not in current:
                return {}, 'turn'
            if not _precedes(target, resolver, predecessors):
                if _precedes(resolver, target, predecessors):
                    raise ValueError('A request resolution must follow its target request')
                return {}, 'order'
            resolved.setdefault(target, []).append(resolver)
    return resolved, None


def _plan_update(messages, ordered, predecessors, possible, current):
    """Resolve the last explicit current-turn plan state using proved order only."""
    updates = {ident for ident in possible if 'invitation' in messages[ident][1]}
    has_later_update = set()
    for ident in reversed(ordered):
        if ident in updates or ident in has_later_update:
            has_later_update.update(predecessors[ident])
    latest = updates - has_later_update
    if not latest:
        return None, None
    values = {messages[ident][1]['invitation'] for ident in latest}
    # An update may belong to an old turn if an outgoing barrier is unordered.
    # Differing unordered updates cannot be resolved by upload order or ID size.
    if not latest.issubset(current):
        return None, 'turn'
    if len(values) != 1:
        return None, 'order'
    return {'invitation': values.pop(),
            'bubble_ids': [ident for ident in ordered if ident in latest]}, None


def resolve_screens(screens, config, links, reply_to_id=None):
    """Use within-screen order and verified repeated bubble IDs, never upload order."""
    if not isinstance(screens, list) or not screens:
        raise ValueError('screens must contain one or more annotated views')
    order = TopologicalSorter()
    messages = {}
    request_updates = {}
    earlier = set()
    predecessors = {}
    for screen in screens:
        if not isinstance(screen, list):
            raise ValueError('Each screen must be a list in visible reading order')
        previous = None
        for item in screen:
            bubble = read_bubble(item, config)
            if bubble is None:
                continue
            ident, sender, facts, resolved = bubble
            senders, observed = messages.setdefault(ident, (set(), {}))
            if sender != 'unknown':
                senders.add(sender)
            if any(key in observed and observed[key] != val for key, val in facts.items()):
                raise ValueError('Recheck conflicting observations on the same bubble')
            observed.update(facts)
            if resolved is not None:
                targets = set(resolved)
                if ident in request_updates and request_updates[ident] != targets:
                    raise ValueError('Recheck conflicting request resolutions on the same bubble')
                request_updates[ident] = targets
            order.add(ident)
            predecessors.setdefault(ident, set())
            if previous is not None:
                order.add(ident, previous)
                predecessors[ident].add(previous)
                earlier.add(previous)
            previous = ident

    # A visible timestamp or another verified ordering cue may join disjoint views.
    if not isinstance(links, list):
        raise ValueError('screen_links must be a list of ordered bubble ID pairs')
    for pair in links:
        if (not isinstance(pair, list) or len(pair) != 2 or
                any(type(i) is not int or i not in messages for i in pair)):
            raise ValueError('Each screen link needs two IDs present in these screens')
        older, newer = pair
        order.add(newer, older)
        predecessors[newer].add(older)
        earlier.add(older)

    if reply_to_id is not None and (
            type(reply_to_id) is not int or reply_to_id not in messages or
            messages[reply_to_id][0] != {'other'}):
        raise ValueError('reply_to_id must identify a verified other-sender bubble')

    tails = set(messages) - earlier
    try:
        order.prepare()
    except CycleError:
        tails.clear()  # Inconsistent overlap cannot establish any reliable last bubble.
    ordered = []
    if tails:
        while order.is_active():
            ready = sorted(order.get_ready())
            ordered.extend(ready)
            order.done(*ready)
    last_id = next(iter(tails)) if len(tails) == 1 else None
    if any(len(senders) > 1 for ident, (senders, _) in messages.items() if ident != last_id):
        tails.clear()
        last_id = None
    directions = [messages[i][0] for i in tails]
    sender = 'unknown'
    if directions and len(directions[0]) == 1 and all(group == directions[0] for group in directions):
        sender = next(iter(directions[0]))
    if not messages:
        gap = 'missing'
    elif last_id is None:
        gap = 'order'
    elif sender == 'unknown':
        gap = 'sender'
    else:
        gap = 'none'
    current_turn_ids = []
    selected_id = None
    plan_update = None
    plan_gap = None
    resolved_requests = {}
    request_gap = None
    if gap == 'none' and sender == 'other':
        # A bubble belongs to the current other turn only when every visible
        # user/unknown barrier is proved to precede it. Prefix upload order is
        # never evidence of that relation.
        barriers = {ident: 1 << index for index, ident in enumerate(
            ident for ident in ordered if messages[ident][0] != {'other'})}
        all_barriers = (1 << len(barriers)) - 1
        seen_barriers = {}
        for ident in ordered:
            seen = barriers.get(ident, 0)
            for previous in predecessors[ident]:
                seen |= seen_barriers[previous]
            seen_barriers[ident] = seen
            if messages[ident][0] == {'other'} and seen == all_barriers:
                current_turn_ids.append(ident)

        # A possibly-current question with an unordered barrier must not be
        # silently discarded either. Mark whether a barrier is proved later.
        barrier_later = set()
        for ident in reversed(ordered):
            if ident in barriers or ident in barrier_later:
                barrier_later.update(predecessors[ident])
        possible_turn_ids = {ident for ident in ordered
                             if messages[ident][0] == {'other'} and ident not in barrier_later}
        resolved_requests, request_gap = _request_resolutions(
            messages, request_updates, predecessors, possible_turn_ids,
            set(current_turn_ids), ordered)

        def pending_request(ident):
            return _needs_answer(messages[ident][1]) and ident not in resolved_requests

        help_level = max((_help_priority(messages[ident][1]) for ident in current_turn_ids
                          if pending_request(ident)), default=0)
        primary_help = [ident for ident in current_turn_ids if pending_request(ident)
                        and _help_priority(messages[ident][1]) == help_level] if help_level else []
        if reply_to_id is not None:
            if reply_to_id in resolved_requests:
                raise ValueError('reply_to_id cannot select a request already resolved in this turn')
            if reply_to_id in current_turn_ids:
                if primary_help and reply_to_id not in primary_help:
                    gap = 'content'
                else:
                    selected_id = reply_to_id
            elif reply_to_id in possible_turn_ids:
                gap = 'order'
            else:
                raise ValueError('reply_to_id cannot select an earlier conversation turn')
        elif any(pending_request(ident) for ident in possible_turn_ids
                 if ident not in current_turn_ids):
            gap = 'order'
        elif pending_request(last_id):
            if primary_help and len(primary_help) == 1:
                selected_id = primary_help[0]
            elif primary_help and last_id not in primary_help:
                gap = 'content'
            else:
                selected_id = last_id
        elif any(pending_request(ident) for ident in current_turn_ids
                 if ident != last_id):
            gap = 'content'
        else:
            selected_id = last_id
        plan_update, plan_gap = _plan_update(
            messages, ordered, predecessors, possible_turn_ids,
            set(current_turn_ids))
        if plan_gap:
            gap = 'order'
            selected_id = None
        if request_gap:
            gap = 'order'
            selected_id = None
    elif gap == 'none' and reply_to_id is not None:
        raise ValueError('reply_to_id requires a current other-sender turn')
    current = ({key: value for key, value in messages[selected_id][1].items()
                if key in BUBBLE_FIELDS} if selected_id is not None else {})
    if plan_update is not None:
        current['invitation'] = plan_update['invitation']
    current.update(latest_sender=sender, pending_reply=sender == 'user', turn_gap=gap)
    summary = {'distinct_sent': len(messages), 'last_id': last_id,
               'latest_sender': sender, 'turn_gap': gap,
               'current_turn_ids': current_turn_ids, 'reply_to_id': selected_id}
    summary['current_turn_content'] = [
        {'id': ident, 'function': messages[ident][1].get('function', 'unknown'),
         'request_marked': _needs_answer(messages[ident][1]),
         **({'request_resolved': True} if ident in resolved_requests else {}),
         'selected_primary': ident == selected_id} for ident in current_turn_ids]
    if plan_update is not None:
        summary['plan_update'] = plan_update
    if plan_gap is not None:
        summary['plan_gap'] = plan_gap
    if resolved_requests:
        summary['request_resolutions'] = [
            {'request_id': ident, 'resolved_by_ids': resolved_requests[ident]}
            for ident in ordered if ident in resolved_requests]
    if request_gap is not None:
        summary['request_gap'] = request_gap
    return current, summary
