# electron-ci 与 Python 版本决策

> 2026-10-18。目标：用 ymmuse/electron-ci 的全套流程跑通第三方 electron 打包。
> 里程碑①：**官方 electron v4.0.0 基线**通过本项目 electron-ci 完整编译打包。

## 背景

重建定制版 electron（ymmuse AVI 链：electron dev-ymmuse → electron-libcc
dev-ymmuse → electron-libcc-ffmpeg）的编译打包，以 `ymmuse/electron-ci`
为蓝本，在 `legacy/` 下新建我们自己的 `electron-ci` 项目驱动，源码全部
取自本仓库 `legacy/`（自包含，不依赖 ymmuse / electron 官方远程）。

## 基线（2026-10-18 定稿：v1.8.4 → v4.0.0）

- 蓝本 `ymmuse/electron-ci` 的 electron 子模块指定官方 **v1.8.4**
  （`9dfb85dd`）；本项目原沿用同版本；
- **v1.8.4 依赖的 `vendor/libchromiumcontent` 内部引用的
  `piotrbulinski/boto` 已被 GitHub 删除**，递归子模块初始化 clone 失败
  （CI 实测：`fatal: clone of 'https://github.com/piotrbulinski/boto.git' ... failed`）；
- **v4.0.0 起 electron 不再使用 libchromiumcontent**（chromium 经
  DEPS/gclient 拉取），根 `.gitmodules` 仅 `vendor/requests`
  （kennethreitz/requests）、`vendor/boto`（官方 `boto/boto`，存在）——
  不受删仓影响；
- 结论：**本项目 electron-ci 迁出基线 = 官方 v4.0.0（`f2d1e5fa9e72397e74222ee37e94d08ecd1e82ef`）**。

## 问题：2018 构建链需要 python2

- 蓝本脚本为 **python2** 时代产物（`print '...'` 语句，python3 直接 SyntaxError）；
- electron 源码内的 2018 构建脚本同样依赖 **python2**（`script/cibuild`
  使用 `os.environ.has_key` 等 python2-only 写法）；
- 无法用 python3 直接替换：语法与标准库差异大，且 electron 源码不能
  直接修改并持久化。

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
   `python legacy/electron-ci/init.py` + `python legacy/electron-ci/build.py --target-arch x64`；
4. **源码获取为 ijkplayer 式（git 迁出指定版本，不使用 git 子模块链接登记）**：
   - `scripts/fetch-sources.py` 为**通用拉取器**（仿 `pull-repo-base.sh`）：
     `python fetch-sources.py <url> <commit> <name>` 一次拉取一个仓库源码到
     `vendors/<name>/`——**git clone + checkout 锁定 commit + `git submodule
     update --init --recursive`**（保留仓库自身子模块机制）；
   - `scripts/init-sources.py` 为**源码清单**（仿 `init-android.sh`）：
     逐行调用 `fetch-sources.py` 拉取全部源码，**追加第三方仓库只需在
     清单按行加一条 `pull(...)`**；
   - **electron 用 git 迁出官方 `f2d1e5fa`（= v4.0.0）**：递归子模块自动
     就位 `vendor/requests`、`vendor/boto`（官方仓库）——无需手动复制；
     electron 源码内 `.gitmodules` 定义文件不删除、不修改；
   - pyyaml 由子模块改为 **git 迁出**（`fetch-sources.py` 拉 yaml/pyyaml
     b6cbfeec 到 `vendors/pyyaml/`，git 忽略，不入库）——**当前暂未迁出**
     （补丁机制为惰性引入，待需要补丁时按需追加）；
5. 补丁机制（`apply-patches.py` / `patches.py` / `git.py` / `patches/`）保留，
   **当前 `patches/` 已清空为占位**（尚未开始应用任何补丁）。

## 当前 electron-ci 结构（2026-10-18：vendors / scripts 复数规范）

```
legacy/electron-ci/
├─ init.py                # 入口（python2）：下载源码 → 复制工作副本 → 应用补丁 → 编辑编译参数
├─ build.py               # 编译驱动（python2）：bootstrap → build → dist（只负责编译链）
├─ clean.py               # 清理远程源码目录（python2）
├─ vendors/               # 第三方源码（git 迁出产物，git 忽略）
│  └─ electron/           #   git 迁出官方 f2d1e5fa（v4.0.0；递归子模块
│                         #   requests/boto；git 忽略，不入库）
├─ scripts/               # 构建脚本（全部 .py 扩展名；含 main() 者带 shebang）
│  ├─ init-sources.py     #   源码清单（仿 init-android.sh：逐行调 fetch-sources.py 拉全部）
│  ├─ fetch-sources.py    #   通用拉取器（仿 pull-repo-base.sh：git clone+checkout+递归子模块）
│  ├─ apply-patches.py    #   补丁应用入口（ci 自己的 py 逻辑）
│  ├─ patches.py          #   蓝本原样（模块，无 main；自动使用 vendors/pyyaml）
│  └─ git.py              #   蓝本原样（模块，无 main）
├─ patches/               # 补丁集（ci 自定义的全部补丁来源，当前已清空为占位）
└─ README.md
```

electron 源码经 **git 迁出**（官方 v4.0.0，而非 ymmuse 修改版），源码真实
落在 `vendors/electron/` 下并保留子模块机制。补丁应用过程
（`.patches.yaml` 的 repo 为相对 electron-ci 根的目标路径）由 ci 自己的
py 逻辑完成（`scripts/apply-patches.py`，细节外部不关心）。
**追加第三方源码仓库**：在 `scripts/init-sources.py` 按行追加一条
`pull('<url>', '<commit>', '<name>')` 即可，通用拉取器 `fetch-sources.py`
无需改动。

**入口分工（顺序固定）**：根目录 `init.py` 完成前置——①下载源码
（调 `scripts/init-sources.py`）②复制工作副本（`vendors/electron` → ci 根
`electron/`，base 保持原样）③应用补丁（调 `scripts/apply-patches.py`，
补丁 = `patches/common/*/.patches.yaml` 定义的全部补丁）④编辑编译参数
（**预留点位**，具体参数内容待定）；根目录 `build.py` 只负责编译链
（bootstrap → build → dist），不涉及任何子模块/第三方库复制。

**项目约束**：所有 py 脚本一律 `.py` 扩展名；含 `main()` 的脚本第一行
必须有 shebang（本项目 python2，统一 `#!/usr/bin/env python2`，并声明
`# -*- coding: utf-8 -*-`）；纯模块（git.py / patches.py）不要求 shebang。

## 2026 环境下重建 2018 编译的现实约束

- **python2 运行时**：GitHub Actions 已安装（linux: apt python2；windows:
  C:\Python27 msi），强制校验版本；
- **磁盘**：git 迁出 electron 全历史 + 递归子模块体积较大，v4.0.0 源码树
  （chromium 经 DEPS/gclient 拉取）约 20–30 GB，Actions runner 空间紧张；
- **工具链**：2018 构建基于 xcode9，现代 runner（xcode 15+）需逐项适配；
- **时长**：全量编译可能接近或超过 Actions 6 小时上限。

## 待办

- [ ] Actions 试跑验证 init（切 v4.0.0 后 boto 删仓问题已消除，预期 init 通过）
- [ ] v4.0.0 下 build.py bootstrap 调用链验证（官方 bootstrap 经 DEPS/gclient，
      与蓝本 v1.8.4 libcc 流程不同，需按真实卡点适配）
- [ ] 产物（electron dist）经 workflow 上传 GitHub Releases（不进 git）
- [ ] 里程碑①通过后，组装为 `@chiflix/electron` 风格 npm 包的方案
