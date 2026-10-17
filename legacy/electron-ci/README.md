# electron-ci（本项目）

以 `ymmuse/electron-ci` 为蓝本、在 monorepo 内自建的 electron 编译驱动项目。
当前里程碑①：让**官方 electron v4.0.0 基线**通过本项目编译链完整打包
（产物进 GitHub Releases，不入 git）。

**定位（2026-10-18 二版架构）**：本项目只是 **electron 官方构建工具链
（depot_tools / gclient / gn / ninja）的薄封装**——实际编译必须使用
electron 官方工具链本身，用 python 写只是图方便，不实现任何构建逻辑。

> 基线说明：蓝本 electron-ci 原指定官方 v1.8.4（`9dfb85dd`），其依赖的
> `vendor/libchromiumcontent` 内部引用的 `piotrbulinski/boto` 已被 GitHub
> 删除，递归子模块初始化失败；v4.0.0 起 electron 不再使用
> libchromiumcontent（chromium 经 DEPS/gclient 拉取），根 `.gitmodules`
> 仅 `vendor/requests`、`vendor/boto`（官方 `boto/boto`），不受影响——
> 因此本项目基线定为 v4.0.0。
>
> 版本锚定：`v4.0.0` 是 annotated tag（tag 对象 `f2d1e5fa9…`），指向真实
> commit `005264ca1f92…`（"Bump v4.0.0"，2018-12-20，Chromium
> 69.0.3497.106 / Node 10.11.0）。gclient 锁定用 commit sha。

## Python 版本（重要）

- 蓝本脚本为 **python2** 时代产物（`print '...'` 语句等，python3 直接语法错误）；
- electron 源码内的 2018 构建脚本同样依赖 **python2**（DEPS hooks 调
  `python` 执行 `apply_all_patches.py` 等，均为 py2 脚本）；
- **uv 不支持 python2**（实测 `uv python install 2.7` / `3.7` 均报 No download
  found，仅支持 3.8+），因此本项目**不使用 uv**，由 GitHub Actions 安装
  python2 全程驱动；
- 本目录脚本均按 python2 兼容写法编写（`print('...')` 括号形式、
  无 encoding 参数等）。

## 本项目约束（脚本规范）

- **所有 py 脚本一律使用 `.py` 扩展名**；
- **含有 `main()` 的 py 脚本，第一行必须有 shebang 启动注释**
  （本项目为 python2，统一写 `#!/usr/bin/env python2`，避免系统默认
  python3 误用），确保可直接执行；py2 下含非 ASCII 内容须同时声明
  `# -*- coding: utf-8 -*-`；
- 纯被导入的模块不要求 shebang，但须为 `.py` 扩展名。

## 构建体系（v4.0.0 = GN/gclient，官方文档 build-instructions-gn.md）

**v4.0.0 的 electron 仓库 `script/` 下没有 `bootstrap.py` / `build.py` /
`create-dist.py`**（本地实证）——v1.8.4 时代的 python 脚本链在 v4.0.0 已
不存在，构建链路为：

```
# 1. init.py（前置准备，官方 hooks 自动完成补丁/npm/外部二进制）
depot_tools/gclient.py config --name src/electron --unmanaged https://github.com/electron/electron
depot_tools/gclient.py sync --with_branch_heads --with_tags --revision src/electron@005264ca1f...
   ├─ 拉取 chromium（~30GB）/ node / buildtools（原样不动）
   ├─ hook: apply_all_patches.py      （应用官方 patches，patches 机制 v4.0.0 起存在）
   ├─ hook: update-external-binaries.py（下载 electron-frameworks 外部二进制）
   └─ hook: npm install               （electron 的 npm 依赖）

# 2. build.py（编译，只调官方命令）
cd gn-workspace/src
gn gen out/Release --args=import("//electron/build/args/release.gn")
ninja -C out/Release electron
# 产物：gn-workspace/src/out/Release/electron（linux）/ electron.exe（windows）
```

## 入口分工（init.py 准备，build.py 编译）

