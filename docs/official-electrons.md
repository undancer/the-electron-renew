# 本项目中的官方 electron：版本盘点、相互定位与 patches 机制考证

> 更新：2026-10-18（electron-ci 基线 v1.8.4 → v4.0.0）。目标：把本项目内所有官方 electron 精确锚定到官方 tag/分支
> （含旧日 master），并考证官方 `patches/` 目录从哪个版本开始支持。
> 依据全部来自本地仓库对象（`git describe`、`ls-tree`、`DEPS`）与官方 release 页。

## 一、盘点总览（5 处官方 electron）

| 位置 | 官方身份（git describe 精确锚定） | gitlink / HEAD | 存在形式 |
| --- | --- | --- | --- |
| `legacy/electron-electron-main` | **v46.0.0-nightly.20261016 之后 6 提交**（官方 main 当前 HEAD，已滚动到 46 系列） | `baccc3ffd` | 子模块，已迁出（--depth 1） |
| `legacy/electron-electron-v7.3.3` | **v7.3.3**（精确命中 tag） | `3f2d5c217` | 子模块，已迁出（--depth 1） |
| `legacy/electron-ci/vendors/electron` | **v4.0.0**（精确命中 tag；2026-10-18 由 v1.8.4 `9dfb85dd` 切换而来，规避 boto 删仓） | `f2d1e5fa` | fetch-sources.py git 迁出（本项目 electron-ci 基线，git 忽略不入库；蓝本原指定 v1.8.4） |
| `legacy/ymmuse-electron-ci-develop/electron` | **v1.8.4**（同 commit `9dfb85dd`） | `9dfb85dd` | 蓝本 electron-ci 自带的子模块定义（并入登记，未迁出） |
| 本地对象（electron-ci/vendors/electron 曾克隆对象库） | 官方 **master @ 2018-04-10 = v1.8.2-beta.3 之后 1315 提交**（2.0.0 开发线） | `6fc819dae` | 仅对象持有（非正式子模块），dev-ymmuse fork 基线 |

## 二、版本锚定与内核对照

| 官方身份 | commit | 时间 | Chromium | Node.js | V8 |
| --- | --- | --- | --- | --- | --- |
| main（= v46.0.0-nightly.20261016-6） | `baccc3ffd` | 2026-10-16 | 158.0.8105.0 | v24.22.0 | — |
| v7.3.3 | `3f2d5c217` | 2020-08-25 | 78.0.3904.130 | v12.8.1 | 7.8.279.23 |
| v4.0.0（electron-ci 基线，2026-10-18 切换） | `f2d1e5fa` | 2018-10-17 | 69.0.3497.106（DEPS 实证） | 10.11.0（官方 release） | — |
| v1.8.4 | `9dfb85dd` | 2018-03-17（release） | 59.0.3071.115 | 8.2.1 | 5.9.211.38 |
| 2018-04-10 master（= v1.8.2-beta.3 + 1315） | `6fc819dae` | 2018-04-10 | 63.0.3239.x（Chromium 63） | 9.7.0 | — |

来源：DEPS（main/v7.3.3）、官方 release 页 v1.8.4/v7.3.3、electron-vs-official.md（6fc819dae 内核取自 libcc VERSION）。

## 二点五、受 `piotrbulinski/boto` 删仓影响的版本区间（2026-10-18 实证）

背景：electron 1.x–3.x 的 `vendor/libchromiumcontent` 子模块内部又登记了
`vendor/boto` 子模块；其中一段时期的 URL 指向 `piotrbulinski/boto.git`，
该仓库现已被 GitHub 删除 → 递归子模块初始化 clone 失败
（本项目 CI 实测：v1.8.4 全量迁出失败）。

扫描方法：本地 vendored electron（全量 tag 120 个含 libchromiumcontent）逐 tag
取 libcc gitlink sha → 在 electron/libchromiumcontent 全量历史中 `git show <sha>:.gitmodules`
读取 boto URL（本表逐一实证，非推断）。

| 区间 | libcc 内 boto URL | 受影响 |
| --- | --- | --- |
| v1.7.x 及更早（v1.7.1–v1.7.16 实证） | `https://github.com/boto/boto`（官方） | **否** |
| v1.8.0 / v1.8.1 / v1.8.2-beta.1 | 官方 boto/boto | **否** |
| **v1.8.2-beta.2 起（1-8-x 全线：v1.8.2 正式 ~ v1.8.8）** | **`https://github.com/piotrbulinski/boto.git`（已删除）** | **是** |
| **v2.0.x 全系（beta.1 ~ v2.0.18，含 2.1.0-unsupported）** | **piotrbulinski/boto.git（已删除）** | **是** |
| **v3.0.x / v3.1.x 全系（beta ~ 正式）** | **piotrbulinski/boto.git（已删除）** | **是** |
| **v4.0.0-nightly.20180816 ~ 20180905（早期 4.0 nightly 仍带 libcc）** | **piotrbulinski/boto.git（已删除）** | **是** |
| v4.0.0 正式版（`f2d1e5fa`）及之后 | 无 libcc 子模块（chromium 经 DEPS/gclient；根 .gitmodules 的 boto = 官方 boto/boto） | **否** |

