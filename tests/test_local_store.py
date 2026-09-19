import tempfile
import unittest
from pathlib import Path

from optibot.local_store import LocalStore


class LocalStoreTests(unittest.TestCase):
    def test_index_survives_a_new_process_and_supports_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = LocalStore(root)
            file_id = first.upload_text("guide.md", "# Guide")
            first.attach_many([{"file_id": file_id, "attributes": {"article_id": "123"}}])

            second = LocalStore(root)
            files = second.list_files()
            self.assertEqual(1, len(files))
            self.assertEqual("123", files[0]["attributes"]["article_id"])
            self.assertIn("# Guide", (root / "uploads" / f"{file_id}.md").read_text())

            second.delete_file(file_id)
            self.assertEqual([], LocalStore(root).list_files())
            self.assertFalse((root / "uploads" / f"{file_id}.md").exists())


if __name__ == "__main__":
    unittest.main()
