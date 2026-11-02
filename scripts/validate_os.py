#!/usr/bin/env python3
"""Check cross-references, byte identities and actionable route configuration."""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    errors = []
    routes = json.loads((root / 'system/router.json').read_text(encoding='utf-8'))
    methods = json.loads((root / 'system/methods.json').read_text(encoding='utf-8'))['methods']
    sources = json.loads((root / 'system/sources.json').read_text(encoding='utf-8'))
    provenance = json.loads((root / 'knowledge/provenance/external_sources.json').read_text(encoding='utf-8'))
    method_ids = [m['id'] for m in methods]
    route_ids = [r['id'] for r in routes['routes']]
    if len(method_ids) != len(set(method_ids)) or len(route_ids) != len(set(route_ids)):
        errors.append('Duplicate method or route IDs')
    if routes['routes'][-1]['when'] != {'always':True}:
        errors.append('No final fallback')

    def check_expr(e):
        if e.get('always') is True:
            return
        if 'all' in e or 'any' in e:
            for child in e.get('all', e.get('any')):
                check_expr(child)
        elif e.get('field') not in routes['defaults'] or e.get('op') not in ['eq','in','gte']:
            errors.append('Invalid rule expression: '+str(e))

    for rule in routes['routes']:
        check_expr(rule['when'])
        if len(rule['method_ids']) != 1 or rule['method_ids'][0] not in method_ids:
            errors.append('Bad primary method for ' + rule['id'])
    for method in methods:
        if not method['sources'] or not method['avoid'] or not method['use_when']:
            errors.append('Incomplete card '+method['id'])
        for source in method['sources']:
            if not (root/source['path']).is_file():
                errors.append('Missing method source: '+source['path'])
    for source in sources['records']:
        if not (root/source['local_entry']).is_file():
            errors.append('Missing source entry: '+source['id'])
    if len(sources['records']) != len({s['id'] for s in sources['records']}):
        errors.append('Duplicate source IDs')
    if sum(s.get('is_book', False) for s in sources['records']) != 119:
        errors.append('Original book classification must contain 119 book files')
    for group, expected in [('books2_original_snapshot',126),('uploaded_material',22),('public_github_source',9)]:
        if sum(s['group']==group for s in sources['records']) != expected:
            errors.append('Incorrect source count for '+group)
    historical = json.loads((root/'knowledge/provenance/source_inventory.json').read_text(encoding='utf-8'))
    old_readme = next(item for item in historical['records'] if item['path']=='README.md')
    data = (root/'knowledge/provenance/README-original.md').read_bytes()
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != old_readme['git_blob_sha']:
        errors.append('Original README backup bytes changed')
    for archive in provenance['archives']:
        path = root/archive['archive_path']
        if not path.is_file():
            errors.append('Missing archive '+str(path.relative_to(root)))
            continue
        data = path.read_bytes()
        git_blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if hashlib.sha256(data).hexdigest() != archive['sha256'] or git_blob != archive['git_blob_sha']:
            errors.append('Archive bytes mismatch: '+archive['archive_path'])
        if not (root/archive['license_archive']).is_file():
            errors.append('Missing license: '+archive['license_archive'])

    # Validate local links in the new runtime and expansion notes. Existing historical
    # records can contain out-of-scope external source links and are not rewritten.
    docs = list((root/'system').glob('*.md'))
    docs += [root/p for p in ['README.md','START_HERE.md','AGENTS.md','CURRENT_STATE.md','KNOWLEDGE_INDEX.md','CHAT_GUIDANCE_PLAYBOOK.md']]
    docs += list((root/'knowledge/books').glob('*expansion.md'))
    docs += [root/'knowledge/books/G09-ocr-input.md']
    for doc in docs:
        if not doc.is_file():
            errors.append('Missing required document '+str(doc.relative_to(root)))
            continue
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if re.match(r'[a-z]+:', link) or link.startswith('#'):
                continue
            target=unquote(link.split('#')[0])
            if target and not (doc.parent/target).resolve().is_file():
                errors.append('Broken local link: '+str(doc.relative_to(root))+' -> '+link)
    return {'ok':not errors, 'errors':errors, 'methods':len(methods), 'routes':len(route_ids),
            'source_records':len(sources['records']), 'archived_files':len(provenance['archives']),
            'scope':'结构/链接/归档身份检查，不是截图识别或恋爱效果验证'}


if __name__ == '__main__':
    result=validate()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['ok'] else 1)