结论：
- **受影响窗口 = v1.8.2-beta.2 → v3.1.13（含 v4.0.0 早期 nightly 2018-08~09）**；
- **本项目 electron-ci 基线切 v4.0.0 正式版（`f2d1e5fa`）即完全脱离受影响窗口**；
- 若日后需编译 v1.8.2-beta.2 ~ v3.1.x 区间版本，必须先把 libcc 的 boto URL
  重定向到可用仓库（如官方 boto/boto 或自建镜像）再迁出。

## 三、按时间顺序排序（含 v2.0.0）

按提交时间先后排列；**官方正式版本之间不标注提交差**，仅对项目引用的两个对象
（v1.8.4 = 蓝本 CI 基线、2018-04-10 master = dev-ymmuse 基线）描述"距离 v2.0.0 还差几次提交"：

> **里程碑 ①：v7.3.3** —— 本项目重建链的**第一个里程碑**：以官方 **v7.3.3**
> （`3f2d5c217`，Chromium 78 / Node 12.8.1 / V8 7.8）为基线，配合 ymmuse 定制补丁，
> **复刻还原出 SPlayerX 实际依赖的第三方打包 electron**（`@chiflix/electron@7.3.3`，
> chiflix/electron 无源码，由 ymmuse 系 fork 承载改动）。表中以 ⭐ 重点标记。

| 顺序 | 版本/对象 | commit | 提交时间 | 内置 Node | 浏览器引擎（Chromium） | 与 v2.0.0 的关系 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | v1.8.4（蓝本 CI 源码基线，1-8-x 线；工具：Yarn1 使用区 / pnpm3 段口径） | `9dfb85dd` | 2018-03-16 | 8.2.1 | 59.0.3071.115 | 距 v2.0.0 还差 **974** 提交 |
| 2 | 2018-04-10 master（dev-ymmuse 基线，主干，= v1.8.2-beta.3+1315） | `6fc819dae` | 2018-04-10 | 9.7.0 | 63.0.3239 | 距 v2.0.0 还差 **101** 提交 |
| 3 | **v2.0.0**（主干口径首个正式版，2018-05-01；工具：pnpm3 段口径） | `6b90807cb8` | 2018-05-01 | 8.9.3 | 61.0.3163.100 | — |
| 4 | **v3.0.0**（内置 Node 10 段起点；Node 10 LTS 起始；工具：pnpm4/5 段口径） | `34c202518d` | 2018-09-18 | 10.2.0 | 66.0.3359.181 | 官方版本 |
| 5 | **v4.0.0**（首次支持 `patches/` 的版本） | `005264ca1f` | 2018-12-20 | 10.11.0 | 69.0.3497.106 | 官方版本 |
| 6 | **v5.0.0**（内置 Node 12 段起点；Node 12 LTS 起始；工具：pnpm4/5 严格首匹配） | `7514372e79` | 2019-04-24 | 12.0.0 | 73.0.3683.119 | 官方版本 |
| 7 | **v4.2.12**（4.x 系列最终版；内置 Node 10 段终点；Vue 3 下限 Node>=10 对应；工具：Yarn2 下限 / pnpm4/5 段口径） | `3e0e966662` | 2019-10-16 | 10.11.0 | 69.0.3497.106 | 官方版本 |
| 8 | ⭐ **v7.3.3**（**里程碑 ①：复刻还原第三方打包 electron 的目标基线**；7-3-x 维护线；**7.x 系列最终版**，无 7.4.x） | `3f2d5c217` | 2020-08-25 | 12.8.1 | 78.0.3904.130 | 官方版本 |
| 9 | **v8.5.5**（8.x 系列最终版） | `78a4a48f6f` | 2020-11-18 | 12.13.0 | 80.0.3987.163 | 官方版本 |
| 10 | **v12.0.0**（Vite 2.0（2021-02-16，Vue 官方推荐工具链 webpack→vite 切换点）后首个 electron major；内置 Node 14 段起点；工具：TS5.0 首匹配 / pnpm7 严格首匹配） | `3ae63c9a06` | 2021-03-02 | 14.16.0 | 89.0.4389.69 | 官方版本 |
| 11 | **v11.5.0**（内置 Node 12 段终点；对应项目 `engines.node ^12` / vue 2.6 工具链；工具：Yarn1 使用区 / pnpm6 段终点） | `3d0705d81f` | 2021-08-31 | 12.18.3 | 87.0.4280.141 | 官方版本 |
| 12 | **v15.0.0**（内置 Node 16 段起点；Node 16 LTS 起始） | `c3e6746fa9` | 2021-09-21 | 16.5.0 | 94.0.4606.51 | 官方版本 |
| 13 | **v16.0.0**（内置 Node 16.9.1；工具：Corepack 首匹配（Node 16.9.0 首次内置后首个 electron）） | `dae224619f` | 2021-11-16 | 16.9.1 | 96.0.4664.45 | 官方版本 |
| 14 | **v14.2.9**（内置 Node 14 段终点；Node 14 LTS 截止；工具：pnpm7 段终点 / TS5.1+ 首匹配） | `37a7155bd8` | 2022-03-30 | 14.17.0 | 93.0.4577.82 | 官方版本 |
| 15 | **v19.0.0**（首个要求 Python 3 的版本；工具：pnpm8 首匹配） | `42266d2bf0` | 2022-05-31 | 16.14.2 | 102.0.5005.61 | 官方版本 |
| 16 | **v22.0.0**（Electron Forge 6（2022-11-03，官方推荐打包工具 packager/builder→Forge 变更点）后首个 electron major；22.x 线首发） | `71941e720e` | 2022-11-29 | 16.17.1 | 108.0.5359.62 | 官方版本 |
| 17 | **v23.0.0**（内置 Node 18 段起点；Node 18 LTS 起始；工具：pnpm9/10 首匹配 / TS7 严格首匹配） | `bfb870234d` | 2023-02-06 | 18.12.1 | 110.0.5481.77 | 官方版本 |
| 18 | **v22.3.27**（内置 Node 16 段终点；Vue 2.7 + webpack4 工具链上限；工具：Yarn1 使用区 / TS7 段擦边） | `e2dac668c6` | 2023-10-09 | 16.17.1 | 108.0.5359.215 | 官方版本 |
| 19 | **v29.0.0**（内置 Node 20 段起点；Node 20 LTS 起始） | `69d371fc41` | 2024-02-20 | 20.9.0 | 122.0.6261.39 | 官方版本 |
| 20 | **v28.3.3**（内置 Node 18 段终点；Node 18 LTS 截止） | `92e4123de7` | 2024-05-23 | 18.18.2 | 120.0.6099.291 | 官方版本 |
| 21 | **v35.0.0**（内置 Node 22 段起点；Node 22 LTS 起始） | `107b3f8580` | 2025-03-04 | 22.14.0 | 134.0.6998.44 | 官方版本 |
| 22 | **v34.5.8**（内置 Node 20 段终点；Node 20 LTS 截止） | `a0e026826c` | 2025-06-04 | 20.19.1 | 132.0.6834.210 | 官方版本 |
| 23 | **v40.0.0**（内置 Node 24 段起点；Node 24 LTS 起始） | `35b8855913` | 2026-01-15 | 24.11.1 | 144.0.7559.60 | 官方版本 |
| 24 | **v39.8.10**（内置 Node 22 段终点；Node 22 LTS 截止） | `d7c42ebd5c` | 2026-05-05 | 22.22.1 | 142.0.7444.265 | 官方版本 |
| 25 | main（= v46.0.0-nightly.20261016-6） | `baccc3ffd` | 2026-10-16 | 24.22.0 | 158.0.8105.0 | 官方版本 |
| 26 | **v44.9.0**（内置 Node 24 段终点；Node 24 LTS 截止；当前最新 stable） | `fd148b9908` | 2026-10-17 | 24.22.0 | 152.0.7977.167 | 官方版本 |

