# -*- coding: utf-8 -*-
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path.cwd()
SKILL = ROOT / "harness-core"


class VectorQueueDeferredTest(unittest.TestCase):
    def test_skip_unavailable_defers_instead_of_done(self):
        home = Path(tempfile.mkdtemp())
        mem_dir = home / "memory-emotion"
        os.environ["DSH_HOME"] = str(home)
        os.environ["MEMORY_EMOTION_DATA_DIR"] = str(mem_dir)
        sys.path.insert(0, str(SKILL))
        try:
            import memory_store as ms
            import vector_queue
            import vector_worker

            conn = ms.connect()
            conn.execute(
                "INSERT INTO memories (scope, content, kind, importance, valence, arousal, "
                "created_at, updated_at, archived) VALUES (?,?,?,?,?,?,?,?,0)",
                ("character:demo-archivist", "测试向量队列延迟语义", "fact",
                 0.5, 0.0, 0.5, ms.now_iso(), ms.now_iso()),
            )
            conn.commit()
            mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()

            self.assertTrue(vector_queue.enqueue(mid))

            def boom(_text):
                raise OSError("Connection refused")

            vector_worker._embed = boom
            result = vector_worker.run(limit=10, skip_unavailable=True, retry_interval=100)
            done, failed, skipped, deferred, scanned = result
            self.assertEqual(deferred, 1)
            self.assertEqual(scanned, 1)
            self.assertEqual(done, 0)

            con = vector_queue._connect()
            con.row_factory = __import__("sqlite3").Row
            row = con.execute(
                "SELECT status, done_at, next_retry_at, attempts, retry_count, last_error "
                "FROM queue WHERE memory_id=?",
                (mid,),
            ).fetchone()
            self.assertEqual(row["status"], "deferred")
            self.assertIsNone(row["done_at"])
            self.assertIsNotNone(row["next_retry_at"])
            self.assertGreater(row["next_retry_at"], time.time())
            self.assertEqual(row["retry_count"], 1)
            self.assertIn("Connection refused", row["last_error"])
            con.close()
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
