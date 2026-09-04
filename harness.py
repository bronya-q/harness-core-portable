#!/usr/bin/env python3
"""Root launcher — forwards to harness-core/harness.py."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve()))
runpy.run_path(str(Path(__file__).resolve().parent / "harness-core" / "harness.py"), run_name="__main__")
