# electron-ci（本项目）

以 `ymmuse/electron-ci` 为蓝本、在 monorepo 内自建的 electron 编译驱动项目。
当前里程碑①：让**官方 electron v4.0.0 基线**通过本项目编译链完整打包
（产物进 GitHub Releases，不入 git）。

> 基线说明：蓝本 electron-ci 原指定官方 v1.8.4（`9dfb85dd`），其依赖的
> `vendor/libchromiumcontent` 内部引用的 `piotrbulinski/boto` 已被 GitHub
> 删除，递归子模块初始化失败；v4.0.0 起 electron 不再使用
> libchromiumcontent（chromium 经 DEPS/gclient 拉取），根 `.gitmodules`
> 仅 `vendor/requests`、`vendor/boto`（官方 `boto/boto`），不受影响——
> 因此本项目基线定为 v4.0.0（commit `f2d1e5fa`）。

## Python 版本（重要）

- 蓝本脚本为 **python2** 时代产物（`print '...'` 语句等，python3 直接语法错误）；
- electron 源码内的 2018 构建脚本同样依赖 **python2**；
- **uv 不支持 python2**（实测 `uv python install 2.7` / `3.7` 均报 No download
  found，仅支持 3.8+），因此本项目**不使用 uv**，由 GitHub Actions 安装
  python2 全程驱动；
- 本目录脚本均按 python2 兼容写法编写（`print('...')` 括号形式、
  无 encoding 参数等）。

## 本项目约束（脚本规范）

- **所有 py 脚本一律使用 `.py` 扩展名**（含无参数入口脚本，如 `apply-patches.py`）；
- **含有 `main()` 的 py 脚本，第一行必须有 shebang 启动注释**
  （本项目为 python2，统一写 `#!/usr/bin/env python2`，避免系统默认
  python3 误用），确保可直接执行；py2 下含非 ASCII 内容须同时声明
  `# -*- coding: utf-8 -*-`；
- 纯被导入的模块（如 `git.py`、`patches.py`）不要求 shebang，但须为
  `.py` 扩展名。

## 源码获取（git 迁出指定版本，不使用 git 子模块链接登记）

参考 bilibili/ijkplayer 的做法，本项目**不把源码登记为 git 子模块**，
而是由脚本 **git 迁出**（clone → checkout 锁定 commit → 递归子模块）
到指定位置：

1. **`scripts/fetch-sources.py`（通用拉取器，仿 `pull-repo-base.sh`）**：
   `python fetch-sources.py <url> <commit> <name>` 一次拉取一个仓库源码到
   `vendors/<name>/`——**git clone + checkout 指定 commit + `git submodule
   update --init --recursive`**（保留仓库自身子模块机制，子模块按其
   `.gitmodules` 锁定的版本就位）；
   `scripts/init-sources.py`（清单，仿 `init-android.sh`）逐行调用它拉取
   全部所需源码，**追加第三方仓库只需在 `init-sources.py` 按行加一条
   `pull(...)`，不改拉取器本身**；
2. **electron 用 git 迁出官方 `f2d1e5fa`（= v4.0.0）**：递归子模块自动
   就位根 `.gitmodules` 锁定的 `vendor/requests`、`vendor/boto`
   （官方 `boto/boto`）——无需手动复制。

源码均经 git 迁出（electron 官方），产物 git 忽略不入库；构建不依赖任何
git 子模块接线（源码内 `.gitmodules` 定义文件不删除、不修改）。

## 入口分工（init.py 准备，build.py 编译）

- **`init.py`（根目录，python2）**：完成编译前全部前置，顺序固定——
  1) **下载源码**（调 `scripts/init-sources.py` 清单，git 迁出 electron）；
  2) **复制工作副本**（`vendors/electron` 整体复制为 ci 根目录下 `electron/`，
     含 `.git` 与已就位子模块；base 保持原样，后续修改都在副本上）；
  3) **应用补丁**（调 `scripts/apply-patches.py`，ci 自己的 py 逻辑读
     `patches/common/*/.patches.yaml` 定义的补丁并 git apply——**细节由
     补丁机制自己完成，外部不关心**）；
  4) **编辑编译参数**（**预留点位**——具体参数内容待定，仅保留动作位置，
     不预设任何参数）；
- **`build.py`（根目录，python2）**：**只负责编译链**（bootstrap → build →
  dist），不下载、不操作任何 git 子模块。

## 源码接线

