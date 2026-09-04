# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path

from harness_core import MemoryClient, EventClient, UsageClient


class HarnessCoreAPITest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="harness-api-test-"))
        self.data_dir = self.home / ".dsh" / "memory-emotion"
        os.environ["DSH_HOME"] = str(self.home / ".dsh")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.home, ignore_errors=True)
        os.environ.pop("DSH_HOME", None)

    def test_memory_client(self):
        mc = MemoryClient(data_dir=str(self.data_dir))
        r = mc.add("character:demo", "blue key", "manual")
        self.assertTrue(r.get("ok"))
        notes = mc.list("character:demo")
        self.assertEqual(len(notes.get("notes", [])), 1)

    def test_event_usage_clients(self):
        ec = EventClient(data_dir=str(self.data_dir))
        r = ec.record_event("user_correction", "character:demo")
        self.assertTrue(r.get("ok"))
        uc = UsageClient(data_dir=str(self.data_dir))
        r = uc.record(640, 18420, 17780)
        self.assertTrue(r.get("ok"))
        s = uc.summary()
        self.assertEqual(s.get("rows"), 1)


if __name__ == "__main__":
    unittest.main()
