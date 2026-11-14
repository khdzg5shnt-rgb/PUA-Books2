"""Resolve curated method references to actual Markdown sections, locally."""
import json
import re
from collections import Counter
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


def citation_headings(reference, sections):
    """Resolve only exact headings; a page locator does not bind an entire file."""
    counts = Counter(item['heading'] for item in sections)
    if 'section_headings' in reference:
        headings = reference['section_headings']
        if (not isinstance(headings, list) or not headings or
                any(not isinstance(item, str) or not item.strip() for item in headings) or
                len(headings) != len(set(headings)) or
                any(counts[item] != 1 for item in headings)):
            raise ValueError('Source section bindings must identify unique existing headings')
        return list(headings)
    locator = reference.get('locator')
    return [locator] if isinstance(locator, str) and counts[locator] == 1 else []


def _resolve_from_sections(reference, sections, excerpt_limit=1600):
    found = [item for item in sections if item['heading'] == reference['heading']]
    if len(found) != 1:
        raise ValueError('Preferred reference heading is missing or ambiguous: ' +
                         reference['path'])
    # The caller may reuse parsed public notes within this request.
    item = dict(found[0])
    content = item.pop('text')
    return item | {'excerpt': content[:excerpt_limit],
                   'excerpt_complete': len(content) <= excerpt_limit}


def resolve_reference(reference, root=ROOT, excerpt_limit=1600):
    return _resolve_from_sections(reference, markdown_sections(reference['path'], root),
                                  excerpt_limit)


class KnowledgeCatalog:
    """Read public configuration once per operation, never cache conversation input.

    This object belongs to one brief or search. A new operation creates a new
    catalog, so edits to notes or bindings are visible without invalidating any
    process-wide cache. Returned references cannot mutate the parsed sections.
    """

    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.methods = load_methods(self.root)
        self.lookup = load_lookup(self.root)
        self._sections = {}
        self._preferred = {}

    def sections(self, path):
        if path not in self._sections:
            self._sections[path] = markdown_sections(path, self.root)
        return self._sections[path]

    def resolve(self, reference, excerpt_limit=1600):
        return _resolve_from_sections(reference, self.sections(reference['path']), excerpt_limit)

    def preferred(self, method_id):
        if method_id not in self.methods or method_id not in self.lookup['methods']:
            raise ValueError('Unknown method ID')
        if method_id not in self._preferred:
            reference = self.lookup['methods'][method_id]['preferred']
            if reference['path'] not in {s['path'] for s in self.methods[method_id]['sources']}:
                raise ValueError('Preferred reference is not a cited method source')
            self._preferred[method_id] = self.resolve(reference)
        return dict(self._preferred[method_id])


def operation_catalog(root, catalog=None):
    if catalog is None:
        return KnowledgeCatalog(root)
    if not isinstance(catalog, KnowledgeCatalog) or catalog.root != Path(root).resolve():
        raise ValueError('Use a public knowledge catalog from the requested repository')
    return catalog


def method_reference(method_id, root=ROOT):
    return KnowledgeCatalog(root).preferred(method_id)
