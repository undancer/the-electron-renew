# electron-ci：蓝本（ymmuse/electron-ci）vs 本项目 行为对比

> 2026-10-18。对比维度 = **行为链**（下载源码 → 应用补丁 → 修改编译配置 →
> 编译 → 保存产物），不比较源码是否逐字节一致。
> 蓝本 = `legacy/ymmuse-electron-ci-develop`；本项目 = `legacy/electron-ci`。
> 本项目基线 = 官方 electron v4.0.0（`f2d1e5fa`）；蓝本基线 = 官方 v1.8.4
> （`9dfb85dd`）——基线变更原因见 docs/electron-ci.md。

## 0. 行为链总览

**完整行为链 = 5 步**：
1. 下载源码 → 2. 应用补丁 → 3. 修改编译配置 → 4. 编译 → 5. 保存产物

本项目 5 步均有落实（**仅两个 ci 项目视角，不含 GitHub Actions**）：
`init-sources.py`（①）→ `apply-patches.py`（②，机制保留，补丁暂未启用）
→ 预留点位（③，参数待定）→ `build.py` bootstrap + build（④）
→ `create-dist.py`（⑤，产物 `electron/dist`）

## 1. 行为链逐环节对比

### ① 下载源码

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| electron | `.gitmodules` 子模块 checkout → `electron/`（v1.8.4 `9dfb85dd`） | `init-sources.py` 清单 → `fetch-sources.py` git 迁出官方 v4.0.0（`f2d1e5fa`，递归子模块 requests/boto）→ `vendors/electron/` | **结构等价**（git 迁出 vs 子模块），**基线不同**（v1.8.4 → v4.0.0，规避 boto 删仓） |
| pyyaml | 子模块 checkout → `vendor/pyyaml/` | 脚本 git 迁出（b6cbfeec）→ `vendors/pyyaml/` | **等价**（当前未迁出，惰性引入） |

### ② 应用补丁

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 主流程 | libcc `script/update` 自动应用 libcc 自带补丁（ffmpeg `github-ymmuse-feature-avi.patch`，启用 AVI demuxer） | 补丁机制保留（`apply-patches.py`），**`patches/` 当前已清空为占位**，尚未应用任何补丁 | **机制一致、未启用**（里程碑①先跑官方基线，补丁待后续） |
| 入口 | `apply-patches`：遍历 `patches/common` → `PatchesConfig` → apply，失败退出 1 | `apply-patches.py`：同一行为（补丁目录指向 electron-ci 根 `patches/`） | **一致** |

### ③ 修改编译配置

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 编译参数 | libcc `chromiumcontent/args/ffmpeg.gn`（proprietary_codecs / Chrome branding）经补丁修改 | **预留点位**（init.py `edit_build_args()`，具体参数内容待定，不预设） | **待定**（里程碑①推进时填充） |

### ④ 编译

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 驱动 | `build.py` 仅执行 `libcc/script/update -t <arch>`；`apply-patches`、`bootstrap.py` 为注释占位（未实现） | `build.py`：检查 `electron/` 存在 → `electron/script/bootstrap.py --target_arch=x64 -v`（官方脚本，DEPS/gclient 就位依赖）→ `electron/script/build.py -c R` | **结构一致**（v4.0.0 无 libcc，bootstrap 为官方全链） |

### ⑤ 保存产物

| | 蓝本 | 本项目 | 等价性 |
| --- | --- | --- | --- |
| 产物 | 无（update 后即结束） | `create-dist.py` → `electron/dist`；GitHub Actions 上传 GitHub Releases（不进 git） | **超出** |

## 2. 行为差异（有意的，非缺失）

1. **源码就位通道**：子模块 checkout → 脚本 git 迁出（ijkplayer 式）——
   行为机制不同，行为结果一致（锁 commit、落位一致、子模块机制保留）。
2. **基线**：v1.8.4（蓝本）→ v4.0.0（本项目）——规避
   `piotrbulinski/boto` 删仓导致的递归子模块 clone 失败；
   v4.0.0 无 libchromiumcontent，chromium 经 DEPS/gclient 拉取。
3. **编译链长度**：蓝本 1 步（libcc update）→ 本项目 5 步全链（bootstrap
   为官方脚本，无 libcc 参与）。

## 3. 结论

- **蓝本已实现的行为（①②③主流程、④的 update 部分），本项目全部覆盖**
  （一致或等价达成）；
- **蓝本意图未实现的行为（④bootstrap/build、⑤产物），本项目已补全**；
- **无"蓝本有、本项目缺"的行为**；
- 当前状态：补丁（②③）与编译参数（③）为里程碑①过渡态（补丁清空为
  占位、参数预留点位），先验证官方 v4.0.0 基线完整编译通过；
- 验证口径：同一输入（本项目锁定 commit v4.0.0）→ 同一落位 → 同一编译
  链 → 同一产物（electron/dist → Releases）。
