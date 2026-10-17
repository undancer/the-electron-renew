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
- 结论：**本项目 electron-ci 迁出基线 = 官方 v4.0.0**。

> 版本锚定澄清：`v4.0.0` 是 annotated tag，其 tag 对象 sha 为
> `f2d1e5fa9e72397e74222ee37e94d08ecd1e82ef`，指向的真实 commit 为
> `005264ca1f92f920ff09c91c10a3d612ac94f1d7`（"Bump v4.0.0"，2018-12-20，
> Chromium 69.0.3497.106 / Node 10.11.0）。`git checkout f2d1e5fa` 与
> `git checkout v4.0.0` 等价；gclient 锁定用 commit sha（最稳）。

## v4.0.0 构建体系（与蓝本 v1.8.4 的根本差异）

**v4.0.0 的 electron 仓库 `script/` 下没有 `bootstrap.py` / `build.py` /
`create-dist.py`**（本地实证），构建已从 v1.8.4 时代的 python 脚本链切换到
**GN/gclient 体系**（官方 `docs/development/build-instructions-gn.md`）：

1. **获取代码**：`gclient config --name src/electron --unmanaged <url>` +
   `gclient sync --with_branch_heads --with_tags --revision src/electron@<commit>`
   ——按 electron 仓库 DEPS 拉取 chromium（约 30GB）、node、buildtools，
   并自动执行官方 hooks：应用官方 patches（`apply_all_patches.py`，官方
   patches 机制 v4.0.0 起存在）、`npm install`、外部二进制下载
   （`update-external-binaries.py`）；
2. **构建**：`gn gen out/Release --args=import("//electron/build/args/release.gn")`
   + `ninja -C out/Release electron`；
3. **产物**：`src/out/Release/electron`（Linux）/ `electron.exe`（Windows）——
   没有 zip（v4.0.0 无 create-dist.py，dist 组装在官方 release 流程）。

## 问题：2018 构建链需要 python2

- 蓝本脚本为 **python2** 时代产物（`print '...'` 语句，python3 直接 SyntaxError）；
- electron 源码内的 2018 构建脚本同样依赖 **python2**（DEPS hooks 调
  `python` 执行 `apply_all_patches.py` 等，均为 py2 脚本）；
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
4. **【2026-10-18 二版架构】electron-ci 定位 = electron 官方工具链的薄封装**：
   - 实际编译必须使用 electron 官方工具链本身（gclient / gn / ninja），
     我们的 ci 只负责把官方命令串起来 + 锁定版本 + 收集产物，用 py 写只是图方便；
   - **init.py**：装 depot_tools（clone 到 `depot_tools/`）→ `gclient config`
     → `gclient sync`（锁定 v4.0.0 commit，官方 hooks 自动完成补丁/npm/外部二进制）；
   - **build.py**：`cd gn-workspace/src` → `gn gen` → `ninja -C out/Release electron`；
   - 工作区 `gn-workspace/`（gclient 布局：`src/electron` 为可修改工作副本，
     chromium/node/buildtools 为 gclient 拉取的依赖，原样不动）。
   - 原 ijkplayer 式架构（`vendors/` + 复制 `electron/` 工作副本 +
     `scripts/{init-sources,fetch-sources,apply-patches,...}.py`）为
     v1.8.4 蓝本模式，**v4.0.0 下已不使用（deprecated）**，文件保留供
     参考，不再被 init/build 调用。

## 当前 electron-ci 结构（2026-10-18 二版：gclient 薄封装）

```
legacy/electron-ci/
├─ init.py                # 入口（python2）：depot_tools → gclient config → gclient sync
├─ build.py               # 编译驱动（python2）：gn gen → ninja（只调官方命令）
├─ clean.py               # 清理脚本（python2，旧版保留）
├─ depot_tools/           # gclient 宿主工具集（init.py clone，git 忽略，不入库）
├─ gn-workspace/          # gclient 工作区（git 忽略，CI 每次全新生成）
│  ├─ .gclient
│  └─ src/
│     ├─ electron/        # electron v4.0.0（--name src/electron；官方 patches 已应用）
│     └─ ...              # chromium 源码、node、buildtools（gclient 拉取，原样不动）
├─ vendors/               # 【deprecated】旧 ijkplayer 式下载区（仅本地考证用，git 忽略）
├─ electron/              # 【deprecated】旧工作副本（本地考证用，git 忽略）
├─ scripts/               # 【deprecated】旧脚本（init-sources/fetch-sources/
│                         #   apply-patches/patches/git），不再被调用，保留供参考
├─ patches/               # 补丁集（当前已清空为占位；官方 patches 由 DEPS hooks
│                         #   自动应用，本项目自定义补丁后续在此追加）
└─ README.md
```

**入口分工（顺序固定）**：`init.py` 准备（depot_tools + gclient sync）；
`build.py` 编译（gn gen + ninja），只调用官方命令，不实现任何构建逻辑。
**追加第三方源码**：v4.0.0 下由 gclient/DEPS 管理（官方机制），不再需要
手工清单。

**项目约束**：所有 py 脚本一律 `.py` 扩展名；含 `main()` 的脚本第一行
必须有 shebang（本项目 python2，统一 `#!/usr/bin/env python2`，并声明
`# -*- coding: utf-8 -*-`）；纯模块不要求 shebang。

## 2026 环境下重建 2018 编译的现实约束（实证）

- **python2 运行时**：GitHub Actions 已安装（linux: apt python2；
  windows: C:\Python27 msi），强制校验版本；**DEPS hooks 调 `python`，
  CI 必须把 python2 前置**（linux: `/usr/local/bin/python` 指向 python2 的
  shim；windows: `C:/Python27` 前置 PATH）；
- **磁盘（硬约束）**：GitHub 标准 runner 仅 **14GB**，chromium 源码约
  **30GB**、编译产物另需 20–60GB——**标准 runner 放不下**，gclient sync
  必然磁盘不足失败（这是"标准 runner 先试 init"验证法的预期失败点）；
  需换 **larger runner（150GB，付费）** 才能完整编译；
- **Windows 工具链**：v4.0.0（2018）要求 VS2017，windows-2022 是 VS2022，
  chromium 69 的 vs_toolchain 大概率不识别——windows 并行尝试，失败如实记录；
  `DEPOT_TOOLS_WIN_TOOLCHAIN=0` 必须设置（depot_tools 不得下载 Google 内部
  VS，无访问权限）；
- **时长**：全量编译可能接近或超过 Actions 6 小时上限（larger runner
  4 核亦紧张，官方 electron CI 使用自建集群）。

## 待办

- [x] Actions 试跑验证 init（切 v4.0.0 后 boto 删仓问题已消除）
- [x] 确认 v4.0.0 构建体系（script/ 无 bootstrap.py，构建 = gclient + gn + ninja）
- [ ] 标准 runner 试跑 init（gclient sync 预期因磁盘不足失败，验证脚本链前半段）
- [ ] 换 larger runner（150GB）后完整编译 v4.0.0（gn gen + ninja）
- [ ] 产物（src/out/Release/electron）经 workflow 上传 GitHub Releases（不进 git）
- [ ] 里程碑①通过后，组装为 `@chiflix/electron` 风格 npm 包的方案
