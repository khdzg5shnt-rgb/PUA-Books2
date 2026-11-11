#!/usr/bin/env python3
"""Find local method sections; retrieval order is not a psychological score."""
import argparse
import json
import re
from knowledge import ROOT, load_lookup, load_methods, markdown_sections, method_reference


def search(query, limit=8, root=ROOT, method=None):
    if not isinstance(query, str) or type(limit) is not int or limit < 0:
        raise ValueError('Use a text query and a nonnegative integer limit')
    methods, lookup = load_methods(root), load_lookup(root)
    explicit = re.findall(r'\bM\d{2}\b', query.upper())
    if method is None and len(set(explicit)) == 1:
        method = explicit[0]
    if method is not None and (not isinstance(method, str) or method not in methods):
        raise ValueError('Unknown method ID')
    # An explicit method selects the source collection, not a content keyword.
    content_query = re.sub(r'\bM\d{2}\b', ' ', query, flags=re.I)
    terms = [term.casefold() for term in re.split(r'\s+', content_query.strip()) if term]
    if not terms and method is None:
        return []
    selected = [method] if method else list(methods)
    paths = set()
    preferred = {}
    cited = {}
    for mid, card in methods.items():
        for source in card['sources']:
            cited.setdefault(source['path'], set()).add(mid)
    for mid in selected:
        item = method_reference(mid, root)
        key = (item['path'], item['heading'])
        preferred.setdefault(key, []).append(mid)
        if method:
            paths.update(source['path'] for source in methods[mid]['sources']
                         if source['path'].endswith('.md'))
    if not method:
        paths.update(str(path.relative_to(root)) for folder in
                     ['knowledge/books', 'knowledge/topics', 'knowledge/cases']
                     for path in (root / folder).rglob('*.md'))
    paths.update(path for path, _heading in preferred)
    hits = []
    for path in sorted(paths):
        for section in markdown_sections(path, root):
            body = section['text'].casefold()
            heading = section['heading'].casefold()
            mids = preferred.get((path, section['heading']), [])
            aliases = [alias.casefold() for mid in mids
                       for alias in lookup['methods'][mid]['aliases']
                       if alias.casefold() in query.casefold()]
            content_hits = sum(term in body for term in terms)
            query_matched = bool(content_hits or aliases)
            if not query_matched and not (method and mids):
                continue
            # Keep a preferred-section fallback, but let a matching cited section
            # answer a focused query before an unrelated generic paragraph.
            rank = (query_matched, max(map(len, aliases), default=0),
                    sum(term in heading for term in terms), content_hits,
                    bool(mids), path.startswith('knowledge/topics/'))
            lines = section['text'].splitlines()
            matching = [line for line in lines
                        if any(term in line.casefold() for term in terms)]
            snippet = (matching[0] if matching else '\n'.join(lines[1:]))[:240]
            kind = ('preferred_section' if mids else
                    'cited_source_section' if path in cited else 'related_note')
            hits.append((rank, section | {'snippet': snippet, 'method_ids': mids,
                'source_method_ids': sorted(cited.get(path, set())),
                'match_kind': kind, 'query_matched': query_matched}))
    hits.sort(key=lambda item: tuple(-int(x) for x in item[0]) +
              (item[1]['path'], item[1]['line']))
    return [{key: item[key] for key in
             ['path', 'title', 'heading', 'line', 'end_line', 'snippet', 'method_ids',
              'source_method_ids', 'match_kind', 'query_matched']}
            for _rank, item in hits[:min(limit, 20)]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--method', help='Read sources of one method, such as M14')
    parser.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    try:
        result = search(args.query, args.limit, method=args.method)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
