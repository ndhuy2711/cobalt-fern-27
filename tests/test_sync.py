import tempfile
import unittest
from pathlib import Path

from optibot.sync import sync_articles


class MemoryStore:
    def __init__(self):
        self.files = {}
        self.uploaded = []
        self.deleted = []

    def list_files(self):
        return list(self.files.values())

    def upload_text(self, filename, content):
        file_id = f"file-{len(self.uploaded) + 1}"
        self.uploaded.append((file_id, filename, content))
        return file_id

    def attach_many(self, files):
        for item in files:
            self.files[item["file_id"]] = {
                "id": item["file_id"],
                "status": "completed",
                "attributes": item["attributes"],
            }
        return "batch-1"

    def wait_batch(self, batch_id):
        return None

    def delete_file(self, file_id):
        self.deleted.append(file_id)
        del self.files[file_id]


def article(body):
    return {
        "id": 123,
        "title": "Add YouTube",
        "html_url": "https://support.optisigns.com/hc/en-us/articles/123",
        "body": f"<p>{body}</p>",
    }


class SyncTests(unittest.TestCase):
    def test_first_run_uploads_and_second_run_skips(self):
        store = MemoryStore()
        with tempfile.TemporaryDirectory() as directory:
            first = sync_articles([article("Watch a video")], store, Path(directory))
            second = sync_articles([article("Watch a video")], store, Path(directory))

            self.assertEqual({"added": 1, "updated": 0, "skipped": 0, "chunks": 1}, first)
            self.assertEqual({"added": 0, "updated": 0, "skipped": 1, "chunks": 0}, second)
            self.assertEqual(1, len(store.uploaded))
            self.assertEqual(1, len(list(Path(directory).glob("*.md"))))

    def test_update_replaces_old_index_file(self):
        store = MemoryStore()
        with tempfile.TemporaryDirectory() as directory:
            sync_articles([article("Old instructions")], store, Path(directory))
            old_id = next(iter(store.files))

            result = sync_articles([article("New instructions")], store, Path(directory))

            self.assertEqual({"added": 0, "updated": 1, "skipped": 0, "chunks": 1}, result)
            self.assertEqual([old_id], store.deleted)
            self.assertEqual(1, len(store.files))
            self.assertIn("New instructions", store.uploaded[-1][2])


if __name__ == "__main__":
    unittest.main()
