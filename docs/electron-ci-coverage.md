# electron-ci：蓝本（ymmuse/electron-ci）vs 本项目 行为对比

> 2026-10-17。对比维度 = **行为链**（下载源码 → 应用补丁 → 修改编译配置 →
> 编译 → 保存产物），不比较源码是否逐字节一致。
> 蓝本 = `legacy/ymmuse-electron-ci-develop`；本项目 = `legacy/electron-ci`。

## 0. 行为链总览

**完整行为链 = 5 步**：
1. 下载源码 → 2. 应用补丁 → 3. 修改编译配置 → 4. 编译 → 5. 保存产物

本项目 5 步均有落实（**仅两个 ci 项目视角，不含 GitHub Actions**）：
`init-sources.py`（①）→ libcc `update` 自动应用补丁（②，`apply-patches.py` 备用）
→ ffmpeg.gn 配置内置/补丁（③）→ `bootstrap.py` + `build.py`（④）
→ `create-dist.py`（⑤，产物 `vendors/electron/dist`）

## 1. 行为链逐环节对比

### ① 下载源码

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| electron | `.gitmodules` 子模块 checkout → `electron/` | `init-sources.py` 清单 → `fetch-sources.py` 下载官方 tarball（9dfb85dd v1.8.4）→ `vendors/electron/` | **等价**（同版本同落位） |
| pyyaml | 子模块 checkout → `vendor/pyyaml/` | 脚本下载（b6cbfeec）→ `vendors/pyyaml/` | **等价** |
| libcc | electron 源码内 `.gitmodules` 子模块 → `electron/vendor/libchromiumcontent` | 脚本下载 ymmuse/electron-libcc（364cf9c6）→ `vendors/libcc/`；`build.py` copy → `electron/vendor/libchromiumcontent` | **等价**（同 commit 同位置） |

### ② 应用补丁

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 主流程 | libcc `script/update` 自动应用 libcc 自带补丁（ffmpeg `github-ymmuse-feature-avi.patch`，启用 AVI demuxer） | **相同**（下载的 libcc 与蓝本同 commit 364cf9c6，自带补丁集） | **一致** |
| 入口 | `apply-patches`：遍历 `patches/common` → `PatchesConfig` → apply，失败退出 1 | `apply-patches.py`：同一行为（补丁目录指向 electron-ci 根 `patches/`） | **一致** |

### ③ 修改编译配置

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| ffmpeg.gn（proprietary_codecs / Chrome branding） | 补丁 `avi_format0001.patch` 修改 `chromiumcontent/args/ffmpeg.gn`（`proprietary_codecs = true`、`ffmpeg_branding = "Chrome"`） | dev-ymmuse 源码**已内置**该配置；`avi_format0001.patch` 保留为备用路径（切换官方 libcc 时用） | **等价**（配置最终生效，行为落点一致） |

### ④ 编译

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 驱动 | `build.py` 仅执行 `libcc/script/update -t <arch>`；`apply-patches`、`electron/script/bootstrap.py -v --build_release_libcc` 为**注释占位（未实现）** | 完整链：copy libcc → `bootstrap.py --build_release_libcc`（内含 libcc bootstrap/update/build/create-dist 全流程）→ `electron/script/build.py -c R` | **超出**（补全蓝本意图） |

### ⑤ 保存产物

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 产物 | 无（update 后即结束） | `create-dist.py` → `vendors/electron/dist` | **超出** |

## 2. 行为差异（有意的，非缺失）

1. **源码就位通道**：子模块 checkout → 脚本下载 tarball（ijkplayer 式）——行为机制不同，行为结果一致（锁蓝本 commit、落位一致、补丁集一致）。
2. **编译链长度**：蓝本 1 步（libcc update）→ 本项目 5 步全链。

## 3. 结论

- **蓝本已实现的行为（①②③主流程、④的 update 部分），本项目全部覆盖**（一致或等价达成）；
- **蓝本意图未实现的行为（④bootstrap/build、⑤产物），本项目已补全**；
- **无"蓝本有、本项目缺"的行为**；
- 验证口径：同一输入（蓝本锁定 commit）→ 同一落位 → 同一补丁注入 → 同一配置 → 同一编译 → 同一产物。
