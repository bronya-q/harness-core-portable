# -*- coding: utf-8 -*-
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic-memory-interop"


def load_runner():
    spec = importlib.util.spec_from_file_location("synthetic_memory_interop", EXAMPLE / "run_scenario.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SyntheticMemoryInteropTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()
        cls.data = json.loads((EXAMPLE / "scenario.json").read_text(encoding="utf-8"))
        cls.trace = cls.runner.build_trace(cls.data)

    def test_fixture_is_synthetic_and_has_no_live_integration_claim(self):
        self.assertEqual(self.data["fixture_kind"], "synthetic")
        self.assertEqual(self.data["integration_status"], "contract_fixture_only")
        self.assertFalse(self.data["boundaries"]["private_data"])
        self.assertFalse(self.data["boundaries"]["network"])
        self.assertFalse(self.data["boundaries"]["external_actions"])
        self.assertFalse(self.data["boundaries"]["rawmem_connected"])
        self.assertFalse(self.data["boundaries"]["memdsl_connected"])
        self.assertEqual(self.data["boundaries"]["autonomous_tasks"], "disabled")

    def test_all_contract_checks_pass(self):
        self.assertTrue(self.trace["summary"]["ok"], self.trace["checks"])

    def test_pending_candidate_is_not_provided_as_active_memory(self):
        row = next(x for x in self.trace["requests"] if x["phase"] == "before_approval")
        self.assertEqual(row["provided_memory_ids"], [])

    def test_current_turn_override_does_not_create_candidate(self):
        row = next(x for x in self.trace["requests"] if x["phase"] == "current_turn_override")
        self.assertFalse(row["creates_candidate"])
        self.assertEqual(row["memory_effects"]["memory-001"], "overridden_by_current_intent")
        self.assertEqual(row["response_mode"], "detailed")

    def test_specific_preference_coexists_with_general_preference(self):
        candidate = next(x for x in self.data["candidates"] if x["candidate_id"] == "candidate-002")
        self.assertNotIn("supersedes", candidate)
        row = next(x for x in self.trace["requests"] if x["phase"] == "contextual_preference")
        self.assertEqual(row["memory_effects"]["memory-002"], "selected_specific_preference")

    def test_memory_does_not_grant_external_action_permission(self):
        row = next(x for x in self.trace["requests"] if x["phase"] == "permission_separation")
        self.assertEqual(row["permission"], "confirmation_required")
        self.assertFalse(row["executed"])

    def test_explicit_correction_supersedes_but_keeps_history(self):
        ids = {x["memory_id"] for x in self.data["candidates"]}
        self.assertIn("memory-001", ids)
        replacement = next(x for x in self.data["candidates"] if x["memory_id"] == "memory-004")
        self.assertEqual(replacement["supersedes"], ["memory-001"])
        row = next(x for x in self.trace["requests"] if x["phase"] == "after_correction")
        self.assertEqual(row["excluded_memory_ids"]["memory-001"], "superseded")
        self.assertNotIn("memory-001", row["provided_memory_ids"])

    def test_generated_markdown_names_actual_model_inputs(self):
        text = self.runner.render_markdown(self.trace)
        self.assertIn("Memories actually provided to model", text)
        self.assertIn("memory-004", text)
        self.assertIn("confirmation_required", text)
        self.assertIn("Review results", text)
        self.assertIn("实际提供给模型", text)
        self.assertIn("我可以先准备发布步骤", text)


if __name__ == "__main__":
    unittest.main()
