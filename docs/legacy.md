# legacy 目录仓库说明

本文档简要说明 `legacy/` 下各仓库的来历、引入方式与当前锁定的分支/版本。

| 目录 | 来源仓库 | 引入方式 | 锁定分支/版本 | 说明 |
|---|---|---|---|---|
| `chiflix-splayerx-4.9.4` | chiflix/splayerx | 子树（squash） | 4.9.4 | SPlayerX 播放器 fork（electron-vue 工程） |
| `chiflix-electron-v7.3.3` | chiflix/electron | 子树（squash） | v7.3.3 | 空仓库（仅 README），仅作引用保存 |
| `electron-electron-main` | electron/electron | 子模块 | main | 官方主分支，作参考 |
| `electron-electron-v7.3.3` | electron/electron | 子模块 | v7.3.3 | 官方 v7.3.3，作保存 |
| `ymmuse-electron-dev-ymmuse` | ymmuse/electron | 子模块 | dev-ymmuse | electron fork 及用户改造（2018） |
| `ymmuse-electron-ci-develop` | ymmuse/electron-ci | 子模块 | develop | CI 构建脚本（checkout electron v1.8.4） |
| `ymmuse-electron-builder-master` | ymmuse/electron-builder | 子模块 | master | electron-builder fork（v20 时代） |
| `ymmuse-electron-libcc-dev-ymmuse` | ymmuse/electron-libcc | 子模块 | dev-ymmuse | libchromiumcontent fork，加 AVI 播放支持 |
| `ymmuse-electron-libcc-ffmpeg-feature-electron-avi` | ymmuse/electron-libcc-ffmpeg | 子模块 | feature-electron-avi | ffmpeg fork，加 AVI 解码 |

备注：

- 子树引入的项目在主线上各保留一条提交；子模块引入的项目按 `.gitmodules` 锁定对应分支/tag 的 commit。
- ymmuse 系列是 2018 年构建「带 AVI 播放支持的 electron 定制版」的配套构建链，当前按各自默认分支占位，最终版本待确认后再调整。
- 如需将子模块改为子树形式，须明确指示后执行。
