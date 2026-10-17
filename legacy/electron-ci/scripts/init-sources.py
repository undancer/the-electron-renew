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
    # 官方 electron（commit f2d1e5fa = v4.0.0）
    # —— 基线说明：v1.8.4（蓝本 electron-ci 子模块指定版本）依赖的
    #    vendor/libchromiumcontent 内部引用的 piotrbulinski/boto 已被 GitHub
    #    删除，递归子模块初始化失败；v4.0.0 起 electron 不再使用
    #    libchromiumcontent（chromium 经 DEPS/gclient 拉取），根 .gitmodules
    #    仅 vendor/requests、vendor/boto（官方 boto/boto），不受影响。
    #    git 迁出保留仓库子模块机制：递归 update 自动就位 .gitmodules 中
    #    锁定的版本，无需手动复制。
    pull('https://github.com/electron/electron',
         'f2d1e5fa9e72397e74222ee37e94d08ecd1e82ef', 'electron')

    # 注：yaml/pyyaml 目前**不迁出**——electron 默认编译链不需要；
    #     补丁解析（patches.py）对 yaml 为惰性引入，待需要补丁时再按需追加。

    print('init-sources done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