口径与补充：
- "距 v2.0.0 还差 N 提交" = 官方（GitHub compare 口径）head 独有提交数，本地
  `git rev-list --count <对象>..v2.0.0` 实证：`9dfb85dd..v2.0.0` = **974**（merge-base
  = `f8adaed76`，即 v1.8.2-beta.3）；`6fc819dae..v2.0.0` = **101**（merge-base = `2a97e484`）。
- v2.0.0 的 commit `6b90807cb8`（"Bump v2.0.0"，2018-05-01）；v4.0.0 的 commit
  `005264ca1f`（"Bump v4.0.0"，2018-12-20）。
- 6fc819dae 的定位：主干上最近 tag = v1.8.2-beta.3（2017-11-24），其后 1,315 提交
  （compare `9dfb85dd...6fc819dae`，本地 `rev-list` 同值）；v1.8.4 侧独有 backport = 99
  （compare `6fc819dae...9dfb85dd`）。
- main 定位：HEAD = **v46.0.0-nightly.20261016 之后 6 提交**（`git describe --tags`）；
  相对最新 stable **v44.8.0**（`60169b45c1`，2026-10-15）领先 **723** 提交（compare
  v44.8.0...baccc3ffd）；package.json 恒为 `0.0.0-development`，版本只能由 describe/DEPS
  定位（Chromium 158 / Node 24.22，领先 stable 44.8.0 的 Chromium 152 两个主版本）。
- 打包工具官方推荐变更考证（v22.0.0 行）：Electron 官方博客
  "Introducing Electron Forge 6"（2022-11-03）声明 **Forge 成为官方
  "batteries-included" 构建/打包管线**——此前官方对构建工具持无意见立场，
  依赖社区 electron-packager / electron-builder；Forge v1~v5 基于已停维护的
  electron-compile，v6 完全重写并迁入 electron 官方组织。变更点后第一个
  electron major = v22.0.0（2022-11-29）。

### v4.0.0 → v7.3.3 之间的官方发布与内核变更

区间内官方正式版发布共 **94 个**（含两端 4.0.0 与 7.3.3；patch 级统计，来源
`releases.electronjs.org/releases.json`）。除下表变更点外，其余发布均为安全/修补
（内核保持不变）。内核仅在这些版本发生 **major 变更**：