- **`init.py`（python2）**：① clone depot_tools 到 `depot_tools/` 并前置
  PATH → ② `gclient config`（工作区 `gn-workspace/`，electron 落
  `src/electron`）→ ③ `gclient sync`（锁定 v4.0.0 commit，官方 hooks
  自动执行：应用官方 patches、npm install、外部二进制下载）；
  另有防御检查：`python` 必须解析到 python2（DEPS hooks 是 py2 脚本）。
- **`build.py`（python2）**：**只调官方命令**——`gn gen` → `ninja`，
  不实现任何构建逻辑，不下载、不操作任何子模块。

## 目录结构

```
legacy/electron-ci/
├─ init.py                 # 入口（python2）：depot_tools → gclient config → gclient sync（含 main）
├─ build.py                # 编译驱动（python2）：gn gen → ninja（含 main，只调官方命令）
├─ clean.py                # 清理脚本（python2，旧版保留）
├─ depot_tools/            # gclient 宿主工具集（init.py clone，git 忽略，不入库）
├─ gn-workspace/           # gclient 工作区（git 忽略，CI 每次全新生成）
│  ├─ .gclient
│  └─ src/
│     ├─ electron/         # electron v4.0.0（--name src/electron；官方 patches 已应用）
│     └─ ...               # chromium 源码、node、buildtools（gclient 拉取，原样不动）
├─ vendors/                # 【deprecated】旧 ijkplayer 式下载区（仅本地考证用，git 忽略）
├─ electron/               # 【deprecated】旧工作副本（本地考证用，git 忽略）
├─ scripts/                # 【deprecated】旧脚本（init-sources/fetch-sources/
│                          #   apply-patches/patches/git），不再被调用，保留供参考
├─ patches/                # 补丁集（当前已清空为占位；官方 patches 由 DEPS hooks
│                          #   自动应用，本项目自定义补丁后续在此追加）
└─ README.md
```

## 补丁机制（重要）

- **官方 patches**：v4.0.0 的构建体系里，官方补丁由 gclient 的 DEPS hook
  `apply_all_patches.py` **自动应用**（`patches/common/config.json` 定义
  各补丁目标目录）——这不是我们实现的，是官方工具链自带行为；
- **本项目自定义补丁**：后续里程碑在 `patches/` 下追加（当前已清空为占位）；
  应用方式待定（可复用官方 `git-import-patches` 机制或自定义 py 逻辑），
  顺序由 init.py 控制；
- 旧的 ijkplayer 式补丁机制（`scripts/apply-patches.py` + `.patches.yaml`）
  在 v4.0.0 下不再使用（deprecated，文件保留供参考）。

## 用法

```sh
# python2 运行（Actions 亦同）
python legacy/electron-ci/init.py                          # 前置：depot_tools + gclient sync（锁定 v4.0.0）
python legacy/electron-ci/build.py --target-arch x64        # 编译：gn gen + ninja
```

## 注意（2026 环境下重建 2018 编译的现实约束）

- **磁盘（硬约束）**：GitHub 标准 runner 仅 **14GB**，chromium 源码约
  **30GB**、编译产物另需 20–60GB——**标准 runner 放不下**（gclient sync
  必然磁盘不足失败）；需换 **larger runner（150GB，付费）** 才能完整编译；
- **python2 前置**：DEPS hooks 调 `python`（py2 脚本），CI 必须让 python2
  优先（linux: `/usr/local/bin/python` shim；windows: `C:/Python27` 前置）；
- **Windows 工具链**：v4.0.0（2018）要求 VS2017，windows-2022（VS2022）
  大概率不识别（chromium 69 vs_toolchain）；必须设
  `DEPOT_TOOLS_WIN_TOOLCHAIN=0`（depot_tools 不得下载 Google 内部 VS）；
- **时长**：全量编译可能接近或超过 GitHub Actions 6 小时上限；
- 产物为 `src/out/Release/electron(.exe)` 可执行文件（v4.0.0 无 zip dist，
  dist 组装在官方 release 流程），可进一步组装为 `@chiflix/electron`
  风格的 npm 包。
