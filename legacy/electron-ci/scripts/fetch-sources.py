#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""通用拉取器：一次调用拉取一个仓库源码到 vendors/<name>。

仿 bilibili/ijkplayer 的 pull-repo-base.sh——脚本只负责「拉取」这一行为，
拉哪个仓库、哪个 commit 由调用方（init-sources.py 清单 / 命令行）传入。

获取方式：**git 迁出指定版本（全量克隆，与 bilibili/ijkplayer 的
pull-repo-base.sh 一致——git clone 即全量历史，工作树 checkout 到目标版本）**——
  git clone {url} {target} → git checkout {commit}（锁定该版本）
  → git submodule update --init --recursive
    （保留仓库子模块机制，子模块按其 .gitmodules 锁定的版本就位；
    无子模块的仓库该命令安静成功）
  → git lfs install（配置 LFS 过滤器）+ git lfs pull（拉取 LFS 对象）
    （仓库自身声明的大文件走 LFS 的，全部落地为真实内容）

用法（python2 运行，Actions 亦同）：
  python fetch-sources.py <url> <commit> <name>

获取产物均被 .gitignore 忽略，不入版本库。
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VENDORS = os.path.join(ROOT, 'vendors')


def fetch_sources(url, commit, name):
    """git 迁出指定版本到 vendors/<name>（已存在则跳过，幂等）。

    全量克隆（与 bilibili/ijkplayer 的 pull-repo-base.sh 一致），
    工作树 checkout 锁定 commit。vendors/ 不存在时先创建。"""
    if not os.path.isdir(VENDORS):
        os.makedirs(VENDORS)
    target = os.path.join(VENDORS, name)
    if os.path.isdir(target):
        # 幂等分支：确保 LFS 对象落地（增量拉取，无副作用）
        print('%s source already at %s, git lfs pull' % (name, target))
        subprocess.check_call(['git', '-C', target, 'lfs', 'pull'])
        return
    print('git cloning %s' % url)
    subprocess.check_call(['git', 'clone', url, target])
    subprocess.check_call(['git', '-C', target, 'checkout', commit])
    print('git submodule update --init --recursive (%s)' % name)
    subprocess.check_call(['git', '-C', target, 'submodule', 'update',
                           '--init', '--recursive'])
    print('git lfs install + pull (%s)' % name)
    subprocess.check_call(['git', '-C', target, 'lfs', 'install'])
    subprocess.check_call(['git', '-C', target, 'lfs', 'pull'])
    print('%s (git) source at %s' % (name, target))


def main():
    parser = argparse.ArgumentParser(
        description='Fetch a repo source into vendors/<name> (git checkout mode)')
    parser.add_argument('url', help='Git repo url, e.g. https://github.com/electron/electron')
    parser.add_argument('commit', help='Full commit SHA (pin version)')
    parser.add_argument('name', help='Target dir name under vendors/')
    args = parser.parse_args()
    fetch_sources(args.url, args.commit, args.name)
    print('fetch %s done.' % args.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
