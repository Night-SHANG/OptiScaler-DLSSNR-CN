#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(*cmd,cwd=None): subprocess.run(list(cmd),cwd=cwd,check=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--worktree',type=Path,default=ROOT/'_upstream'); ap.add_argument('--ref',default=''); ap.add_argument('--no-submodules',action='store_true'); args=ap.parse_args()
    cfg=json.loads((ROOT/'upstream.json').read_text())
    ref=args.ref or cfg.get('commit') or cfg.get('branch','master')
    if ref=='auto': ref=cfg.get('branch','master')
    if args.worktree.exists(): shutil.rmtree(args.worktree)
    run('git','clone','--no-tags',cfg['repository'],str(args.worktree))
    run('git','fetch','origin',ref,cwd=args.worktree)
    run('git','checkout','--detach','FETCH_HEAD',cwd=args.worktree)
    if not args.no_submodules: run('git','submodule','update','--init','--recursive',cwd=args.worktree)
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.worktree,text=True).strip()
    print(sha)
if __name__=='__main__': main()
