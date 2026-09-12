#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'upstream.json'

def select_latest_stable(releases: list[dict]) -> str:
    for release in releases:
        if not release.get('draft') and not release.get('prerelease') and release.get('tag_name'):
            return str(release['tag_name'])
    return ''

def update_tracking(config: dict, scanned: str = '', released: str = '') -> dict:
    updated=dict(config)
    if scanned:
        updated['last_scanned_commit']=scanned
    if released:
        updated['stable_release']=released
        updated['last_released_upstream_tag']=released
    return updated

def compute_status(config: dict, branch_sha: str, stable_tag: str) -> dict:
    return {
        'branch': config.get('branch','master'),
        'branch_sha': branch_sha,
        'branch_changed': bool(branch_sha and branch_sha != config.get('last_scanned_commit','')),
        'stable_tag': stable_tag,
        'stable_release_changed': bool(stable_tag and stable_tag != config.get('last_released_upstream_tag','')),
        'last_scanned_commit': config.get('last_scanned_commit',''),
        'last_released_upstream_tag': config.get('last_released_upstream_tag',''),
    }

def _api_json(url: str, token: str=''):
    headers={'Accept':'application/vnd.github+json','User-Agent':'OptiScaler-fork-CN-upstream-sync','X-GitHub-Api-Version':'2022-11-28'}
    if token: headers['Authorization']=f'Bearer {token}'
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=30) as response:
        return json.load(response)

def github_status(config: dict, token: str='') -> dict:
    repo_url=config['repository'].removesuffix('.git')
    parts=urllib.parse.urlparse(repo_url).path.strip('/').split('/')
    if len(parts)<2: raise ValueError(f'cannot infer GitHub owner/repo from {repo_url}')
    owner,repo=parts[-2],parts[-1]
    branch=config.get('branch','master')
    commit=_api_json(f'https://api.github.com/repos/{owner}/{repo}/commits/{urllib.parse.quote(branch)}',token)
    releases=_api_json(f'https://api.github.com/repos/{owner}/{repo}/releases?per_page=30',token)
    return compute_status(config,str(commit.get('sha','')),select_latest_stable(releases))

def _write_outputs(path: Path, status: dict):
    def b(v): return 'true' if v else 'false'
    lines=[
        f"branch={status['branch']}", f"branch_sha={status['branch_sha']}",
        f"branch_changed={b(status['branch_changed'])}", f"stable_tag={status['stable_tag']}",
        f"stable_release_changed={b(status['stable_release_changed'])}"
    ]
    with path.open('a',encoding='utf-8') as f:
        for line in lines: f.write(line+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',type=Path,default=CONFIG)
    ap.add_argument('--json-out',type=Path)
    ap.add_argument('--github-output',type=Path)
    ap.add_argument('--set-scanned',default='')
    ap.add_argument('--set-released',default='')
    args=ap.parse_args()
    config=json.loads(args.config.read_text(encoding='utf-8'))
    if args.set_scanned or args.set_released:
        config=update_tracking(config,args.set_scanned,args.set_released)
        args.config.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return 0
    status=github_status(config,os.getenv('GITHUB_TOKEN',''))
    print(json.dumps(status,ensure_ascii=False,indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.github_output: _write_outputs(args.github_output,status)
    return 0

if __name__=='__main__': raise SystemExit(main())
