#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Git helper functions.

Everything in here should be project agnostic, shouldn't rely on project's structure,
and make any assumptions about the passed arguments or calls outcomes.
"""

import os
import subprocess

def apply(repo, patch_path, reverse=False):
  # repo 是相对 electron-ci 根的目标仓库路径（如 electron/ 内子路径）。
  # git apply 必须在该目标仓库内执行：若在父仓库（monorepo 根）执行，
  # 子模块内部文件对父仓库不可见（目录为 gitlink），git 会报 Skipped 且
  # 返回 0，但补丁实际不会生效。
  target_dir = os.path.abspath(os.path.join(os.getcwd(), repo))

  # 目标仓库目录不存在（如嵌套子模块因网络未展开）→ 明确失败，不静默跳过
  if not os.path.isdir(target_dir):
    return False

  args = ['git', 'apply',
          '--ignore-space-change',
          '--ignore-whitespace',
          '--whitespace', 'fix'
          ]
  if reverse:
    args += ['--reverse']
  args += ['--', patch_path]

  return_code = subprocess.call(args, cwd=target_dir)
  applied_successfully = (return_code == 0)

  return applied_successfully
