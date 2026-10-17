#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""构建 electron（基线 v4.0.0）。

蓝本：ymmuse/electron-ci（python2，GitHub Actions 用 python2 运行）。

职责边界：**build.py 只负责编译链**——bootstrap → build → dist。
源码获取、补丁应用、编译参数编辑均不在本脚本：由根目录 **init.py** 先行完成
（init.py = 下载源码 → 复制工作副本 → 应用补丁 → 编辑编译参数）。
build.py 不下载、不操作任何 git 子模块。

源码落位（均 git 忽略，不入库）：
  vendors/electron/    官方 electron base（git 迁出 f2d1e5fa = v4.0.0）
  electron/            **工作副本**（init.py 从 vendors/electron 复制到 ci 根目录下；
                       补丁、编译参数、编译全部在此副本上进行，vendors/ base 保持原样）

流程：
  1) 检查 electron/ 工作副本存在（不存在则退出——先跑 init.py）
  2) electron/script/bootstrap.py（官方脚本，经 DEPS/gclient 就位依赖）
  3) electron/script/build.py -c R
  4) electron/script/create-dist.py    （产物在 electron/dist）

用法（python2 运行，Actions 亦同）：
  python legacy/electron-ci/init.py                           # 下载源码+复制副本+补丁+参数
  python legacy/electron-ci/build.py --target-arch x64         # 再编译
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
# 工作副本由 init.py 从 vendors/electron 复制到 ci 根目录下 electron/，
# 所有修改与编译都在副本上进行（vendors/ base 保持原样）
ELECTRON = os.path.join(ROOT, 'electron')


def run(argv, cwd=None):
    print('$ ' + ' '.join(argv))
    subprocess.check_call(argv, cwd=cwd)


def bootstrap_electron(target_arch):
    """驱动 electron 官方 bootstrap（release）：script/bootstrap.py 按
    electron 自带 DEPS/gclient 逻辑就位编译依赖。"""
    run([sys.executable,
         os.path.join(ELECTRON, 'script', 'bootstrap.py'),
         '--target_arch=' + target_arch,
         '-v'],
        cwd=ELECTRON)


def build_electron_dist():
    run([sys.executable, os.path.join(ELECTRON, 'script', 'build.py'), '-c', 'R'],
        cwd=ELECTRON)
    run([sys.executable, os.path.join(ELECTRON, 'script', 'create-dist.py')],
        cwd=ELECTRON)


def main():
    parser = argparse.ArgumentParser(description='Build electron (baseline v4.0.0) via electron-ci')
    parser.add_argument('-t', '--target-arch', default='x64', help='Target architecture')
    parser.add_argument('--dist-only', action='store_true',
                        help='Only build electron dist, skip bootstrap')
    args = parser.parse_args()

    # 前置检查：工作副本 electron/ 必须存在（由 init.py 复制生成），
    # 不存在直接退出——build.py 不负责下载/复制
    if not os.path.isdir(ELECTRON):
        print('ERROR: electron/ not present.')
        print('Run init.py first:  python legacy/electron-ci/init.py')
        return 1

    if not args.dist_only:
        bootstrap_electron(args.target_arch)

    build_electron_dist()
    print('DONE. dist is under ' + os.path.join(ELECTRON, 'dist'))


if __name__ == '__main__':
    sys.exit(main())
