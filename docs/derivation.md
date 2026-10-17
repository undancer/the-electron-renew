# the-electron-renew 推导记录

## 项目目标

**重建 SPlayerX 的编译**。以 splayerx **4.9.4** 为基准版本。

splayerx 4.9.4 由两部分组成：



1. **js 代码**（应用本体）

2. **第三方 electron**（运行时 / 编译底座）

## 目的一：找出第三方 electron 到底是哪一个

### 推导方法与结论

直接证据来自 `legacy/chiflix-splayerx-4.9.4/package.json`：



| 位置                | 内容                                             | 含义                        |
| ----------------- | ---------------------------------------------- | ------------------------- |
| `devDependencies` | `"@chiflix/electron": "7.3.3"`                 | 精确锁定版本（非 `^` 区间）          |
| `_moduleAliases`  | `"electron": "node_modules/@chiflix/electron"` | 运行时强制将 `electron` 模块解析到该包 |

**结论：splayerx 4.9.4 使用的第三方 electron 是 npm 包&#x20;**`@chiflix/electron@7.3.3`，其 GitHub 源仓库为 `chiflix/electron`。

由此串起已添加的项目：



* `chiflix/electron`（v7.3.3）＝ npm 包 `@chiflix/electron` 的 GitHub 源仓库，**无源码、仅保存引用**；

* `electron/electron` v7.3.3（官方）＝ 定制的基础参照；

* `electron/electron` main（官方）＝ 最新参考。

### chiflix/electron 溯源



* 唯一提交者：**ymmuse**（12 次贡献）→ 定制 electron 的人即 ymmuse；

* 其 tags（v7.1.1-dev \~ v7.3.3 全套）均指向 README 空壳提交（ee10850d /ee89abaad）→ 确认仓库无代码。

## ymmuse 名下 electron 相关仓库 fork 判定

以 "是否 fork 官方、是否有修改" 为判据，结果为**全部有实际改动，无一纯 fork**：



| 仓库                      | 形态         | 上游                                 | 改动证据                                                                                     | 结论              |
| ----------------------- | ---------- | ---------------------------------- | ---------------------------------------------------------------------------------------- | --------------- |
| `electron`              | fork 官方    | electron/electron                  | 自建 `dev-ymmuse` 分支，独有提交 `disable jumbo_build`（2018-04-30）                                | 保留              |
| `electron-builder`      | fork 官方    | electron-userland/electron-builder | `ymmuse` 分支独有提交（Windows scoped package 路径修正）；master 为官方 2018-06 快照                       | 保留              |
| `splayerx`              | fork 官方    | chiflix/splayerx                   | 自有提交（`playService`、`improves seek speed on air shared mode`），develop 停在 **4.9.2-beta.2** | 保留（注意非 4.9.4 线） |
| `electron-ci`           | 自建（非 fork） | —                                  | 原创构建脚本（`checkout electron v1.8.4`）                                                       | 保留              |
| `electron-libcc`        | 镜像自建       | chromium libchromiumcontent        | 独有提交 `add feature support plays avi file`                                                | 保留              |
| `electron-libcc-ffmpeg` | 镜像自建       | chromium ffmpeg                    | 独有提交 `add avi decode files`                                                              | 保留              |

## ymmuse 仓库深挖（2026-10-17）

基于本地子模块 + 加深历史 + GitHub 对比，各仓库基线、独有改动如下：

| 仓库 / 分支 | 基线 | ymmuse 独有改动 | 说明 |
| --- | --- | --- | --- |
| electron `dev-ymmuse` | 官方 master @ 2018-04-10（`6fc819dae`，Chromium 63 + Node 9.7.0，≈ v2.0.0 发布前） | 9 提交：`vendor/libchromiumcontent` 子模块改指向 **ymmuse/electron-libcc（dev-ymmuse）**、4 次 gitlink 调整、4 次 CI 配置（.travis.yml / script/cibuild，macOS 编译）、README | **electron 源码零改动**，定制全部下沉到 libchromiumcontent |
| electron-libcc `dev-ymmuse` | 官方 libchromiumcontent（VERSION = 63.0.3239.150） | 3 提交：`add feature support plays avi file`（**github-ymmuse-feature-avi.patch**，最终落 `patches/common/ffmpeg/`）+ gn 构建参数；`fix compiler error`；`disable jumbo_build` | **AVI 支持核心**（补丁作用于 chromium 集成 ffmpeg） |
| electron-libcc-ffmpeg `feature-electron-avi` | ffmpeg 源码镜像（chromium third_party/ffmpeg 集成结构） | 1 提交：`add avi decode files` | AVI 解码源码 |
| electron-ci `develop` | 自建 | build.py → electron/vendor/libchromiumcontent/script/update + apply-patches + bootstrap；electron 子模块指向官方 electron（`9dfb85dd`） | 该定制链的 CI 构建脚本 |
| electron-builder `master` / `ymmuse` | 官方 2018-06-04 快照（`5f39351`，#2976） | `ymmuse` 分支 +1 提交（`6028df6a`）：Windows 下 scoped package 路径修正（NodeModuleCopyHelper.ts） | 与 AVI 链无关；版本线（2018）≠ splayerx 4.9.4 的 electron-builder@^22.8.1 |

