# AGENTS.md — project context for coding agents

> This file is a fixture/template for AGENTS.md-based agents.

## What this project is

Portable, local-first memory, persona, knowledge and engineering-role runtime for long-running agents.

## Before editing code

1. Run `python package_selfcheck.py`
2. Read `docs/ROADMAP.md` and the relevant task in `docs/tasks/`
3. Run `python harness.py demo --offline` to understand the public path

## Constraints

- Do not read private local overlay data from `~/.dsh/harness-local/`
- Do not enable `autonomous_tasks`
- Do not add private persona names to public core
