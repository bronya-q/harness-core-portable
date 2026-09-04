#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harness-core/mcp_server.py — wrapper for minimal MCP server. Run via harness.py mcp serve."""
import runpy
import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
runpy.run_path(str(Path(__file__).resolve().parent.parent / "harness_core" / "adapters" / "mcp_server.py"), run_name="__main__")
