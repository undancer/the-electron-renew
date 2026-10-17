#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""拉取全部编译所需源码（仿 bilibili/ijkplayer 的 init-android.sh：
逐行调用通用拉取器 fetch-sources.py，一行一个仓库，全部 git 迁出）。

追加第三方仓库：在本文件按行追加一条 pull(...) 调用即可，
无需改动 fetch-sources.py 拉取器本身。

用法（python2 运行，Actions 亦同）：
  python legacy/electron-ci/scripts/init-sources.py
"""

import os
import subprocess
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
FETCH = os.path.join(SCRIPTS, 'fetch-sources.py')


def pull(url, commit, name):
    subprocess.check_call([sys.executable, FETCH, url, commit, name])


def main():
    # 官方 electron（commit 9dfb85dd = v1.8.4，Chromium 63）
    # ——蓝本 electron-ci 的 electron 子模块指定版本（官方，非 ymmuse 修改版）。
    #    git 迁出保留仓库子模块机制：递归 update 自动拉取官方 libcc
    #    （vendor/libchromiumcontent）、node、depot_tools 等（按 electron 源码
    #    .gitmodules 锁定的版本就位），无需手动复制。
    pull('https://github.com/electron/electron',
         '9dfb85dd21bed39639144e30f3438debdf9010d2', 'electron')

    # 注：yaml/pyyaml 目前**不迁出**——electron 默认编译链不需要；
    #     补丁解析（patches.py）对 yaml 为惰性引入，待需要补丁时再按需追加。

    print('init-sources done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
