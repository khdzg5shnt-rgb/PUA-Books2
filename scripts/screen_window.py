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


def resolve_screens(screens, config, links):
    """Use within-screen order and verified repeated bubble IDs, never upload order."""
    if not isinstance(screens, list) or not screens:
        raise ValueError('screens must contain one or more annotated views')
    order = TopologicalSorter()
    messages = {}
    earlier = set()
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
            if previous is not None:
                order.add(ident, previous)
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
        earlier.add(older)

    tails = set(messages) - earlier
    try:
        order.prepare()
    except CycleError:
        tails.clear()  # Inconsistent overlap cannot establish any reliable last bubble.
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
    current = dict(messages[last_id][1]) if gap == 'none' else {}
    current.update(latest_sender=sender, pending_reply=sender == 'user', turn_gap=gap)
    summary = {'distinct_sent': len(messages), 'last_id': last_id,
               'latest_sender': sender, 'turn_gap': gap}
    return current, summary
