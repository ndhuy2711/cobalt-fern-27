import time

import requests


class OpenAIStore:
    @classmethod
    def create_vector_store(cls, api_key, name, session=None):
        store = cls(api_key, "", session=session)
        return store._request("POST", "/vector_stores", json={"name": name})["id"]

    def __init__(self, api_key, vector_store_id, session=None):
        self.session = session or requests.Session()
        self.vector_store_id = vector_store_id
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.base_url = "https://api.openai.com/v1"

    def _request(self, method, path, **kwargs):
        response = self.session.request(
            method,
            self.base_url + path,
            headers=self.headers,
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def list_files(self):
        files = []
        after = None
        while True:
            params = {"limit": 100}
            if after:
                params["after"] = after
            page = self._request(
                "GET", f"/vector_stores/{self.vector_store_id}/files", params=params
            )
            files.extend(page["data"])
            if not page.get("has_more"):
                return files
            after = page.get("last_id") or files[-1]["id"]

    def attach_many(self, files):
        items = []
        for file in files:
            items.append({
                **file,
                "chunking_strategy": {
                    "type": "static",
                    "static": {"max_chunk_size_tokens": 4096, "chunk_overlap_tokens": 0},
                },
            })
        result = self._request(
            "POST",
            f"/vector_stores/{self.vector_store_id}/file_batches",
            json={"files": items},
        )
        return result["id"]

    def upload_text(self, filename, content):
        result = self._request(
            "POST",
            "/files",
            data={"purpose": "assistants"},
            files={"file": (filename, content.encode("utf-8"), "text/markdown")},
        )
        return result["id"]

    def wait_batch(self, batch_id):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            batch = self._request(
                "GET", f"/vector_stores/{self.vector_store_id}/file_batches/{batch_id}"
            )
            status = batch["status"]
            if status == "completed":
                if batch.get("file_counts", {}).get("failed", 0):
                    raise RuntimeError(f"Vector ingestion failed: {batch['file_counts']}")
                return
            if status in {"failed", "cancelled"}:
                raise RuntimeError(f"Vector ingestion {status}: {batch}")
            time.sleep(2)
        raise TimeoutError(f"Vector ingestion timed out for {batch_id}")

    def delete_file(self, file_id):
        self._request("DELETE", f"/vector_stores/{self.vector_store_id}/files/{file_id}")
        self._request("DELETE", f"/files/{file_id}")
