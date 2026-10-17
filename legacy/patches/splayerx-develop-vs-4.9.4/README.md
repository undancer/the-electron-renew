# splayerx develop（默认分支）相对 4.9.4 的补丁封存

## 背景与用途

本项目（the-electron-renew）以 **splayerx 4.9.4** 为重建编译的基准，已通过 git subtree 将
`chiflix/splayerx` 的 `4.9.4` tag 源码封存在 `legacy/chiflix-splayerx-4.9.4/`。

上游仓库 `chiflix/splayerx` 存在被删除的风险。经对比，其默认分支 `develop`
（commit `032efcc9`）相对 `4.9.4`（commit `c62a90b7`）仅领先 5 个提交、变更 3 个文件，
全部为**构建层修正与依赖升级，无功能代码变更**。为完整保留这一增量，将其以
`format-patch` 形式封存于此，防止上游仓库删除后信息丢失。

## 补丁清单

| 补丁 | 对应提交 | 内容 |
|---|---|---|
| `0001-build-change-git-rev.patch` | `4518b14` | `scripts/build-mac.sh` 调整 git rev 获取方式（含 yarn.lock 变动） |
| `0002-build-check-splayerx-object.patch` | `d517532` | `scripts/build-mac.sh` 增加对 splayerx 对象的检查 |
| `0003-build-deps-bump-ini-from-1.3.5-to-1.3.8.patch` | `f5c7428` | dependabot 依赖升级：ini 1.3.5 → 1.3.8（yarn.lock） |

另有两个 merge 提交（`a3e48b4`、`032efcc9`）无独立内容变更，`format-patch` 默认跳过。

## 应用方法

在 `legacy/chiflix-splayerx-4.9.4/` 目录内按序应用：

```sh
git am ../patches/splayerx-develop-vs-4.9.4/0001-*.patch
git am ../patches/splayerx-develop-vs-4.9.4/0002-*.patch
git am ../patches/splayerx-develop-vs-4.9.4/0003-*.patch
```

或一次性应用全部：

```sh
git am ../patches/splayerx-develop-vs-4.9.4/*.patch
```

> 注：splayerx 子树在主仓库内是 squash 引入的（仅一条提交），`git am` 需要在其自身的
> git 仓库上下文（即独立 clone 出 4.9.4 后再应用）才能保留提交信息；在主仓库内直接
> `git apply` 也可手工合入（忽略提交元数据）。

## 溯源信息

- 上游：`git@github.com:chiflix/splayerx.git`
- 对比基准：`c62a90b7`（tag `4.9.4`）→ `032efcc9`（branch `develop`）
- 差异统计：`ahead_by=5, behind_by=0`；变更文件 3 个（package.json / scripts/build-mac.sh / yarn.lock）
- 生成时间：2026-10-17