| 版本 | 发布时间 | Chromium | Node.js | V8 | 变更 |
| --- | --- | --- | --- | --- | --- |
| **4.0.0** | 2018-12-20 | 69.0.3497.106 | 10.11.0 | 6.9.427.24 | 区间起点；首次支持 `patches/` |
| **5.0.0** | 2019-04-24 | **73.0.3683.119** | **12.0.0** | 7.3.492.27 | **Chromium 69→73 + Node 10→12** 双 major |
| **6.0.0** | 2019-07-29 | **76.0.3809.88** | 12.4.0 | 7.6.303.27 | Chromium major（Node 仅 minor） |
| **7.0.0** | 2019-10-21 | **78.0.3905.1** | 12.8.1 | 7.8.279 | Chromium major；7.x 全系保持 Chromium 78 |
| **7.3.3** | 2020-08-25 | 78.0.3904.130 | 12.8.1 | 7.8.279.23 | 区间终点；**本项目引用的版本** |

补充：
- 区间内 minor 线共 9 条：4.0/4.1/4.2、5.0、6.0/6.1、7.0/7.1/7.2/7.3；同一 major 内的
  minor 升级（如 7.1→7.2→7.3）只携带 Chromium/Node patch 与维护修复，不升内核 major。
- 时间线交叉：7.0.0（2019-10-21）比 6.1.0（2019-10-22）早一天发布（major 先于维护线补丁）。

### 构建链 Python 要求切换点（py2 → py3）

对本仓库重建编译链的意义：蓝本 ymmuse/electron-ci 的 py 脚本按 Python 2 编写（对应官方
v1.8.4 时代），而本表用于判断若升级到更新的官方 electron，从哪个版本起可改用 py3。

以官方 `docs/development/build-instructions-{linux,macos,windows}.md` 为准
（本地 `git show <tag>:<文件>` 逐 tag 实证）：

| 版本 | 发布时间 | 官方文档 Python 要求 |
| --- | --- | --- |
| v7.3.3 | 2020-08-25 | **Python 2.7.x**（linux/macos 均写 2.7；windows 写 2.7.10+） |
| v8.0.0 ~ v13.0.0 | 2020-08 ~ 2021-06 | Python 2.7.x（windows 自 v12 起不再写 2.7，改列 pywin32） |
| v14.0.0 ~ v18.0.0 | 2021-08 ~ 2022-03 | Python 2.7.x（linux/macos 仍写 2.7） |
| **v19.0.0** | **2022-05-31** | **Python >= 3.7**（linux/macos 同步改为 3.7） |
| v20.0.0 及以后 | 2022-08 ~ | Python >= 3.7（保持） |

结论（二分法实证：v7.3.3 为 py2 起点，v18 为最后一个 py2，v19 为首个 py3，中间无 major）：
- **官方构建文档首次声明可用/要求 Python 3 的版本 = v19.0.0（2022-05-31，Chromium 102 / Node 16.14）**；
- v7.3.3 ~ v18.x 全链官方要求 Python 2.7（注意：Chromium 上游实际更早移除 py2，
  electron 文档存在滞后——v19 才是文档口径的切换点）；
- 本项目重建链锁定的官方基线为 v4.0.0（2026-10-18 由 v1.8.4 切换）/v7.3.3，
  均在 py2 区间，故 electron-ci 用 Python 2 驱动与官方口径一致
  （详见 docs/electron-ci.md）。

二分法过程（低边界 v7.3.3 = py2.7，高边界 v44.8.0 = py3.9，逐 tag show 官方文档实证）：

```
v7.3.3 (2020-08) py2.7 ──────────────────────────── v44.8.0 (2026-10) py3.9
   │                                                     │
   ├─ v26.0.0 (2023-02) = py3.7 → 左移                    │
   │     └─ v16.0.0 (2021-11) = py2.7 → 右移              │
   │           └─ v21.0.0 (2022-08) = py3.7 → 左移        │
   │                 └─ v18.0.0 (2022-03) = py2.7 → 右移  │
   │                       └─ v19.0.0 (2022-05) = py3.7   │
   └──────────────── 收敛：v18（最后 py2）↔ v19（首个 py3）─┘
```

- 二分后延续验证：v26.0.0 / v30.0.0 = Python >= 3.7；v40.0.0 / v44.8.0 = Python >= 3.9
  （linux/macos 文档；v40 起 linux 文档不再单列 python 要求，改引用 Chromium 依赖说明）。
- v19.0.0 已纳入上方排序表（第 6 行）；v4.0.0（首次 patches/）与 v19.0.0（首次 py3）
  同为本项目重建链的两个"能力里程碑"版本。

**py2.7 下限锚定**（按用户口径，不溯源更早版本）：
- 表中最早两个版本即为 py2.7 要求下限，官方文档均实证 Python 2.7.x：
  - v1.8.4（`9dfb85dd`）：linux "Python 2.7.x … You must have Python 2.7.x for the
    script to succeed"；windows "Python 2.7"；
  - 2018-04-10 master（`6fc819dae`）：同上（同时代文档结构）；
- 低于这两个版本不再考证 py2.7 下限（本项目重建链不涉及更早版本）。
- 由此完整区间：**Python 2.7：v1.8.4 / 2018-04-10 master（下限）→ v18.x（上限）；
  Python 3：v19.0.0 起**。

