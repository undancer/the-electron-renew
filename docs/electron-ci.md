# electron-ci 与 Python 版本决策

> 2026-10-17。目标：用 ymmuse/electron-ci 的全套流程跑通完整第三方 electron 打包。

## 背景

重建定制版 electron（ymmuse AVI 链：electron dev-ymmuse → electron-libcc dev-ymmuse
→ electron-libcc-ffmpeg）的编译打包，以 `ymmuse/electron-ci` 为蓝本，
在 `legacy/` 下新建我们自己的 `electron-ci` 项目驱动，源码全部取自本仓库
`legacy/`（自包含，不依赖 ymmuse / electron 官方远程）。

## 问题：2018 构建链需要 python2

- 蓝本脚本为 **python2** 时代产物（`build.py` 内 `print '...'` 语句，python3 直接 SyntaxError）；
- electron/libcc 源码内的 2018 构建脚本同样依赖 **python2**：
  - libcc `script/update` 使用 `urllib2`（python2-only）；
  - electron `script/cibuild` 使用 `os.environ.has_key`（python2-only）。
- 无法用 python3 直接替换：语法与标准库差异大，且 electron/libcc 是我们
  legacy 下的子模块（源码不能直接修改并持久化）。

## 验证：uv 不支持 python2

实测（uv 0.11.12）：

```
uv python install 2.7   → error: No download found for cpython-2.7-windows-x86_64-none
uv python install 3.7   → error: No download found for cpython-3.7-windows-x86_64-none
uv python list          → 可用版本从 3.8/3.9 起
```

结论：**uv 仅支持 Python 3.8+，无法提供 python2**（python2 已于 2020 EOL）。

## 决策

1. **暂时移除 uv 特性**：根 `pyproject.toml`、`uv.lock`、`.venv`、
   `legacy/electron-ci/pyproject.toml` 全部移除（提交 2026-10-17）；
2. **electron-ci 重写为 python2 兼容**：以 ymmuse/electron-ci 为蓝本，
   脚本采用 py2 兼容写法（`print('...')` 括号形式、open 不带 encoding 参数等）；
3. **GitHub Actions 用 python2 全程驱动**：
   `python legacy/electron-ci/scripts/build.py --target-arch x64`；
4. **源码获取改为 ijkplayer 式（git 迁出指定版本，不使用 git 子模块链接登记）**：
   - `scripts/fetch-sources.py` 为**通用拉取器**（仿 `pull-repo-base.sh`）：
     `python fetch-sources.py <url> <commit> <name>` 一次拉取一个仓库源码到
     `vendors/<name>/`——**git clone + checkout 锁定 commit + `git submodule
     update --init --recursive`**（保留仓库自身子模块机制）；
   - `scripts/init-sources.py` 为**源码清单**（仿 `init-android.sh`）：
     逐行调用 `fetch-sources.py` 拉取全部源码（electron + pyyaml），
     **追加第三方仓库只需在清单按行加一条 `pull(...)`**；
   - **electron 用 git 迁出官方 `9dfb85dd`（= v1.8.4，蓝本 electron 子模块
     指定版本，Chromium 63）**：递归子模块自动就位**官方 libcc**
     （`electron/libchromiumcontent` → `vendors/electron/vendor/libchromiumcontent`）
     与 node、depot_tools 等——**无需手动复制 libcc**（回归蓝本行为；
     electron 源码内 `.gitmodules` 定义文件不删除、不修改）；
   - pyyaml 由子模块改为 **git 迁出**（`fetch-sources.py` 拉 yaml/pyyaml
     b6cbfeec 到 `vendors/pyyaml/`，git 忽略，不入库）；
5. 蓝本补丁机制（`apply-patches.py` / `patches.py` / `git.py` / `patches/`）保留，
   **AVI 注入 = `apply-patches`**（蓝本意图路径：`avi_format0001.patch` 改官方
   libcc 的 ffmpeg.gn + ffmpeg AVI 补丁），`--apply-patches` 显式执行。

## 当前 electron-ci 结构（2026-10-17 重建：vendors / scripts 复数规范）

```
legacy/electron-ci/
├─ vendors/          # 第三方源码（git 迁出产物）
│  ├─ electron/      #   git 迁出官方 9dfb85dd（含递归子模块：官方 libcc 等；
│  │                 #   v1.8.4，蓝本指定版本，Chromium 63；git 忽略，不入库）
│  └─ pyyaml/        #   git 迁出（yaml/pyyaml b6cbfeec，git 忽略）
├─ scripts/          # 构建脚本（全部 .py 扩展名；含 main() 者带 shebang）
│  ├─ build.py       #   驱动脚本：apply-patches → bootstrap → build → dist（不负责源码获取）
│  ├─ init-sources.py   # 源码清单（仿 init-android.sh：逐行调 fetch-sources.py 拉全部）
│  ├─ fetch-sources.py  # 通用拉取器（仿 pull-repo-base.sh：git clone+checkout+递归子模块）
│  ├─ apply-patches.py  # 补丁应用入口（AVI 注入路径，--apply-patches）
│  ├─ patches.py     #   蓝本原样（模块，无 main；自动使用 vendors/pyyaml）
│  └─ git.py         #   蓝本原样（模块，无 main）
├─ patches/          # 蓝本补丁集（ffmpeg AVI / libcc gn），路径不改（electron/vendor/...）
└─ README.md
```

electron 源码经 **git 迁出**（**完全参考蓝本指定的版本**：官方 electron @ 9dfb85dd，
而非 ymmuse 修改版），源码真实落在 `vendors/electron/` 下并保留子模块机制，
官方 libcc 自动就位于 `vendors/electron/vendor/libchromiumcontent`，
补丁应用过程（`.patches.yaml` 的 repo 为相对 electron-ci 根的目标路径，
本项目为 `vendors/electron/vendor/libchromiumcontent/...`）由 ci 自己的
py 逻辑完成（`scripts/apply-patches.py`，细节外部不关心）。
**追加第三方源码仓库**：在 `scripts/init-sources.py` 按行追加一条
`pull('<url>', '<commit>', '<name>')` 即可，通用拉取器 `fetch-sources.py` 无需改动。

**入口分工（顺序固定）**：根目录 `init.py` 完成前置——①下载源码
（调 `scripts/init-sources.py`）②应用补丁（调 `scripts/apply-patches.py`，
补丁 = `patches/common/*/.patches.yaml` 定义的全部补丁）③编辑编译参数
（**预留点位**，具体参数内容待定）；根目录 `build.py` 只负责编译链
（bootstrap → build → dist）。

**项目约束**：所有 py 脚本一律 `.py` 扩展名；含 `main()` 的脚本第一行
必须有 shebang（本项目 python2，统一 `#!/usr/bin/env python2`，并声明
`# -*- coding: utf-8 -*-`）；纯模块（git.py / patches.py）不要求 shebang。

## 2026 环境下重建 2018 编译的现实约束

- **python2 运行时**：macOS runner 是否自带 / 可安装 python2 需试跑确认；
- **磁盘**：Chromium 63 源码树约 20–30 GB，Actions macOS runner 空间紧张；
- **工具链**：2018 构建基于 xcode9，现代 runner（xcode 15+）需逐项适配；
- **时长**：全量编译可能接近或超过 Actions 6 小时上限。

## 待办

- [ ] Actions 触发 `Build custom electron (ymmuse chain)` 试跑，按真实卡点迭代
- [ ] 若 python2 在 runner 缺失，确定安装途径（brew / 自编译 / 自带 tarball）
- [ ] 产物（electron dist）组装为 `@chiflix/electron` 风格 npm 包的方案
