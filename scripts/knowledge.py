"""Resolve curated method references to actual Markdown sections, locally."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r'^(#{1,6})\s+(.+?)\s*#*\s*$')


def load_methods(root=ROOT):
    data = json.loads((root / 'system/methods.json').read_text(encoding='utf-8'))
    return {item['id']: item for item in data['methods']}


def load_lookup(root=ROOT):
    return json.loads((root / 'system/knowledge_map.json').read_text(encoding='utf-8'))


def local_path(path, root=ROOT):
    base = root.resolve()
    candidate = (base / path).resolve()
    if not candidate.is_relative_to(base) or not candidate.is_file():
        raise ValueError('Reference must be an existing file inside books2')
    return candidate


def markdown_sections(path, root=ROOT):
    """Return leaf text blocks with 1-based inclusive line ranges."""
    lines = local_path(path, root).read_text(encoding='utf-8').splitlines()
    headings = [(index, match.group(2)) for index, line in enumerate(lines)
                if (match := HEADING.match(line))]
    title = headings[0][1] if headings else Path(path).stem
    if not headings:
        headings = [(0, title)]
    result = []
    for position, (start, heading) in enumerate(headings):
        stop = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        content = '\n'.join(lines[start:stop]).strip()
        result.append({'path': str(path), 'title': title, 'heading': heading,
                       'line': start + 1, 'end_line': stop, 'text': content})
    return result


def resolve_reference(reference, root=ROOT, excerpt_limit=1600):
    sections = markdown_sections(reference['path'], root)
    found = [item for item in sections if item['heading'] == reference['heading']]
    if len(found) != 1:
        raise ValueError('Preferred reference heading is missing or ambiguous: ' +
                         reference['path'])
    item = found[0]
    content = item.pop('text')
    return item | {'excerpt': content[:excerpt_limit],
                   'excerpt_complete': len(content) <= excerpt_limit}


def method_reference(method_id, root=ROOT):
    methods = load_methods(root)
    lookup = load_lookup(root)
    if method_id not in methods or method_id not in lookup['methods']:
        raise ValueError('Unknown method ID')
    reference = lookup['methods'][method_id]['preferred']
    if reference['path'] not in {s['path'] for s in methods[method_id]['sources']}:
        raise ValueError('Preferred reference is not a cited method source')
    return resolve_reference(reference, root)