### Vue 2 与内置 Node 兼容性（添加 electron 版本的判断依据）

本项目（SPlayerX 4.9.4）实证（`legacy/chiflix-splayerx-4.9.4/package.json`）：
- `vue: ^2.6.11`、`vue-template-compiler: ^2.6.10`、`webpack: ^4.44.2`、`engines.node: ^12`；
- 实际 electron 依赖 = `@chiflix/electron@7.3.3`（Node 12.8.1）。

Vue 2 版本线：最终 minor = **2.7**（2022-07-01 发布，2.7.16 为最终 patch，EOL 2023-12-31）；
Vue 2.7 构建链 = webpack 4 + vue-loader 15 + Vue CLI 4.5.18 / 5.0.6（官方升级指南）。

**Node 上限依据**：Vue 2 标配的 webpack 4（及其 md4 哈希）在 **Node 17+**（内置 OpenSSL 3）
编译报 `ERR_OSSL_EVP_UNSUPPORTED` → Vue 2.x 工具链支持 Node 的上限为 **Node 16**。

内置 Node major → Electron 段终点（解析自 `releases.electronjs.org/releases.json`）：

| 内置 Node | 段内最后 Electron | 时间 | 内核 |
| --- | --- | --- | --- |
| Node 12 | **11.5.0** | 2021-08-31 | Chromium 87 / Node 12.18.3 |
| Node 14 | 14.2.9 | 2022-03-30 | Chromium 93 / Node 14.17.0 |
| Node 16 | **22.3.27** | 2023-10-09 | Chromium 108 / Node 16.17.1 |
| Node 18 | 28.3.3 | 2024-05-23 | Chromium 120 / Node 18.18.2 |
| Node 20 | 34.5.8 | 2025-06-04 | Chromium 132 / Node 20.19.1 |
| Node 22 | 39.8.10 | 2026-05-05 | Chromium 142 / Node 22.22.1 |
| Node 24 | 44.9.0 | 2026-10-17 | Chromium 152 / Node 24.22.0 |

结论（两个口径，均入排序表）：
- **口径 A（当前项目）**：`engines.node ^12` + vue 2.6 工具链 → 内置 Node 12 的最后
  electron = **v11.5.0**（`3d0705d81f`）；
- **口径 B（Vue 2.7 上限）**：webpack 4 / vue-loader 15 上限 Node 16 → 内置 Node 16 的最后
  electron = **v22.3.27**（`e2dac668c6`）。

Vue 3 下限考证（对称问题，官方 `vuejs/core` package.json `engines.node` 实证）：
- **v3.0.0（2020-09-18）/ v3.2.0（2021-08）均声明 `node >=10.0.0`** → Vue 3 下限 = **Node 10**；
- v3.5.0（2024-09）起升为 `>=18.12.0`；
- 内置 Node 10 段的最后 electron = **v4.2.12**（2019-10-16，Node 10.11.0 / Chromium 69）——
  注意其时序早于 Vue 3.0.0 发布（2020-09），属"内置该下限 Node 的 electron 段终点"，
  与 Vue 2.7 上限对应的 v22.3.27 同为"按内置 Node 匹配、而非按发布时间匹配"。

### 依赖工具（Yarn / Corepack / pnpm）的 Node 要求考证

本项目（SPlayerX 4.9.4）时代使用 **Yarn 1（Classic）**；Yarn 家族以 1 / 2 为分界：

| 工具 | engines（npm registry 实证） | Node 要求 → 对应 electron |
| --- | --- | --- |
| **Yarn 1（Classic，1.22.22）** | `node >= 4.0.0`（npm dist-tag `latest` 至今仍为 1.22.22） | 下限 Node 4 → electron 0.x（表外）；实际使用区间 Node 8~16 → 表内 v1.8.4（Node 8.2.1）/ v11.5.0（Node 12 终点）/ v22.3.27（Node 16 终点）已覆盖 |
| **Yarn 2（Berry，2.4.3）** | `node >= 10`（npm dist-tag `berry` = 2.4.3；2.x 即 Berry 分界） | 下限 Node 10 → 内置 Node 10 段终点 **v4.2.12**（已在表，同 Vue 3 下限口径） |
| **Corepack** | Node 官方文档实证 "Added in: v16.9.0, v14.19.0"（实验性，Node 16.9.0 于 2021-08-31 发布） | 门槛 Node 16.9 → 首个内置 Node ≥16.9 的 electron = **v16.0.0**（Node 16.9.1 / Chromium 96.0.4664.45，2021-11-16，已入表第 13 行） |

**pnpm 各 major 的 Node 边界**（npm registry engines 实证）：

