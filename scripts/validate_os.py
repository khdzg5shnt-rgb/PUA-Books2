#!/usr/bin/env python3
"""Check cross-references, byte identities and actionable route configuration."""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from knowledge import citation_headings, markdown_sections, method_reference

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    errors = []
    routes = json.loads((root / 'system/router.json').read_text(encoding='utf-8'))
    methods = json.loads((root / 'system/methods.json').read_text(encoding='utf-8'))['methods']
    sources = json.loads((root / 'system/sources.json').read_text(encoding='utf-8'))
    provenance = json.loads((root / 'knowledge/provenance/external_sources.json').read_text(encoding='utf-8'))
    historical = json.loads((root/'knowledge/provenance/source_inventory.json').read_text(encoding='utf-8'))
    lookup = json.loads((root/'system/knowledge_map.json').read_text(encoding='utf-8'))['methods']
    tasks = json.loads((root/'system/tasks.json').read_text(encoding='utf-8'))['tasks']
    state = json.loads((root/'system/work_state.json').read_text(encoding='utf-8'))
    method_ids = [m['id'] for m in methods]
    route_ids = [r['id'] for r in routes['routes']]
    if len(method_ids) != len(set(method_ids)) or len(route_ids) != len(set(route_ids)):
        errors.append('Duplicate method or route IDs')
    if routes['routes'][-1]['when'] != {'always':True}:
        errors.append('No final fallback')

    def check_expr(e):
        if not isinstance(e, dict):
            errors.append('Rule expression must be an object')
            return
        if e == {'always':True}:
            return
        if len(e) == 1 and ('all' in e or 'any' in e):
            children=e.get('all', e.get('any'))
            if not isinstance(children,list) or not children:
                errors.append('Rule group must contain conditions')
                return
            for child in children:
                check_expr(child)
        elif (set(e) != {'field','op','value'} or e.get('field') not in routes['defaults']
              or e.get('op') not in ['eq','in','gte']):
            errors.append('Invalid rule expression: '+str(e))
        else:
            field,op=e['field'],e['op']
            default=routes['defaults'][field]
            operands=e['value'] if op=='in' else [e['value']]
            if (not isinstance(operands,list) or not operands or
                    any(type(value) is not type(default) or
                        (field in routes['enums'] and value not in routes['enums'][field])
                        for value in operands) or
                    (op=='gte' and type(default) is not int)):
                errors.append('Rule operand type mismatch: '+field)

    if set(routes.get('field_help',{})) != set(routes['defaults']):
        errors.append('Every fact field needs a current-scope description')
    human_routes = re.findall(r'^\|\s*\d+\s*\|\s*(R[0-9A-Z]+)\s*\|',
                             (root/'system/SCENARIO_ROUTER.md').read_text(encoding='utf-8'),
                             flags=re.M)
    if human_routes != route_ids:
        errors.append('Readable route order does not match configuration')

    for rule in routes['routes']:
        check_expr(rule['when'])
        if len(rule['method_ids']) != 1 or rule['method_ids'][0] not in method_ids:
            errors.append('Bad primary method for ' + rule['id'])
        if rule['action'] not in {'draft','hold','stop','clarify'}:
            errors.append('Unknown route action: '+rule['id'])
        if ('acknowledgement_only' in rule and
                (type(rule['acknowledgement_only']) is not bool or
                 (rule['acknowledgement_only'] and
                  (rule['action'] != 'draft' or rule['method_ids'] not in (['M17'], ['M23']))))):
            errors.append('Invalid boundary acknowledgement contract: '+rule['id'])
    for method in methods:
        if not method['sources'] or not method['avoid'] or not method['use_when']:
            errors.append('Incomplete card '+method['id'])
        for source in method['sources']:
            if not (root/source['path']).is_file():
                errors.append('Missing method source: '+source['path'])
            elif 'section_headings' in source:
                try:
                    if not source['path'].endswith('.md'):
                        raise ValueError('Explicit headings require a Markdown source')
                    citation_headings(source, markdown_sections(source['path'], root))
                except (ValueError, OSError):
                    errors.append('Invalid method source section binding: '+method['id'])
    if set(lookup) != set(method_ids):
        errors.append('Knowledge map must cover every method exactly')
    for method_id,item in lookup.items():
        aliases=item.get('aliases')
        if not isinstance(aliases,list) or not aliases or any(
                not isinstance(value,str) or not value.strip() for value in aliases):
            errors.append('Invalid lookup aliases: '+method_id)
        try:
            method_reference(method_id,root)
        except (ValueError,KeyError,OSError):
            errors.append('Invalid preferred method section: '+method_id)
    if set(tasks) != {'reply','meaning','analysis','review','training'}:
        errors.append('Task modes must contain the five supported tasks')
    if any(tasks.get('reply',{}).get(key) != value for key,value in
           [('max_candidates',1),('max_lines',2),('max_questions',1)]):
        errors.append('Reply contract must keep one short candidate')
    for source in sources['records']:
        if not (root/source['local_entry']).is_file():
            errors.append('Missing source entry: '+source['id'])
    if len(sources['records']) != len({s['id'] for s in sources['records']}):
        errors.append('Duplicate source IDs')
    if sum(s.get('is_book', False) for s in sources['records']) != 119:
        errors.append('Original book classification must contain 119 book files')
    groups={'books2_original_snapshot':historical['records'],
            'uploaded_material':provenance['sources'],
            'public_github_source':provenance['github_sources']}
    for group,items in groups.items():
        actual={s['id'] for s in sources['records'] if s['group']==group}
        if actual != {item['id'] for item in items}:
            errors.append('Source IDs do not match provenance: '+group)
    originals={item['id']:item for item in historical['records']}
    for item in sources['records']:
        if item['group']=='books2_original_snapshot':
            prior=originals.get(item['id'],{})
            if any(item[key] != prior.get(key) for key in ['git_blob_sha','reading_status']):
                errors.append('Original source identity/status mismatch: '+item['id'])
            if item.get('is_book') != (prior.get('kind')=='book_file'):
                errors.append('Original book kind mismatch: '+item['id'])
    books=[s for s in sources['records'] if s.get('is_book')]
    complete=sum(s['reading_status']=='provided_file_text_complete' for s in books)
    unread=sum(s['reading_status']=='unread' for s in books)
    partial=len(books)-complete-unread
    expected_stats={'original_items':len(historical['records']),'book_files':len(books),
        'uploads':len(provenance['sources']),'public_github_sources':len(provenance['github_sources']),
        'source_records':len(sources['records']),'current_book_files_text_complete':complete,
        'current_book_files_text_partial':partial,'current_book_files_not_started':unread}
    if sources['statistics'] != expected_stats:
        errors.append('Source statistics do not match records')
    # An unfinished file cannot be bypassed by opening an unread one. The user-
    # facing ratio counts completed supplied files, never completed + partial.
    unfinished_ids = [s['id'] for s in books if s['reading_status'] not in
                      {'provided_file_text_complete', 'unread'}]
    if state.get('unfinished_file_queue') != unfinished_ids:
        errors.append('Unfinished-file queue does not match source records')
    if unfinished_ids and sources['next_work_unit']['id'] != unfinished_ids[0]:
        errors.append('Finish the current unfinished file before opening another book')
    display = state.get('progress_display', {})
    if (display.get('reported_numerator') != complete or
            display.get('reported_denominator') != len(books) or
            display.get('ratio_basis') != 'current_file_text_complete_only' or
            display.get('partial_excluded_from_numerator') is not True):
        errors.append('Reported reading ratio must count completed files only')
    if state['reading_bookmark'] != sources['next_work_unit']:
        errors.append('Runtime reading bookmark does not match source state')
    next_unit=sources['next_work_unit']
    next_original=originals.get(next_unit['id'],{})
    if (next_unit['git_blob_sha'] != next_original.get('git_blob_sha') or
            next_unit['path'] != next_original.get('path')):
        errors.append('Next reading unit identity mismatch')
    for key in ['runtime_entry','request_example','report','validation']:
        if not (root/state[key]).is_file():
            errors.append('Missing runtime entry: '+key)
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
            if item.get('reading_status') == 'supplied_text_partial':
                if not (0 < end < item['characters']) or item.get('next_character') != end:
                    errors.append('Partial source has no accurate next breakpoint: '+item['id'])
            elif end != item['characters']:
                errors.append('Incomplete stated range: '+item['id'])
            extra_note_paths.add(item['notes'])
        top30_complete=sum(e['reading_status'].startswith(('current_provided_entry_text_complete',
                     'historical_full_text_read_with_existing_notes')) for e in s04['entries'])
        counts=s04['coverage_counts']
        if top30_complete != counts['supplied_text_complete_entries']:
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
            if item.get('coverage_mode') == 'mixed_direct_read_and_verified_prior_text':
                reused=item['reused_reading']
                prior=next((s for s in provenance['sources'] if s['id']==reused['source_id']),None)
                entry=next((e for e in (prior or {}).get('entries',[]) if e['entry']==reused['entry']),None)
                if entry is None or entry['sha256'] != reused['sha256'] or not entry['reading_status'].startswith(
                        ('current_provided_entry_text_complete','historical_full_text_read_with_existing_notes')):
                    errors.append('Reused reading has no matching completed source: '+item['id'])
                proof_file=root/reused['proof']
                if not proof_file.is_file():
                    errors.append('Missing page equivalence manifest: '+item['id'])
                else:
                    proof=json.loads(proof_file.read_text(encoding='utf-8'))
                    if (proof['pdf_sha256'] != item['sha256'] or
                            proof['prior_entry_sha256'] != reused['sha256'] or not proof['not_a_new_full_read']):
                        errors.append('Page equivalence identity mismatch: '+item['id'])
                    rows=proof['pages']
                    if [r['file_page'] for r in rows] != list(range(1,item['page_count']+1)):
                        errors.append('Incomplete page equivalence manifest: '+item['id'])
                    a,b=reused['file_pages']
                    matched=[r for r in rows if a<=r['file_page']<=b]
                    if len(matched) != reused['page_count'] or any(
                            not r['normalized_equal'] or
                            r['prior_normalized_characters'] != r['pdf_normalized_characters'] or
                            r['prior_normalized_sha256'] != r['pdf_normalized_sha256'] for r in matched):
                        errors.append('Claimed reused pages do not match: '+item['id'])
                end=0
                for a,b in item['actual_read_chunks']:
                    if a<end or b<=a or b>item['characters']:
                        errors.append('Invalid direct reading range: '+item['id'])
                    end=b
                if sum(b-a for a,b in item['actual_read_chunks']) != item['newly_read_characters']:
                    errors.append('Direct and reused reading counts conflated: '+item['id'])
            extra_note_paths.add(item['notes'])
    for source in provenance['github_sources']:
        if source.get('core_round_synthesis_note'):
            extra_note_paths.add(source['core_round_synthesis_note'])
        extra_note_paths.update(source.get('continuation_synthesis_notes', []))
        archived_documents=sum(a['repository']==source['repository'] and a['source_path']!='LICENSE'
                               for a in provenance['archives'])
        if archived_documents != source['archived_document_count']:
            errors.append('GitHub archive count mismatch: '+source['id'])
        for item in source['files']:
            if item.get('read_coverage'):
                if item['read_coverage']['ranges'] != [[0,item['characters']]]:
                    errors.append('GitHub reading coverage mismatch: '+item['original_path'])
                extra_note_paths.add(item['notes'])
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
    docs += [root/item['preferred']['path'] for item in lookup.values()]
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
            'task_modes':len(tasks),'preferred_sections':len(lookup),
            'source_records':len(sources['records']), 'archived_files':len(provenance['archives']),
            'book_text_complete':complete,'book_not_started':unread,
            'scope':'结构/链接/来源身份/阅读状态/段落定位与输出约定检查，不是截图识别或恋爱效果验证'}


if __name__ == '__main__':
    result=validate()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['ok'] else 1)
