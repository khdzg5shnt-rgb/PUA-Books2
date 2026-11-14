#!/usr/bin/env python3
"""Render short working cards and a complete, separate source index."""
import argparse
import json
from pathlib import Path

from knowledge import ROOT, KnowledgeCatalog, citation_headings


def label(text):
    return text.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')


def render_documents(root=ROOT):
    catalog = KnowledgeCatalog(root)
    cards = ['# 方法卡', '',
        '日常只读当前主方法的一张卡，再读它的一处首选段落。完整出处另列在'
        '[方法出处索引](METHOD_SOURCES.md)，不要求每轮全部打开。', '',
        '方法是写作与决策规则；来源收录不等于某条回复已获实证验证。'
        '事实、当前边界和本轮任务始终优先。成品口吻见'
        '[一句自然话的取舍](REPLY_PROTOCOL.md#一句自然话的取舍)。', '']
    sources = ['# 方法出处索引', '',
        '本页逐项保留方法配置中的全部出处，供核原文与维护。日常使用'
        '[简短方法卡](METHOD_CARDS.md)和一处相关段落即可。', '',
        '精确绑定只对列出的段落有效；旧页码定位只保留追溯，不能把整份笔记'
        '都扩成该方法的可用段落。目录中的原书主张不自动成为当前动作或实证依据。', '']
    for mid, method in catalog.methods.items():
        primary = catalog.preferred(mid)
        cards.extend([f'## {mid} {method["name"]}', '',
            '适用：' + method['use_when'], '',
            '动作：' + method['operation'], '',
            '避免：' + method['avoid'], '',
            f'首选笔记：[{label(primary["heading"])}](../{primary["path"]})。'
            f'按该标题定位；运行入口会返回实际行段。', '',
            f'全部出处：[{len(method["sources"])}处](METHOD_SOURCES.md#{mid.lower()})。', '',
            '依据范围：' + method['evidence_level'], ''])
        if method.get('example') is not None:
            if method.get('example_kind') != 'synthetic_not_user_chat':
                raise ValueError('Only explicitly synthetic examples belong in method views')
            example = method['example']
            if (not isinstance(example, dict) or set(example) != {'other', 'reply'} or
                    any(not isinstance(value, str) for value in example.values())):
                raise ValueError('Synthetic method examples need two text fields')
            cards.extend([f'虚构例：她说“{example["other"]}”；草稿：“{example["reply"]}”', ''])
        sources.extend([f'## {mid}', '', method['name'] + f'；共{len(method["sources"])}处。', ''])
        for source in method['sources']:
            headings = citation_headings(source, catalog.sections(source['path']))
            entry = f'- [{label(source.get("locator", source["path"]))}](../{source["path"]})'
            if not headings:
                entry += '；旧定位，仅追溯，未绑定整份正文。'
            elif headings != [source.get('locator')]:
                entry += '；精确段落：' + '、'.join(headings) + '。'
            sources.append(entry)
        sources.append('')
    return {'system/METHOD_CARDS.md': '\n'.join(cards).rstrip() + '\n',
            'system/METHOD_SOURCES.md': '\n'.join(sources).rstrip() + '\n'}


def check_documents(root=ROOT):
    errors = []
    for relative, expected in render_documents(root).items():
        path = Path(root) / relative
        if not path.is_file() or path.read_text(encoding='utf-8') != expected:
            errors.append('Generated method view is not synchronized: ' + relative)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--write', action='store_true', help='Update both views from current configuration')
    modes.add_argument('--check', action='store_true', help='Check both views without writing')
    args = parser.parse_args()
    try:
        if args.write:
            documents = render_documents()
            for relative, text in documents.items():
                (ROOT / relative).write_text(text, encoding='utf-8')
            result = {'ok': True, 'updated': list(documents)}
        else:
            errors = check_documents()
            result = {'ok': not errors, 'errors': errors}
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