| pnpm major | 代表版本 | engines | Node 要求 → 对应 electron（首匹配 ≥ 下限，均在表内） |
| --- | --- | --- | --- |
| pnpm 3 | 3.8.1 | `node >= 8.15` | electron 无内置 Node ≥8.15 且 <10 的版本（Node 8 段最高 = v2.0.0 的 8.9.3），按段口径命中表内 v1.8.4 / v2.0.0 |
| pnpm 4 | 4.14.0 | `node >= 10.13` | Node 10 段（段终点 v4.2.12，Node 10.11 略低于 10.13）；严格 ≥10.13 首匹配 = v5.0.0（Node 12） |
| pnpm 5 | 5.18.9 | `node >= 10.16` | 同上（Node 10 段） |
| pnpm 6 | 6.32.25 | `node >= 12.17` | Node 12 段 → 段终点 **v11.5.0**（Node 12.18.3，已表） |
| pnpm 7 | 7.33.7 | `node >= 14.6` | Node 14 段 → 段终点 **v14.2.9** / 严格首匹配 v12.0.0（Node 14.16，均已在表） |
| pnpm 8 | 8.15.9 | `node >= 16.14` | 首匹配 = **v19.0.0**（Node 16.14.2，已表） |
| pnpm 9 | 9.15.9 | `node >= 18.12` | 首匹配 = **v23.0.0**（Node 18.12.1，已表） |
| pnpm 10 | 10.0.0 | `node >= 18.12` | 与 v9 同下限，同上 |

补充：
- Yarn 1 的 engines 下限 Node 4 无表内 electron 对应（electron 0.x 时代早于 Yarn 1 发布），
  故以"实际使用区间"标注；Yarn 2 下限 Node 10 直接命中表内 v4.2.12（Node 10 段终点）。
- Corepack 与 Yarn 2 的关系：Node 16.9 内置 Corepack 的初衷即"免安装使用 Yarn/pnpm"，
  Corepack 默认代理的包管理器版本即 Yarn 2（Berry）家族。
- pnpm 边界全部命中表内已有版本，**无需新增入表**；唯一无精确 electron 对应的是
  pnpm 3（Node 8.15，electron 内置 Node 8 段最高 8.9.3）。

### TypeScript 各主版本的 Node 最低要求（npm engines 实证）

| TS 主版本 | 代表版本 | engines | Node 要求 → 对应 electron |
| --- | --- | --- | --- |
| TS 2.x / 3.x / 4.x | 2.9.2 / 3.9.10 / 4.9.5 | `node >= 4.2.0` | Node 4 段 → electron 0.x（表外） |
| **TS 5.0.x** | 5.0.4 | `node >= 12.20` | Node 12 段最高 12.18.3（v11.5.0）低于 12.20 → 严格首匹配 **v12.0.0**（Node 14.16.0，已表） |
| **TS 5.1+ ~ 6.x** | 5.1.6 / 5.9.2 / 6.0.0-beta | `node >= 14.17` | 首匹配 **v14.2.9**（Node 14.17.0，已表） |
| **TS 7.x（当前版本）** | **7.0.2**（npm `latest`，2026） | `node >= 16.20.0` | Node 16 段最高 16.17.1（v22.3.27）低于 16.20 → 严格首匹配 **v23.0.0**（Node 18.12.1，已表） |

补充：
- 当前 TS 版本 = **7.0.2**（npm dist-tag：`latest` = 7.0.2、`next` = 7.1.0-dev、`beta` = 6.0.0-beta、
  `rc` = 7.0.1-rc；6.x 无 stable 版本号，7.x 直接作为 next major）。
- TS 5.0 的 Node 12.20 与 TS 7 的 Node 16.20 两处下限，electron 内置 Node 段均未精确达到
  （Node 12 段最高 12.18.3、Node 16 段最高 16.17.1），故严格口径分别落到 v12.0.0 与 v23.0.0，
  均为表内已有版本，**无需新增入表**。

### 相交点（共同祖先）、正式版锚定与发布模型切换

- v1.8.4（`9dfb85dd`，1-8-x 维护线）与 2018-04-10 master（`6fc819dae`，主干）的
  **第一次相交 = 共同祖先 `f8adaed76` = v1.8.2-beta.3（2017-11-24）**（本地 `git merge-base` 实证）；
- 分叉后两侧：1-8-x 线 **99 提交** → v1.8.4（GitHub compare `6fc819dae...9dfb85dd`）；
  主干 **1315 提交** → 6fc819dae（compare `9dfb85dd...6fc819dae`；本地 `rev-list` 同值）；
- **相交后第一次 release 的有 tag 正式版**：
  - 时间上全局第一个 = **v1.8.2**（`5e8735c96`，2018-02-06，1-8-x 线）；
  - **master 主干上的第一个正式版 = v2.0.0**（`6b90807cb8`，2018-05-01）——
    **处理口径：经确认，v2.0.0 视为主干内（遗留问题简化）**；git 实证注记：其 tag commit
    实际不在 master 主干链（`merge-base v2.0.0 6fc819dae = 2a97e484`，走 2-0-x 分支线），
    主干直发自 v3.0.0（2018-09-18）起恢复；
- **发布模型切换（重要，回答"1.8.2 是否回到 master"）**：
  - v1.8.1（2017-09-28）及以前：master 主干直发（tag 在主干）；
  - **v1.8.2 起改分支发布**：v1.8.2/v1.8.3/v1.8.4（1-8-x 线）、v2.0.0-beta.1~8 与
    v2.0.0 正式（2-0-x 线）**git 层面均不在 master 主干**（`rev-list` 全链 grep + `merge-base`
    双重实证），但 **v2.0.0 按处理口径视为主干内**；
  - **v3.0.0 起恢复主干直发**：v3.0.0、v4.0.0 的祖先均含 6fc819dae（`--is-ancestor` 实证）；
