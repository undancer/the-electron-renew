#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""清空本地生成物：vendors/（下载的第三方源码 base）与 electron/（工作副本）。

这两个目录均由脚本生成且被 .gitignore 忽略（不入版本库）：
  vendors/   init-sources.py 下载的第三方源码（git 迁出锁定版本 + 子模块 + LFS）
  electron/  init.py 从 vendors/electron 复制的工作副本（补丁/参数/编译载体）

删除后可重新运行 init.py 完整重建；clean 只清理本地目录，不动版本库。

用法（python2 运行，Actions 亦同）：
  python legacy/electron-ci/clean.py
"""

import os
import shutil
import sys
import time

ROOT = os.path.abspath(os.path.dirname(__file__))
# 待清理的本地生成物目录（相对 electron-ci 根）
TARGETS = ['vendors', 'electron']
# Windows 上文件可能被杀软/索引瞬时占用，rmtree 失败时按此重试
RETRIES = 5
RETRY_DELAY_SECONDS = 5


def rmtree_with_retry(path):
    """删除目录；被占用（WindowsError/OSError）时重试，避免中途中断。"""
    for attempt in range(1, RETRIES + 1):
        try:
            shutil.rmtree(path)
            return True
        except (OSError, WindowsError) as e:
            print('retry %d/%d: %s' % (attempt, RETRIES, e))
            time.sleep(RETRY_DELAY_SECONDS)
    return False


def main():
    for name in TARGETS:
        path = os.path.join(ROOT, name)
        if os.path.isdir(path):
            if rmtree_with_retry(path):
                print('%s/ cleaned' % name)
            else:
                print('%s/ cleanup FAILED after %d retries' % (name, RETRIES))
                return 1
        else:
            print('%s/ not present, skip' % name)
    print('clean done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
