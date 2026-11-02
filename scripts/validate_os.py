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

    # Reading ledgers prove metadata consistency, not that a person/model read text.
    extra_note_paths=set()
    core_file=root/'knowledge/provenance/core_reading_ledger.json'
    if core_file.is_file():
        ledger=json.loads(core_file.read_text(encoding='utf-8'))
        s04=next(s for s in provenance['sources'] if s['id']=='S04')
        for item in ledger['units']:
            entry=next((e for e in s04['entries'] if e['entry']==item['entry']),None)
            if entry is None or entry['sha256'] != item['sha256']:
                errors.append('Core reading identity mismatch: '+item['id'])
            end=0
            for a,b in item['read_ranges']:
                if a != end or b <= a:errors.append('Noncontiguous reading range: '+item['id'])
                end=b
            if end != item['characters']:errors.append('Incomplete stated range: '+item['id'])
            extra_note_paths.add(item['notes'])
        complete=sum(e['reading_status'].startswith(('current_provided_entry_text_complete',
                     'historical_full_text_read_with_existing_notes')) for e in s04['entries'])
        counts=s04['coverage_counts']
        if complete != counts['supplied_text_complete_entries']:
            errors.append('TOP30 completed count does not match entry statuses')
        if sum(counts[k] for k in ['supplied_text_complete_entries',
                'legible_text_complete_with_unresolved_garbling',
                'remaining_without_verified_complete_reading']) != len(s04['entries']):
            errors.append('TOP30 counts do not sum to entry count')
    additional=root/'knowledge/provenance/additional_reading_ledger.json'
    if additional.is_file():
        for item in json.loads(additional.read_text(encoding='utf-8'))['records']:
            source=next(s for s in provenance['sources'] if s['id']==item['id'])
            if item['sha256'] != source['sha256']:
                errors.append('Upload reading identity mismatch: '+item['id'])
            if item['read_ranges'] != [[0,item['characters']]]:
                errors.append('Upload coverage mismatch: '+item['id'])
            extra_note_paths.add(item['notes'])
    for source in provenance['github_sources']:
        if source.get('core_round_synthesis_note'):
            extra_note_paths.add(source['core_round_synthesis_note'])
    cards=(root/'system/METHOD_CARDS.md').read_text(encoding='utf-8')
    for method in methods:
        heading='## '+method['id']+' '+method['name']
        if cards.count(heading)!=1 or method['operation'] not in cards or method['avoid'] not in cards:
            errors.append('Readable card is not synchronized: '+method['id'])

    # Validate local links in the new runtime and expansion notes. Existing historical
    # records can contain out-of-scope external source links and are not rewritten.
    docs = list((root/'system').glob('*.md'))
    docs += [root/p for p in ['README.md','START_HERE.md','AGENTS.md','CURRENT_STATE.md','KNOWLEDGE_INDEX.md','CHAT_GUIDANCE_PLAYBOOK.md']]
    docs += list((root/'knowledge/books').glob('*expansion.md'))
    docs += [root/'knowledge/books/G09-ocr-input.md']
    docs += [root/path for path in extra_note_paths]
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