- 由此，2018-04-10 master（`6fc819dae`）的**正式版口径锚定 = "v2.0.0 正式版之前的 master"**
  （v1.8.2-beta.3 + 1315 提交，位于 v1.8.2 与 v2.0.0 之间；git 实证中 v2.0.0 在分支线、
  主干直发自 v3.0.0 恢复，但处理口径统一按 v2.0.0 在主干内）。

## 四、相互关系

### 血缘（官方 electron/electron.git 同源）

```
v1.8.2-beta.3 (2017-11-24)  ← 相交点（共同祖先）
    │  └─ 1-8-x 维护线 → v1.8.4 (2018-03-16) ← 蓝本 electron-ci 源码基线（9dfb85dd）
    └─ master 主干（+1315 提交）
          └─ 6fc819dae (2018-04-10) ← dev-ymmuse fork 基线（Chromium 63 / Node 9.7）
                │
                ├─ ymmuse dev-ymmuse 定制线（57cd9d9，源码零改动，定制在 libcc）
                │
                └─ 官方继续（处理口径主干线）：v2.0.0 (2018-05-01) → v3.0.0 (2018-09-18)
                      → v4.0.0 (2018-12-20, 首次支持 patches/) → … → v7.3.3 (2020-08-25)
                      → … → main = v46.0.0-nightly (2026-10-16)
```

注：git 实证中 v2.0.0 的 tag commit 在 2-0-x 分支线（不在 master 主干链），
但按用户确认的处理口径视为主干内（遗留问题简化），上图据此绘制。

关键点：
- **v1.8.3 / v1.8.4 是 1-8-x 维护线的 tag**，不在 master 主干历史链上，
  因此 2018-04-10 的 master（6fc819dae）在主干链上最近的 tag 是 **v1.8.2-beta.3**（+1315 提交），
  而不是 v1.8.4——这是旧日 master 锚定官方版本的准确描述方式。
- main 分支的版本号在 package.json 恒为 `0.0.0-development`，其官方身份只能靠
  `git describe`（v46.0.0-nightly 系列）与 DEPS 内核版本（Chromium 158）定位：
  已领先稳定版（44.8.0 = Chromium 152）两个主版本。

### 用途矩阵

| 官方 electron | 用途 |
| --- | --- |
| main（v46 nightly） | 参考最新 electron（结构/API/构建链形态），用户指定 main 而非某个 release |
| v7.3.3 | 参考——与 SPlayerX 4.9.4 实际依赖的 `@chiflix/electron@7.3.3`（npm）同版本号、同内核（Chromium 78） |
| v4.0.0（electron-ci/vendors/electron） | **本项目 electron-ci 构建链基线**（2026-10-18 由 v1.8.4 切换；蓝本 ymmuse/electron-ci 原锁定 v1.8.4 `9dfb85dd`，因 piotrbulinski/boto 删仓切换 v4.0.0 `f2d1e5fa`） |
| v1.8.4（蓝本自带定义） | 蓝本仓库 .gitmodules 原样并入、保留定义（历史事实） |
| 2018-04-10 master（6fc819dae） | dev-ymmuse fork 基线（差异对比基准，见 electron-vs-official.md） |

### 构建链归属（两条路线，均保留）

1. **蓝本 CI 线**：官方 **v1.8.4**（9dfb85dd）源码 + electron-ci/patches 补丁 → 对应蓝本
   `ymmuse/electron-ci`（e82d2d8，2018-04-28 建仓）；
2. **dev-ymmuse 线**：官方 **2018-04-10 master**（6fc819dae）源码 + 定制
   libchromiumcontent（364cf9c6，AVI + proprietary codecs）→ 对应 `ymmuse/electron` dev-ymmuse。

两者时间点不同（蓝本 v1.8.4 线 / 本项目 v4.0.0 线 vs master 2018-04 线）；
本项目当前由 `build-custom-electron.yml`（workflow_dispatch，matrix linux/windows）
打包 **v4.0.0 基线**，产物上传 GitHub Releases（不进 git）。

## 五、官方 `patches/` 目录引入考证

### 引入版本：v4.0.0（2018-12-20 发布）

本地逐 tag 检查树（`git ls-tree <tag> --name-only`）：

| tag | `patches/` 是否存在 |
| --- | --- |
| v2.0.0（2018-05-01） | 否 |
| v3.0.0（2018-09-18） | 否 |
| **v4.0.0（2018-12-20）** | **是（首个）** |
| v5.0.0 / v6.0.0 / v7.0.0 | 是 |
| v7.3.3（2020-08-25） | 是 |
| main（2026-10-16） | 是 |

即：**官方 electron 从 v4.0.0 开始支持 `patches/` 目录**（v4 之前补丁机制在
vendor/libchromiumcontent 与 CI 脚本中，无独立 patches 目录）。

### 结构演进

| 版本 | patches/ 结构 |
| --- | --- |
| v4.0.0（初代） | `patches/common` + `patches/mips64el`（**按架构分**） |
| v7.3.3 | `angle、boringssl、chromium、config.json、ffmpeg、icu、node、pdfium、perfetto、quiche、…`（**按组件分**） |
| main | `README.md、angle、boringssl、chromium、config.json、devtools_frontend、ffmpeg、libaddressinput、nan、node、…`（组件持续演进） |

