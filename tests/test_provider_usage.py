# -*- coding: utf-8 -*-
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()
SKILL = ROOT / "harness-core"


class ProviderUsageTest(unittest.TestCase):
    def test_roleplay_usage_aggregation(self):
        home = Path(tempfile.mkdtemp())
        os.environ["DSH_HOME"] = str(home)
        sys.path.insert(0, str(SKILL))
        try:
            from roleplay_memory_chat import _accumulate_provider_usage
            agg = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "duration_ms": 0.0}
            _accumulate_provider_usage(agg, {"prompt_eval_count": 10, "eval_count": 5, "duration_ms": 100.0})
            _accumulate_provider_usage(agg, {"prompt_eval_count": 20, "eval_count": 8, "duration_ms": 150.0})
            self.assertEqual(agg["calls"], 2)
            self.assertEqual(agg["prompt_tokens"], 30)
            self.assertEqual(agg["completion_tokens"], 13)
            self.assertEqual(agg["total_tokens"], 43)
            self.assertAlmostEqual(agg["duration_ms"], 250.0)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_event_store_records_provider_fields(self):
        home = Path(tempfile.mkdtemp())
        os.environ["DSH_HOME"] = str(home)
        sys.path.insert(0, str(SKILL))
        try:
            from event_store import record_usage, list_usage
            uid = record_usage({
                "usage_source": "provider_reported",
                "provider": "ollama",
                "model_id": "qwen3-embedding:0.6b",
                "actual_tokens": 43,
                "prompt_tokens": 30,
                "completion_tokens": 13,
                "components": {"provider": "ollama", "calls": 2},
            })
            self.assertGreater(uid, 0)
            rows = list_usage(limit=10)
            self.assertEqual(rows[0]["provider"], "ollama")
            self.assertEqual(rows[0]["prompt_tokens"], 30)
            self.assertEqual(rows[0]["completion_tokens"], 13)
            self.assertEqual(rows[0]["usage_source"], "provider_reported")
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
