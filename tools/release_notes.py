#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=json.loads((ROOT/'upstream.json').read_text(encoding='utf-8'))

def release_tag_name(upstream_ref: str, upstream_commit: str) -> str:
    safe=re.sub(r'[^A-Za-z0-9._-]+','-',upstream_ref).strip('-').lower() or 'upstream'
    return f'cn-{safe}-{upstream_commit[:8].lower()}'

def translation_stats(catalog: dict, zh: dict) -> dict:
    active={k:v for k,v in catalog.get('entries',{}).items() if not v.get('obsolete')}
    z=zh.get('entries',{})
    reviewed=machine=missing=stale=0
    for k,e in active.items():
        x=z.get(k,{})
        if not x.get('text'):
            missing += 1
        elif x.get('source_hash') != e.get('source_hash'):
            stale += 1
        elif x.get('state') == 'reviewed':
            reviewed += 1
        elif x.get('state') == 'machine_translated':
            machine += 1
        else:
            missing += 1
    total=len(active); effective=reviewed+machine
    return {'total':total,'effective':effective,'reviewed':reviewed,'machine':machine,
            'missing':missing,'stale':stale,'coverage':100.0*effective/total if total else 100.0}


def change_stats(pending: dict, catalog: dict, zh: dict) -> dict:
    scan=pending.get('scan',{}) if isinstance(pending,dict) else {}
    added=list(scan.get('added',[])); changed=list(scan.get('changed',[])); removed=list(scan.get('removed',[]))
    active={k:v for k,v in catalog.get('entries',{}).items() if not v.get('obsolete')}
    zentries=zh.get('entries',{})
    effective=0
    for key in dict.fromkeys(added+changed):
        source=active.get(key)
        translated=zentries.get(key,{})
        if (source and translated.get('text') and translated.get('source_hash')==source.get('source_hash')
                and translated.get('state') in ('reviewed','machine_translated')):
            effective += 1
    return {'added':len(added),'changed':len(changed),'removed':len(removed),'newly_effective':effective}

def render_notes(upstream_ref: str, upstream_commit: str, catalog: dict, zh: dict, pending: dict | None = None) -> str:
    s=translation_stats(catalog,zh)
    c=change_stats(pending or {},catalog,zh)
    return f'''# {UPSTREAM.get('release_prefix','OptiScaler CN')}\n\n- 对应官方版本/引用：`{upstream_ref}`\n- 对应官方 commit：`{upstream_commit}`\n- 中文覆盖：**{s['effective']}/{s['total']} ({s['coverage']:.2f}%)**\n- 人工确认：{s['reviewed']}\n- 机器翻译：{s['machine']}\n- 尚未翻译（自动英文 fallback）：{s['missing']}\n- 源文变化、待复核：{s['stale']}\n- 本次扫描新增 UI：{c['added']}\n- 本次扫描变化 UI：{c['changed']}\n- 本次扫描删除 UI：{c['removed']}\n- 本次新增/更新有效中文：{c['newly_effective']}\n- 构建日期（UTC）：{datetime.now(timezone.utc).isoformat()}\n\n这是社区中文派生构建，不是对应上游 Fork 的官方发布。未覆盖或待复核的项目会显示官方英文，不会显示空白。\n'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream-ref',required=True)
    ap.add_argument('--upstream-commit',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--channel',choices=('master','stable'),default='stable')
    ap.add_argument('--github-output',type=Path)
    a=ap.parse_args()
    cat=json.loads((ROOT/'Localization'/a.channel/'catalog.json').read_text(encoding='utf-8'))
    zh=json.loads((ROOT/'Localization/zh-CN.json').read_text(encoding='utf-8'))
    pending_path=ROOT/'Localization'/a.channel/'pending.json'
    pending=json.loads(pending_path.read_text(encoding='utf-8')) if pending_path.exists() else {}
    a.out.write_text(render_notes(a.upstream_ref,a.upstream_commit,cat,zh,pending),encoding='utf-8')
    tag=release_tag_name(a.upstream_ref,a.upstream_commit)
    if a.github_output:
        with a.github_output.open('a',encoding='utf-8') as f: f.write(f'tag={tag}\n')
    print(tag)
    return 0

if __name__=='__main__': raise SystemExit(main())
