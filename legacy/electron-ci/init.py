#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""electron-ci init：驱动 electron 官方 gclient 工具链就位编译依赖。

理念：ci 只是 electron 官方构建工具链（depot_tools / gclient / gn / ninja）
的薄封装，用 python 写只是图方便，不实现任何构建逻辑。实际编译必须使用
electron 官方工具链本身：
  1) gclient sync 按 electron 仓库 DEPS 拉取 chromium / node / buildtools，
     并自动执行官方 hooks：应用官方 patches（apply_all_patches.py）、
     npm install、外部二进制下载；
  2) gn gen + ninja 编译由 build.py 驱动（同样只调用官方命令）。

本脚本职责（顺序固定）：
  1) 准备 depot_tools（不存在则 clone，并前置 PATH）
  2) gclient config（工作区 gn-workspace，electron 落在 src/electron）
  3) gclient sync（锁定 ELECTRON_REVISION，官方 hooks 自动执行）

工作区（git 忽略，CI 每次全新生成）：
  gn-workspace/            gclient 工作区
    .gclient
    src/
      electron/            electron 锁定版本（--name src/electron，官方 patches 已应用）
      ... chromium 源码、node、buildtools 等（gclient 拉取，原样不动）

用法：
  python legacy/electron-ci/init.py [--revision <commit|tag>]
默认锁定 v4.0.0（真实 commit 005264ca1f；annotated tag v4.0.0 指向它）。
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
WORKSPACE = os.path.join(ROOT, 'gn-workspace')
SRC = os.path.join(WORKSPACE, 'src')
ELECTRON = os.path.join(SRC, 'electron')

ELECTRON_URL = 'https://github.com/electron/electron'
# v4.0.0 真实 commit：annotated tag `v4.0.0` -> commit 005264ca1f "Bump v4.0.0"
# （f2d1e5fa 是 tag 对象本身，checkout 两者等价；此处锁定 commit 最稳）
ELECTRON_REVISION = '005264ca1f92f920ff09c91c10a3d612ac94f1d7'


def run(argv, cwd=None):
    print('$ ' + ' '.join(argv))
    subprocess.check_call(argv, cwd=cwd)


def find_executable(name):
    """按 PATH 找可执行文件（py2.7 无 shutil.which，手动遍历）。"""
    for d in os.environ.get('PATH', '').split(os.pathsep):
        d = d.strip('"')
        if not d:
            continue
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None


def find_python3():
    """定位 python3 解释器（≥3.11）。

    gclient.py 是 python3 写的，且**最新版 depot_tools 需要 python3.11+**
    （`enum.StrEnum` 为 3.11 新增，ubuntu-22.04 系统 python3=3.10 会
    ImportError）。用版本探测：候选命令逐个验证版本，取第一个 ≥3.11 的；
    不能用本进程(py2)跑 gclient.py。
    """
    candidates = ('python3.11', 'python3.12', 'python3.13', 'python3', 'python', 'py')
    for name in candidates:
        p = find_executable(name)
        if not p:
            continue
        try:
            out = subprocess.check_output([p, '-c', 'import sys; print(sys.version_info[0], sys.version_info[1])'])
            major, minor = (int(x) for x in out.split())
            if (major, minor) >= (3, 11):
                return p
        except Exception:
            continue
    return None


def ensure_depot_tools():
    """准备 depot_tools：不存在则 clone；随后前置 PATH（gclient/gn/ninja 从这里取）。"""
    depot = os.path.join(ROOT, 'depot_tools')
    if not os.path.isdir(os.path.join(depot, '.git')):
        run(['git', 'clone',
             'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
             depot])
    os.environ['PATH'] = depot + os.pathsep + os.environ.get('PATH', '')
    return depot


def gclient(depot, argv):
    py3 = find_python3()
    if py3 is None:
        raise SystemExit('no python3 found in PATH (depot_tools/gclient.py needs python3)')
    run([py3, os.path.join(depot, 'gclient.py')] + argv, cwd=WORKSPACE)


def check_hook_python():
    """防御检查：DEPS hooks（apply_all_patches.py 等）由 gclient 调 `python`，
    这些是 v4.0.0 时代的 py2 脚本，`python` 必须解析到 python2。
    workflow 的 Setup/Init 步骤负责把 python2 前置（linux: /usr/local/bin 的
    shim；windows: C:/Python27 前置 PATH）。这里只做 fail-fast 检查。"""
    py = find_executable('python')
    if py is None:
        print('WARNING: `python` not found in PATH (DEPS hooks may fail)')
        return
    try:
        out = subprocess.check_output([py, '-c', 'import sys; print(sys.version_info[0])'])
    except Exception:
        print('WARNING: cannot probe `python` version')
        return
    if out.strip() != '2':
        print('ERROR: `python` resolves to %s -> %s, but v4.0.0 DEPS hooks need python2'
              % (py, out.strip()))
        print('       fix PATH first (linux: ln -s /usr/bin/python2 /usr/local/bin/python;')
        print('       windows: prepend C:/Python27 to PATH)')
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description='Init electron build workspace (gclient)')
    parser.add_argument('--revision', default=ELECTRON_REVISION,
                        help='electron revision to lock (commit sha or tag)')
    parser.add_argument('--clean', action='store_true',
                        help='remove gn-workspace before init')
    args = parser.parse_args()

    if args.clean:
        import shutil
        if os.path.isdir(WORKSPACE):
            shutil.rmtree(WORKSPACE)
    if not os.path.isdir(WORKSPACE):
        os.makedirs(WORKSPACE)

    depot = ensure_depot_tools()
    check_hook_python()
    gclient(depot, ['config', '--name', 'src/electron', '--unmanaged', ELECTRON_URL])
    gclient(depot, ['sync', '--with_branch_heads', '--with_tags',
                    '--revision', 'src/electron@' + args.revision])
    print('init done. Run: python legacy/electron-ci/build.py --target-arch x64')
    return 0


if __name__ == '__main__':
    sys.exit(main())