**关键推论**：

- ymmuse 定制链整体是 **2018-04 的「带 AVI 播放支持的 electron 定制版」**（electron ≈ 2.0.0-beta 时代 / Chromium 63），服务于 splayerx 早期版本线；
- **与 splayerx 4.9.4 的 `@chiflix/electron@7.3.3`（electron 7.3.3，2019-11，Chromium 78）不同代码线**；4.9.4 的 AVI 补丁是否被移植到 7.x 无法从公开仓库确认（chiflix/electron 空壳、npm 包二进制不可读源码），需下载 npm 包比对（ffmpeg 差异 / 是否含 AVI 解码）验证。

## 附带发现



* `ymmuse/splayerx` 的 develop 停在 **4.9.2-beta.2**（2020-04-21），含 ymmuse 私有修改，与 4.9.4 属不同版本线；

* `electron-builder` 的 master 是官方 2018-06-04 快照（#2976），`ymmuse` 分支才是自定义内容；

* ymmuse 系列整体构成 2018 年「带 AVI 播放支持的 electron 定制版」构建链，与 4.9.4 的 `@chiflix/electron@7.3.3` 是否同源待进一步验证。

## 远程编译验证（2026-10-17）

GitHub Actions 两个 workflow（`Build splayerx 4.9.4` / `Build splayerx 4.9.4 (Windows)`，均 `workflow_dispatch` 手动触发，无自动触发器）：

- **Windows 编译已通过**：`windows-2022` runner 上 `npm run build` 自动分发到 `build-win.bat`（gen-electron-builder-config → webpack 编译 → `electron-builder -w`）成功。间接验证：
  - `@chiflix/electron@7.3.3` 从 npm 正常拉取，且镜像含 **win32 二进制**（此前担心的 `electronDownload.mirror` 缺 Windows 产物风险已排除）；
  - 原生依赖（postinstall → install-app-deps）在 windows-2022 预装工具链下可重建。
- **macOS 编译待验证**：`macos-13` runner 排队中，结果未知。

## 版本对比：splayerx 4.9.4 vs 4.9.4-beta.0

全量文件对比（898 个文件）：

- **897 个文件完全一致**（源码、依赖、构建脚本、yarn.lock 等）；
- 唯一差异：`package.json` 的 `version` 字段（`4.9.4` vs `4.9.4-beta.0`）。

**结论：排除 4.9.4-beta.0，保留 4.9.4**（内容零差异，仅版本号标识不同）。4.9.4-beta.0 子树已从 legacy 移除。

## 默认分支（develop）与 4.9.4 的差异

对比 `chiflix/splayerx` 的 `develop`（`032efcc9`）与 tag `4.9.4`（`c62a90b7`）：

- **develop 领先 5 个提交、无分叉**（behind 0），4.9.4 是 develop 历史线上的发布点；
- 变更文件仅 3 个：`package.json`（版本号）、`scripts/build-mac.sh`（+9/-2）、`yarn.lock`（+96/-50）；
- 5 个提交全部为 2020-12 构建层改动（`change git rev`、`check splayerx object`、dependabot ini 升级），无功能变更。

**结论**：4.9.4 是干净稳定的基线；develop 仅多几个构建脚本修正。

**封存动作**：将 develop 相对 4.9.4 的差异以 `format-patch` 形式封存于
`legacy/patches/splayerx-develop-vs-4.9.4/`（3 个补丁 + README 说明），防止上游仓库删除后增量丢失。

## 待办



* [x] 深挖各仓库的改动内容（electron 的 dev-ymmuse 相对官方版本的差异等）——2026-10-17 完成，见「ymmuse 仓库深挖」

* [x] 远程编译试运行（Windows 通过；macOS 排队待验证）——2026-10-17

* [ ] 验证 @chiflix/electron@7.3.3 npm 包内容（是否含 AVI 补丁移植 / ffmpeg 差异）

* [ ] 版本取舍推导（各仓库最终引入的 ref）

* [ ] 确定去留后调整 legacy 布局并提交