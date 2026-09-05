---
title: GitHub Pre-release v0.1.0-alpha.4 外部回读验证
status: verified
kind: deployment-record
date: 2026-09-05
verified_at: 2026-09-05
version: v0.1.0-alpha.4
release_id: 383167139
source_commit: 97cbd5e
target: github
verified_by: external-audit
public: true
contains_private_data: false
topics: [release, github, alpha, verification, ci, failure]
---

# GitHub Pre-release v0.1.0-alpha.4 外部回读验证

## 1. Release 对象

```text
Release object: exists
URL: https://github.com/bronya-q/harness-core-portable/releases/tag/v0.1.0-alpha.4
release id: 383167139
draft: false
prerelease: true
published_at: 2026-09-05T07:17:37Z
assets: 0
```

## 2. Tag 与 commit

```text
tag: v0.1.0-alpha.4 (annotated, unsigned)
tag object: 7d26520437e5e578a85174738edc9dc31e36cb4d
frozen commit: 97cbd5e351d8a71a176d46d264a6f65346b476ba
verified: false
reason: unsigned
```

## 3. Release 正文

与 `docs/releases/v0.1.0-alpha.4.md` 完全一致。

## 4. Tag 归档验证

本地 `git archive v0.1.0-alpha.4` + 独立临时归档：

```text
release_verify      PASS  242 entries
package_selfcheck   PASS
unittest discover   PASS  58 tests
```

> 本地 git archive 通过 ≠ GitHub Download ZIP 已独立下载验证。

## 5. GitHub Actions 状态（已更新）

### 最初失败（audit 时）

```text
run: 33952129886   (alpha.4 冻结提交 97cbd5e)
conclusion: failure
Ubuntu 3.13   package_selfcheck 失败
Ubuntu 3.11   跑到 unit tests 后被取消
Windows 3.11/3.13  被取消
```

### 已修复

- 重写 `tests/test_mcp_server.py`（逐条写/逐条读，降低时序敏感）。
- 后续 push（`e65f51f`、`cbeedf3`）CI 已通过：

```text
run 33952679446   completed success
run 33952861773   completed success

test (windows-latest, 3.13)  ✓
test (windows-latest, 3.11)  ✓
test (ubuntu-latest, 3.13)   ✓
test (ubuntu-latest, 3.11)   ✓
```

**因此 CI 已从失败转为全绿。**

## 6. 已确认的本地测试波动

首次 `python -m unittest discover -s tests -v` 曾出现 MCP stdio 测试失败（只返回 initialize，未返回 tools/list）。重复运行通过。已为此重写 `tests/test_mcp_server.py` 为逐条写/逐条读，减少时序敏感。

## 7. R2 实际进度

```text
release-checklist: 5 / 12
CI 基线: 失败
外部证据: 基本没有
```

## 8. 结论

```text
Release 发布本身: 真实
tag/commit 对应: 正确
Release 正文: 一致
本地 tag 归档: 通过
GitHub Actions: 已修复，当前 main CI 全绿
外部 ZIP: 未独立验证
R2: 本地自动项 5/12，外部项仍缺
```

本记录更新为：alpha.4 发布本体成立；CI 已通过后续修复转绿。外部 ZIP / 真实宿主 / 真人 / Registry / PyPI 仍属 R2 外部证据。
