#!/usr/bin/env python3
"""Search the local curated knowledge, returning paths/snippets, not psychological scores."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def search(query, limit=8, root=ROOT):
    terms = [term.casefold() for term in re.split(r'\s+', query.strip()) if term]
    if not terms:
        return []
    candidates = [root / 'START_HERE.md', root / 'PUA_CORE_SYSTEM.md']
    candidates += [root / 'system' / name for name in
                   ['METHOD_CARDS.md', 'SCENARIO_ROUTER.md', 'REPLY_PROTOCOL.md']]
    candidates += list((root / 'knowledge/books').rglob('*.md'))
    candidates += list((root / 'knowledge/topics').glob('*.md'))
    candidates += list((root / 'knowledge/cases').glob('*.md'))
    hits = []
    for path in sorted(set(candidates)):
        content = path.read_text(encoding='utf-8')
        lines = content.splitlines()
        found = [(index, line) for index, line in enumerate(lines, 1)
                 if any(term in line.casefold() for term in terms)]
        if found:
            matched = sum(term in content.casefold() for term in terms)
            first = found[0]
            hits.append((matched, len(found), str(path.relative_to(root)), first[0], first[1]))
    hits.sort(key=lambda x: (-x[0], -x[1], x[2]))
    return [{'path':path, 'line':line, 'snippet':snippet[:240]}
            for _, _, path, line, snippet in hits[:max(0, limit)]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    parser.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    print(json.dumps(search(args.query, args.limit), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
