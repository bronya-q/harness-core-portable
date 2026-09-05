---
title: GitHub Pre-release v0.1.0-alpha.3 外部回读验证
status: verified
kind: deployment-record
date: 2026-09-04
verified_at: 2026-09-04T13:54:11Z
version: v0.1.0-alpha.3
source_commit: be8167e
release_id: 382769108
target: github
verified_by: project-progress-review
public: true
contains_private_data: false
topics: [release, github, alpha, verification, reproducibility]
---

# GitHub Pre-release v0.1.0-alpha.3 外部回读验证

## 1. 结论

GitHub Release API 已确认 `v0.1.0-alpha.3` 的 Pre-release 对象真实存在：

```text
Release object: exists
URL: https://github.com/bronya-q/harness-core-portable/releases/tag/v0.1.0-alpha.3
release id: 382769108
tag: v0.1.0-alpha.3
name: Harness Core Portable v0.1.0-alpha.3
draft: false
prerelease: true
published_at: 2026-09-04T13:54:11Z
```

因此该 Release 的部署状态可以记为 `deployed`。这只证明 GitHub Pre-release 页面已发布，不等于 alpha.3 已达到 production-ready、MCP 外部认证或所有正文命令都通过。

## 2. Tag 与 commit 对应

GitHub tag ref：

```text
refs/tags/v0.1.0-alpha.3
object type: tag
annotated tag object: f7d8537f65822c94e9fd8209df06fbfd592ef5db
commit: be8167e9d960b8ff7952991051865cc19fc85f82
```

本地 tag 解引用得到同一 commit：

```text
v0.1.0-alpha.3^{} = be8167e9d960b8ff7952991051865cc19fc85f82
```

Tag 是 annotated tag，但 GitHub verification 字段为：

```text
verified: false
reason: unsigned
```

准确表述是“annotated but unsigned”，不能声称 signed/verified tag。

## 3. Release 正文一致性

外部 API 返回的 Release body 与仓库中的：

```text
docs/releases/v0.1.0-alpha.3.md
```

在换行标准化并去除末尾空白后完全一致：

```text
remote body == local release body: true
```

这证明发布页面正文来源一致。

## 4. 冻结点复现

从本地 Git tag 使用 `git archive v0.1.0-alpha.3` 还原冻结点，并在归档目录外保存测试输出，避免测试文件污染发布清单。

结果：

```text
release_verify.py: PASS
source: zip_scan
count: 182
file_entries: 182
issues: []

package_selfcheck.py: PASS
python -m unittest discover: PASS
Ran 8 tests

python -m pip wheel . --no-deps: PASS
wheel: harness_core_portable-0.1.0-py3-none-any.whl
```

这属于本地 tag archive 复现，不是从 GitHub Download ZIP 实际下载后的独立验证。

## 5. Release assets

GitHub Release API 返回：

```text
assets_count: 0
```

因此 Release 页面没有额外上传：

- wheel；
- checksum；
- SBOM；
- signature；
- HCP 示例包。

用户当前只能使用 GitHub 自动生成的 Source code ZIP/TAR 或自行 clone。尝试访问推测的 wheel asset URL 返回 404，与 `assets_count: 0` 一致。

这不影响 Release 页面存在，但“可下载 wheel”不能作为 alpha.3 的外部发布声明。

## 6. 发现的发布正文问题

### 6.1 Manifest count 不一致

Release 正文写：

```text
release manifest entries: 180
```

冻结 tag 实测：

```text
release manifest count: 182
file entries: 182
```

原部署记录还写了 `184（后续工作区随 commit 持续更新）`。部署记录应固定描述 tag 冻结值，不应使用 tag 之后 main 的工作区数量。

正确值：

```text
v0.1.0-alpha.3 release manifest entries = 182
```

### 6.2 `schema validate --mode` 在 tag 中失败

Release 正文列出了：

```bash
python harness.py schema validate --mode <file>
```

在 alpha.3 tag 上用仓库内 situated-mode schema 实测：

```text
rc=1
{"ok": false, "error": "invalid_schema_type", "type": ""}
```

原因是 alpha.3 冻结点的 parser 尚未接入 `--mode`。该修复位于 tag 之后的 main commit `c2930e3`，不能反向归入 alpha.3。

因此：

- Release 正文中的该命令是错误声明；
- 可编辑 Release body 增加勘误，但不可移动 alpha.3 tag；
- 后续 alpha.4 可以声明该命令已修复。