### 与蓝本 electron-ci patches 的关系

- 蓝本 `ymmuse/electron-ci`（2018-04-28 建仓，**早于**官方 v4.0.0）自带
  `patches/common/`（ffmpeg、libchromiumcontent）+ `.patches.yaml`，由
  `apply-patches` 用 `git apply --directory <repo>` 打在 electron 源码上；
- 命名与官方 v4.0.0 的 `patches/common` 同构，但**独立设计**（时间上蓝本更早，
  且蓝本针对 v1.8.4 时代源码，官方 v4 的 patches 作用于自身 Chromium 78 时代依赖）；
- 本项目 `legacy/electron-ci/` 沿用蓝本这套机制（`patches/common/` 原样保留）。

## 六、里程碑 ① 考证：@chiflix/electron@7.3.3 内核对比（实证）

**考证目标**：确认第三方打包 electron（SPlayerX 实际依赖的
`@chiflix/electron@7.3.3`）的内核（Node / Chromium / V8）是否与官方 v7.3.3 一致，
从而坐实"官方 v7.3.3 是复刻基线"这一里程碑 ① 的前提。

**考证过程**（本机 `.git/chiflix_check/` 与 `.git/chiflix_pkg/`，2026-10-17）：

1. **npm registry 元数据**：`@chiflix/electron@7.3.3` 是一个**下载器壳**（无源码）：
   `dependencies = electron-download@4.1.1 / @types/node@^12.0.12 / extract-zip@^1.0.3`，
   `scripts.postinstall = node install.js`，`engines.node >= 8.6`。
2. **install.js 实证**（tarball 解压）：`download({ mirror: 'https://github.com/chiflix/electron/releases/download/v', version: '7.3.3', disableChecksumSafetyCheck: true, ... })`
   —— 即真实二进制来自 **chiflix/electron 的 GitHub Releases v7.3.3**，
   印证"chiflix/electron 仓库无源码、只存二进制"的判断。
3. **安装**：nvm 切 Node 12.22.12（electron-download 4.1.1 需当时 Node），yarn 装包
   触发 postinstall → 下载并解压 `dist/electron.exe`（≈100MB）、`dist/version` = `7.3.3`。
4. **运行时取证**：`dist/electron.exe` 跑一个立即退出的 app，输出
   `process.versions` 到文件。

**对比结果**：

| 内核 | 官方 v7.3.3（`3f2d5c217`） | @chiflix/electron@7.3.3 实际二进制 | 一致 |
| --- | --- | --- | --- |
| Electron | 7.3.3 | 7.3.3（`dist/version` 实证） | ✅ |
| Node | 12.8.1 | 12.8.1（`process.versions.node` 实证） | ✅ |
| Chromium | 78.0.3904.130 | 78.0.3904.130（`process.versions.chrome` 实证） | ✅ |
| V8 | 7.8.279.23 | 7.8.279.23-electron.0（electron 构建惯例后缀） | ✅ |

**结论**：

- 第三方打包 electron（chiflix Release v7.3.3）与官方 v7.3.3 **内核版本完全一致**；
  定制差异在**补丁层**（ffmpeg / AVI 移植等，由 ymmuse 系 fork 承载），不改内核版本号。
- **里程碑 ①（v7.3.3）基线成立**：复刻链 =
  官方 v7.3.3 源码（子模块 `electron-electron-v7.3.3`）+ ymmuse 定制补丁
  （`legacy/electron-ci` 重建，build-custom-electron.yml 驱动）→ 产出与
  chiflix Release v7.3.3 等价的第三方打包 electron。
- `@chiflix/electron` npm 包 = 下载器壳 + `dist/` 缓存机制：`dist/version`
  与包版本一致即跳过下载；`ELECTRON_SKIP_BINARY_DOWNLOAD` 可跳过。

## 七、数据来源

- `git describe --tags`：6fc819dae → `v1.8.2-beta.3-1315-g6fc819dae`；
  9dfb85dd → `v1.8.4`；3f2d5c217 → `v7.3.3`；
  baccc3ffd → `v46.0.0-nightly.20261016-6-gbaccc3ffd0`（本地 759 个官方 tag + 完整历史）。
- DEPS：main = Chromium 158.0.8105.0 / Node v24.22.0；v7.3.3 = Chromium 78.0.3904.130 / Node v12.8.1。
- 官方 release 页：v1.8.4（Chromium 59.0.3071.115 / Node 8.2.1 / V8 5.9.211.38）；
  v7.3.3（Chromium 78.0.3904.130 / Node 12.8.1 / V8 7.8.279.23）。
- tag 日期：v2.0.0=2018-05-01、v3.0.0=2018-09-18、v4.0.0=2018-12-20（blog）、
  v7.3.3=2020-08-25、main nightly=2026-10-16。
- GitHub compare 页（官方）：`9dfb85dd...6fc819dae`=1,315；`6fc819dae...v7.3.3`=4,042；
  `v7.3.3...baccc3ffd`=5,000+（上限截断）；`v44.8.0...baccc3ffd`=723。
