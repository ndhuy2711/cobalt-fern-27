import unittest

from optibot.store import OpenAIStore


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return Response(next(self.responses))


class StoreTests(unittest.TestCase):
    def test_create_vector_store_returns_id_for_configuration(self):
        session = Session([{"id": "vs-new"}])

        store_id = OpenAIStore.create_vector_store("key", "Interview knowledge", session=session)

        self.assertEqual("vs-new", store_id)
        self.assertEqual("POST", session.calls[0][0])
        self.assertTrue(session.calls[0][1].endswith("/vector_stores"))
        self.assertEqual("Interview knowledge", session.calls[0][2]["json"]["name"])

    def test_upload_text_sends_markdown_as_assistant_file(self):
        session = Session([{"id": "file-1"}])
        store = OpenAIStore("key", "vs-test", session=session)

        file_id = store.upload_text("guide.md", "# Guide")

        self.assertEqual("file-1", file_id)
        call = session.calls[0]
        self.assertEqual("POST", call[0])
        self.assertEqual("assistants", call[2]["data"]["purpose"])
        self.assertEqual("guide.md", call[2]["files"]["file"][0])

    def test_list_files_follows_openai_cursor(self):
        session = Session([
            {"data": [{"id": "file-1"}], "has_more": True, "last_id": "file-1"},
            {"data": [{"id": "file-2"}], "has_more": False},
        ])
        store = OpenAIStore("key", "vs-test", session=session)

        files = store.list_files()

        self.assertEqual(["file-1", "file-2"], [file["id"] for file in files])
        self.assertEqual("file-1", session.calls[1][2]["params"]["after"])

    def test_attach_configures_one_chunk_per_uploaded_file(self):
        session = Session([{"id": "batch-1"}])
        store = OpenAIStore("key", "vs-test", session=session)

        batch_id = store.attach_many([{"file_id": "file-1", "attributes": {"article_id": "123"}}])

        self.assertEqual("batch-1", batch_id)
        payload = session.calls[0][2]["json"]["files"][0]
        self.assertEqual("file-1", payload["file_id"])
        self.assertEqual("123", payload["attributes"]["article_id"])
        self.assertEqual(4096, payload["chunking_strategy"]["static"]["max_chunk_size_tokens"])
        self.assertEqual(0, payload["chunking_strategy"]["static"]["chunk_overlap_tokens"])

    def test_wait_batch_rejects_failed_ingestion(self):
        session = Session([{"status": "completed", "file_counts": {"failed": 1}}])
        store = OpenAIStore("key", "vs-test", session=session)

        with self.assertRaisesRegex(RuntimeError, "failed"):
            store.wait_batch("batch-1")

    def test_delete_file_removes_vector_attachment_and_uploaded_file(self):
        session = Session([{"deleted": True}, {"deleted": True}])
        store = OpenAIStore("key", "vs-test", session=session)

        store.delete_file("file-1")

        self.assertEqual(["DELETE", "DELETE"], [call[0] for call in session.calls])
        self.assertIn("/vector_stores/vs-test/files/file-1", session.calls[0][1])
        self.assertTrue(session.calls[1][1].endswith("/files/file-1"))


if __name__ == "__main__":
    unittest.main()
