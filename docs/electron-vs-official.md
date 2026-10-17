# ymmuse/electron（dev-ymmuse）与官方 electron 的差异

> 更新：2026-10-17。目的：精确记录"他的 electron"相对官方改了什么，
> 支撑 SPlayerX 4.9.4 定制版 electron 重建。

## 对比对象

| 角色 | 仓库 | commit | 说明 |
| --- | --- | --- | --- |
| 官方基线 | electron/electron | `6fc819dae`（master @ 2018-04-10，"Fix transparency in capturePage (#12561)"，Chromium 63 / Node 9.7.0，v2.0.0 前身） | dev-ymmuse fork 的基线 |
| ymmuse 定制 | ymmuse/electron | `57cd9d9`（dev-ymmuse 分支 HEAD） | 官方基线 + ymmuse 独有提交 |

对比方法：本地树级对比（`git ls-tree -r`）两个 commit 的全部 1403 条目。

## 总览：仅 5 项不同，electron 本体源码零改动

- 两树条目数：官方 1403 = ymmuse 1403（**无增删文件**）；
- 共同路径 1403 中**内容不同仅 5 项**，其余 1398 完全相同；
- 结论：**atom/、brightray/、lib/、script/、spec/ 等 electron 本体源码零改动**，
  定制内容全部通过 libcc 与 CI/文档层面注入。

| 差异项 | 官方 `6fc819dae` | ymmuse `57cd9d9` |
| --- | --- | --- |
| `.gitmodules` | libcc 子模块 → `electron/libchromiumcontent` | → **`ymmuse/electron-libcc.git`** + `branch = dev-ymmuse` |
| `.travis.yml` | linux+osx / xcode7.3 / master 分支 | **仅 osx x64** / xcode9 / 缓存 libcc src / `dev-ymmuse` 分支 |
| `README.md` | 官方原文 | 开头加 "# README First!"，指向 ymmuse wiki "About This Electron" |
| `script/cibuild` | 默认 bootstrap | 显式 `-v`、debug/release 时加 `--build_debug_libcc` / `--build_release_libcc` |
| `vendor/libchromiumcontent`（gitlink） | 官方 `f1fc5cfb` | **ymmuse 定制版 `364cf9c6`** |

## 逐项差异明细

### 1. `.gitmodules`（libcc 指向定制版）

```diff
 [submodule "vendor/libchromiumcontent"]
 	path = vendor/libchromiumcontent
-	url = https://github.com/electron/libchromiumcontent
+	url = https://github.com/ymmuse/electron-libcc.git
+	branch = dev-ymmuse
```

意义：electron 的 libcc 由官方改为 ymmuse fork（`dev-ymmuse`），
AVI 解码支持、proprietary codecs 等定制全部落在这个 libcc（`364cf9c6`）里。

### 2. `.travis.yml`（CI 只跑 macOS x64）

```diff
 os:
-  - linux
   - osx
-osx_image: xcode7.3
+osx_image: xcode9
+cache:
+  directories:
+    - vendor/libchromiumcontent/src/
 matrix:
   include:
-    - os: linux / TARGET_ARCH=arm
-    - os: linux / TARGET_ARCH=ia32
-    - os: linux / TARGET_ARCH=arm64
+    - os: osx / TARGET_ARCH=x64
 branches:
   only:
-    - master
+    - dev-ymmuse
```

意义：ymmuse 的 CI 仅 macOS x64（xcode9），缓存 libcc 源码树；只构建 dev-ymmuse 分支。

### 3. `README.md`（指向定制说明）

```diff
+﻿# README First!
+## I think you are looking for this What Is About This Electron!
+[链接](https://github.com/ymmuse/electron/wiki/About-This-Electron)
 [![Electron Logo](...)](https://electronjs.org)
```

意义：README 指向 ymmuse wiki 的 "About This Electron" 页面（定制内容说明）。

### 4. `script/cibuild`（显式 libcc 构建模式）

```diff
   args = ['--target_arch=' + target_arch]
+  args += ['-v']
   if not is_release:
     args += ['--dev']
+    args += ['--build_debug_libcc']
+  else:
+    args += ['--build_release_libcc']
   run_script('bootstrap.py', args)
```

意义：CI 显式驱动 debug/release 的 libcc 构建（含 libcc 的 bootstrap/update/build/create-dist 全链）。

### 5. `vendor/libchromiumcontent`（gitlink）

- 官方 `f1fc5cfb`（官方 libcc）→ ymmuse `364cf9c6`（dev-ymmuse，Chromium 63 / VERSION 63.0.3239.150，
  **`chromiumcontent/args/ffmpeg.gn` 已内置 `proprietary_codecs = true` + `ffmpeg_branding = "Chrome"`**，
  仓库内自带 `patches/common/ffmpeg/github-ymmuse-feature-avi.patch` 等）。

## 提交级证据

- dev-ymmuse 相对官方基线有 9 个 ymmuse 独有提交（GitHub 提交页可见，如
  `0fc5774` "Assigned to avi feature"、`9f06f38` "fix compiler error" 等，
  均发生在 2018-04-10 ~ 04-19）；
- 类别：4 个 `vendor/libchromiumcontent` gitlink/URL 调整、4 个 CI 配置
  （`.travis.yml` / `script/cibuild` 等）、1 个 README——与上述树级差异完全吻合；
- **electron 本体源码（C++/JS 构建链）零改动**。

## 重要背景：蓝本 electron-ci 用的是官方 v1.8.4（9dfb85dd）

- 蓝本 `ymmuse/electron-ci` 的 electron 子模块 = 官方 `9dfb85dd`（**v1.8.4 tag，2018-01**），
  不是 dev-ymmuse 基线 `6fc819dae`（2018-04-10），两者差约 3 个月官方演进
  （树对比：534 个文件不同，均为官方自身变化）；
- 即：**蓝本 CI（官方 1.8.4 源码 + electron-ci/patches 补丁）与 dev-ymmuse 线
  （官方 2018-04 master 源码 + 定制 libcc 364cf9c6）是两条不同时间点的构建路线**；
- 本项目两路都保留：`electron-ci`（蓝本同构，官方 9dfb85dd + 补丁）与
  `ymmuse-electron-dev-ymmuse`（dev-ymmuse 57cd9d9 + 定制 libcc），
  由两个独立 GitHub Actions workflow 分别打包。

## 结论

ymmuse/electron（dev-ymmuse）相对官方只改了：
1. **libcc 指向定制版**（gitlink + URL，`364cf9c6`：AVI 解码 + proprietary codecs）；
2. CI 配置（仅 macOS x64、xcode9、dev-ymmuse 分支、显式 libcc 构建模式）；
3. README 指向定制说明 wiki。

electron 本体代码与官方 `6fc819dae` 完全一致——**"定制版 electron"的实质
是"官方 electron + 定制 libchromiumcontent"**。
