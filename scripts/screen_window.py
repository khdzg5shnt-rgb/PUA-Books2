"""Locate the last sent bubble across annotated views of one conversation."""
from graphlib import CycleError, TopologicalSorter

from runtime_io import validate_fact_values


# These describe the particular bubble the reader is answering.
BUBBLE_FIELDS = {'function', 'closed_answer_complete', 'current_turn_low',
                'advice_requested', 'urgent_practical_need', 'roleplay_shared',
                'current_scope_relation'}


def read_bubble(item, config):
    if not isinstance(item, dict):
        raise ValueError('Each screen item must be an object')
    kind = item.get('kind', 'sent')
    if kind in ('draft', 'quote', 'notice'):
        if set(item) != {'kind'}:
            raise ValueError('A non-message marker takes only its kind')
        return None
    if kind != 'sent' or set(item) - {'kind', 'id', 'sender', 'facts'}:
        raise ValueError('Use a sent bubble or a draft, quote or notice marker')
    ident, sender = item.get('id'), item.get('sender')
    if type(ident) is not int or ident < 1 or sender not in ('user', 'other', 'unknown'):
        raise ValueError('A sent bubble needs a positive local ID and a sender')
    facts = item.get('facts', {})
    if not isinstance(facts, dict) or set(facts) - BUBBLE_FIELDS:
        raise ValueError('Only current-bubble observations belong on a sent bubble')
    validate_fact_values(facts, config)
    return ident, sender, facts


def _needs_answer(facts):
    return (facts.get('function') in {'question', 'advice_request'} or
            facts.get('advice_requested', False) or facts.get('urgent_practical_need', False))


def resolve_screens(screens, config, links, reply_to_id=None):
    """Use within-screen order and verified repeated bubble IDs, never upload order."""
    if not isinstance(screens, list) or not screens:
        raise ValueError('screens must contain one or more annotated views')
    order = TopologicalSorter()
    messages = {}
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
            ident, sender, facts = bubble
            senders, observed = messages.setdefault(ident, (set(), {}))
            if sender != 'unknown':
                senders.add(sender)
            if any(key in observed and observed[key] != val for key, val in facts.items()):
                raise ValueError('Recheck conflicting observations on the same bubble')
            observed.update(facts)
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
        if reply_to_id is not None:
            if reply_to_id in current_turn_ids:
                selected_id = reply_to_id
            elif reply_to_id in possible_turn_ids:
                gap = 'order'
            else:
                raise ValueError('reply_to_id cannot select an earlier conversation turn')
        elif _needs_answer(messages[last_id][1]):
            selected_id = last_id
        elif any(_needs_answer(messages[ident][1]) for ident in possible_turn_ids
                 if ident not in current_turn_ids):
            gap = 'order'
        elif any(_needs_answer(messages[ident][1]) for ident in current_turn_ids
                 if ident != last_id):
            gap = 'content'
        else:
            selected_id = last_id
    elif gap == 'none' and reply_to_id is not None:
        raise ValueError('reply_to_id requires a current other-sender turn')
    current = dict(messages[selected_id][1]) if selected_id is not None else {}
    current.update(latest_sender=sender, pending_reply=sender == 'user', turn_gap=gap)
    summary = {'distinct_sent': len(messages), 'last_id': last_id,
               'latest_sender': sender, 'turn_gap': gap,
               'current_turn_ids': current_turn_ids, 'reply_to_id': selected_id}
    return current, summary