### 6.3 Ecosystem status 在 tag 中仍显示 MCP R0

alpha.3 tag 实测：

```text
python harness.py ecosystem status
MCP-capable clients: R0
note: no MCP server yet
```

但同一 tag 已包含 FastMCP server、pyproject 和 MCP test。原因是 `docs/AGENT_COMPATIBILITY.json` 未同步，属于展示状态漂移。

Release 正文使用“MCP / 生态基础”和“Inspector/Registry/真实宿主尚未验证”的措辞总体合理，但不能把 alpha.3 的 `ecosystem status` 输出当作准确证据。

### 6.4 根 `--help` 在 tag 中失败

alpha.3 tag：

```text
python harness.py --help
rc=1
unknown command: --help
```

Release 正文没有直接宣称此命令通过，因此不是正文冲突，但属于已知 UX 缺陷。该问题在 tag 之后的 main 修复，不能算入 alpha.3。

## 7. Release 能力边界

alpha.3 冻结点确实包含：

- HCP 安全与 activation 基础；
- Character Card/corpus draft/situated mode 基础；
- A/B、usage、evidence 基础；
- workspace worktree/run 基础；
- event/token storage；
- FastMCP server；
- `pyproject.toml`；
- 8 个 unittest。

不属于 alpha.3、位于 tag 之后 main 的能力包括：

- GitHub Actions CI；
- `schema --mode` 接线修复；
- provenance/consent/measurement 后续补强；
- n-gram fallback；
- playable card game；
- provider usage coverage；
- vector retry semantics 后续修订。

Release 页面不得把这些 post-tag 能力反写进 alpha.3。

## 8. MCP 与外部生态边界

alpha.3 Release 可以声明：

```text
Includes an experimental MCP server built with FastMCP.
Repository smoke tests cover initialize and tools/list.
The package can be built as a wheel locally.
```

仍不可声明：

```text
Officially MCP Certified
Listed in the Official MCP Registry
Tested with MCP Inspector
Tested with Claude Code
Tested with Codex CLI
Tested with GitHub Copilot
Published on PyPI
```

这些外部证据目前仍未完成。

## 9. 建议修正与执行状态

### GitHub Release body

不改变 tag，只编辑 Release 正文。复核时以下两项已经同步到远端，`updated_at=2026-09-04T14:00:48Z`：

1. ✅ manifest entries 已从 `180` 改为 `182`；
2. ✅ 已为 `schema validate --mode` 增加勘误，说明 alpha.3 中 parser 未接线、修复属于 tag 之后的 main/alpha.4；
3. ⬜ 如需分发 wheel，应明确 Release assets 当前为 0，并另行上传受校验产物；
4. ✅ 保留 Alpha/WIP、非 production-ready 和 MCP 外部未验证说明。

远端 body 与仓库 `docs/releases/v0.1.0-alpha.3.md` 在标准化换行后完全一致。

### 仓库文档

1. 把原部署记录 manifest count 改为 182；
2. 删除重复的 MCP 未验证条目；
3. 将“第三方 clone + ZIP 回读未验证”细化为：本地 tag archive 已通过，GitHub Download ZIP 尚未完成；
4. 更新旧 whole-project audit 中 alpha.3 API 404 的历史状态，或标注已被本文 supersede；
5. 不移动、不删除 `v0.1.0-alpha.3` tag。

## 10. 最终判定

```text
GitHub Pre-release object: VERIFIED / DEPLOYED
Release body local/remote consistency: VERIFIED
Tag → commit mapping: VERIFIED
Tag type: ANNOTATED, UNSIGNED
Tag archive selfcheck/tests: PASS
Manifest frozen count: 182
Uploaded assets: 0
GitHub Download ZIP execution: NOT YET VERIFIED
Release body accuracy: ERRATA APPLIED / REMOTE-LOCAL MATCH
MCP Inspector/Registry/real hosts: NOT VERIFIED
Production readiness: NOT CLAIMED
```

## 11. 后辈接手说明

- 以本文替代“alpha.3 Release API 404/tag-only”的旧快照；
- 发布事实已经变化时，应保留历史报告但标注 superseded，而不是悄悄改写历史；
- 编辑 GitHub Release body 是外部操作，需要用户授权；
- 不要移动公开 tag；
- 不把 main 后续功能归入 alpha.3；
- 不把 annotated tag 称为 signed tag；
- 不把 GitHub 自动 Source ZIP 称为上传的 release asset；
- Autonomous 与 L4/L5 actual-impact 继续禁用。
