# First-time user testing protocol

## Goal

Find 5 first-time users to validate that a new user can experience, inspect, correct, forget and restore scoped memory without reading internal docs.

## Setup

- Clean clone from GitHub or Download ZIP
- No private local overlay data
- No Ollama required for offline demo
- Record with user consent; no real username/path/private persona in results

## Tasks

1. Download/clone
2. Run `python harness.py demo --offline`
3. Run `python harness.py dashboard build`
4. Find a memory (`memory list --scope character:alice` / after demo)
5. Correct it (`memory correct ...`)
6. Forget it (`memory forget --id ...`)
7. Restore a version (`memory restore ...`)
8. Determine which character a memory belongs to
9. Confirm no network upload
10. Find data directory
11. Clear demo (`harness.py demo --reset`)

## Record

- completion (pass/fail)
- time (optional)
- where stuck
- number of wrong commands
- whether understood shadow
- whether misread gate FAIL as install failure
- whether successfully deleted data

## Output

Fill one row per participant in `results-template.md`. Store in `docs/user-testing/`. Redact everything.
