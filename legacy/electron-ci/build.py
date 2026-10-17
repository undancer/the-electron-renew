#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""electron-ci build：驱动 electron 官方 GN/ninja 工具链编译。

理念：ci 只是 electron 官方构建工具链的薄封装——实际编译使用官方
gn gen + ninja（见官方 docs/development/build-instructions-gn.md），
本脚本只负责把命令串起来并检查产物，不实现任何构建逻辑。

前提：init.py 已完成 gclient sync（gn-workspace/src 就位，官方 patches
已应用、依赖已就绪、depot_tools 已 clone）。

流程：
  1) 检查 gn-workspace/src/electron 存在（不存在先跑 init.py）
  2) cd gn-workspace/src
  3) gn gen out/Release --args=import("//electron/build/args/release.gn")
  4) ninja -C out/Release electron
  5) 产物 src/out/Release/electron（linux）/ electron.exe（windows）

用法：
  python legacy/electron-ci/init.py
  python legacy/electron-ci/build.py --target-arch x64
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
WORKSPACE = os.path.join(ROOT, 'gn-workspace')
SRC = os.path.join(WORKSPACE, 'src')
ELECTRON = os.path.join(SRC, 'electron')


def run(argv, cwd=None):
    print('$ ' + ' '.join(argv))
    subprocess.check_call(argv, cwd=cwd)


def main():
    parser = argparse.ArgumentParser(description='Build electron (GN/ninja) via electron-ci')
    parser.add_argument('-t', '--target-arch', default='x64',
                        help='target cpu (official: x86 from x64 hosts tested)')
    parser.add_argument('-c', '--config', default='Release',
                        help='gn config (Release/Debug)')
    args = parser.parse_args()

    if not os.path.isdir(ELECTRON):
        print('ERROR: %s not present; run init.py first' % ELECTRON)
        return 1

    # gn/ninja 来自 depot_tools（init.py 已 clone），前置 PATH 后直接调命令名
    depot = os.path.join(ROOT, 'depot_tools')
    if os.path.isdir(depot):
        os.environ['PATH'] = depot + os.pathsep + os.environ.get('PATH', '')

    config = args.config
    gn_args = 'import("//electron/build/args/%s.gn")' % config.lower()
    if args.target_arch != 'x64':
        gn_args += ' target_cpu="%s"' % args.target_arch

    run(['gn', 'gen', 'out/' + config, '--args=' + gn_args], cwd=SRC)
    run(['ninja', '-C', 'out/' + config, 'electron'], cwd=SRC)

    exe = 'electron' if os.name != 'nt' else 'electron.exe'
    dist = os.path.join(SRC, 'out', config, exe)
    print('DONE. binary: ' + dist)
    return 0


if __name__ == '__main__':
    sys.exit(main())
