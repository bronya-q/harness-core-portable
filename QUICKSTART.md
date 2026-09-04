# Quickstart

## Requirements

- Python 3.11+
- No Ollama / API key needed for the offline demo
- No private user data required

## 5-minute experience

```bash
git clone https://github.com/bronya-q/harness-core-portable.git
cd harness-core-portable
python harness.py start
```

Pick **1. Offline demo**.

Or directly:

```bash
python harness.py demo --offline
```

The demo shows:

1. Alice remembers "the blue key is under the old harbor bell tower"
2. Bob cannot read Alice's private memory (scope isolation)
3. Alice and Bob both know "the old harbor is always foggy" (shared story core)
4. Blue key corrected to silver key
5. v1 → v2 → restore creates v3
6. One-click cleanup of temporary data

## Doctor

```bash
python harness.py doctor
```

## Inspect your data

```bash
python harness.py data status
python harness.py inspect --scope character:alice
```

## Cleanup

```bash
python harness.py demo --reset
```

## No model installed?

- Offline demo, Notebook, Story Core, scope isolation, correction, and restore do **not** require a model.
- Only AI dialogue generation needs a local Ollama.
