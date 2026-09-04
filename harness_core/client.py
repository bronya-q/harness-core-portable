# -*- coding: utf-8 -*-
"""Stable Python client for Harness Core Portable.

Usage:
    from harness_core import MemoryClient
    mem = MemoryClient(data_dir=None)
    mem.add(scope="character:demo", content="用户把钥匙放在钟楼下", kind="manual")
    notes = mem.list(scope="character:demo")
    mem.record_event(event_type="user_correction", scope="character:demo")
    mem.record_usage(actual_tokens=640, baseline_tokens=18420, avoided_tokens=17780)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = Path(__file__).resolve().parent.parent
_SKILL = _ROOT / "harness-core"
_DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"


class _Base:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else _DATA_DIR

    def _env(self):
        env = dict(os.environ)
        env["DSH_HOME"] = str(self.data_dir.parent)
        return env

    def _run(self, script, *args):
        p = subprocess.run([sys.executable, str(_SKILL / script), *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=self._env(), timeout=30)
        try:
            return json.loads(p.stdout)
        except Exception:
            return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}


class MemoryClient(_Base):
    def add(self, scope, content, kind="manual"):
        return self._run("notebook.py", "note", "--scope", scope, "--text", content, "--kind", kind)

    def list(self, scope, limit=10, include_archived=False):
        args = ["list", "--scope", scope, "--limit", str(limit)]
        if include_archived:
            args.append("--all")
        return self._run("notebook.py", *args)

    def forget(self, note_id):
        return self._run("notebook.py", "forget", "--id", note_id)

    def restore(self, scope, version):
        return self._run("notebook.py", "restore", "--scope", scope, "--version", str(version))


class EventClient(_Base):
    def record_event(self, event_type, scope, content_type="fact", session_id=None):
        args = ["event", "add", "--scope", scope, "--event-type", event_type, "--content-type", content_type]
        if session_id:
            args += ["--session-id", session_id]
        return self._run("event_commands.py", *args)

    def list(self, limit=10):
        return self._run("event_commands.py", "event", "list", "--limit", str(limit))


class UsageClient(_Base):
    def record(self, actual_tokens, baseline_tokens=0, avoided_tokens=0, model_id="undisclosed"):
        return self._run("event_commands.py", "usage", "record",
                         "--actual", str(actual_tokens), "--baseline", str(baseline_tokens),
                         "--avoided", str(avoided_tokens), "--model", model_id)

    def summary(self):
        return self._run("event_commands.py", "usage", "summary")