| 角色 | 位置 | 获取方式 |
| --- | --- | --- |
| electron 源码（构建主体） | `vendors/electron/` | `init-sources.py` 清单调 `fetch-sources.py` git 迁出官方 f2d1e5fa（v4.0.0，递归子模块 requests/boto，git 忽略） |
| 官方 boto / requests | `vendors/electron/vendor/boto`、`vendor/requests` | electron 递归子模块（官方 boto/boto、kennethreitz/requests，按 electron .gitmodules 锁定版本） |
| 遗留参考源码 | `../ymmuse-electron-libcc-ffmpeg-feature-electron-avi` | 遗留目录，仅供阅读参考（不参与构建） |

## 构建链

```
# 1. 前置准备（下载源码 → 复制工作副本 → 应用补丁 → 编辑编译参数，顺序固定）
python legacy/electron-ci/init.py
# 2. 编译（build.py 只负责编译链）
python legacy/electron-ci/build.py --target-arch x64
  ├─ 1. electron/script/bootstrap.py --target_arch=x64 -v   （官方脚本，DEPS/gclient 就位依赖）
  ├─ 2. electron/script/build.py -c R
  └─ 3. electron/script/create-dist.py                       （产物在 electron/dist）
```

## 补丁机制（重要）

- **应用补丁 = ci 自己的 py 逻辑**（`scripts/apply-patches.py` 读
  `patches/common/*/.patches.yaml` 定义的补丁并 git apply，细节由补丁机制
  自己完成，外部不关心）；`patches/` 下定义的补丁即全部补丁来源；
- 当前 `patches/` 已**清空为占位**（尚未开始应用任何补丁）；
- `.patches.yaml` 的 `repo` 为相对 electron-ci 根的目标路径。
- 依赖：`apply-patches.py` / `patches.py` 需要 **pyyaml**，由 `vendors/pyyaml`
  提供（`patches.py` 自动把 `vendors/pyyaml/lib` 加入 `sys.path`；
  经 `fetch-sources.py` git 迁出 yaml/pyyaml b6cbfeec，git 忽略——
  当前暂未迁出，补丁机制为惰性引入，待需要补丁时按需追加）。

## 目录结构

```
legacy/electron-ci/
├─ init.py                 # 入口：下载源码 → 复制工作副本 → 应用补丁 → 编辑编译参数（含 main，python2）
├─ build.py                # 编译驱动：bootstrap → build → dist（含 main，python2；只负责编译链）
├─ clean.py                # 清理远程源码目录（含 main，python2）
├─ vendors/                # 第三方源码（复数规范，git 迁出产物）
│  └─ electron/            #   git 迁出官方 f2d1e5fa（v4.0.0；递归子模块 requests/boto；git 忽略）
├─ scripts/                # 构建脚本（全部 .py 扩展名，复数规范）
│  ├─ init-sources.py      #   源码清单（仿 init-android.sh：逐行调 fetch-sources.py 拉全部，含 main）
│  ├─ fetch-sources.py     #   通用拉取器（仿 pull-repo-base.sh：git clone+checkout+递归子模块，含 main）
│  ├─ apply-patches.py     #   补丁应用入口（ci 自己的 py 逻辑；含 main，shebang 启动）
│  ├─ patches.py           #   补丁列表解析（模块，无 main）
│  └─ git.py               #   git apply 封装（模块，无 main）
├─ patches/                # 补丁集（ci 自定义的全部补丁来源，当前已清空为占位）
└─ README.md
```

## 用法

```sh
# python2 运行（Actions 亦同）
python legacy/electron-ci/init.py                          # 前置：下载源码 → 复制副本 → 应用补丁 → 编辑编译参数
python legacy/electron-ci/build.py --target-arch x64        # 编译

# 通用拉取器：一次拉一个仓库（仿 pull-repo-base.sh，由 init-sources.py 调用）
python legacy/electron-ci/scripts/fetch-sources.py <url> <commit> <name>
```

## 注意（2026 环境下重建 2018 编译的现实约束）

- **磁盘**：git 迁出 electron 全历史 + 递归子模块体积较大，v4.0.0
  源码树（chromium 经 DEPS/gclient 拉取）约 20–30 GB，Actions runner
  空间紧张；
- **工具链**：2018 构建基于 xcode9 / python2，现代 runner（xcode 15+）
  大概率需要适配（clang/SDK 层面报错需逐一处理）；
- **时长**：全量编译可能接近或超过 GitHub Actions 6 小时上限；
- 产物为完整 electron dist，可进一步组装为 `@chiflix/electron` 风格的
  npm 包。
