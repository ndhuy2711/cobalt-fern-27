import json
from pathlib import Path
from uuid import uuid4


class LocalStore:
    def __init__(self, root):
        self.root = Path(root)
        self.uploads = self.root / "uploads"
        self.uploads.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"

    def _read_index(self):
        if not self.index.exists():
            return {}
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _write_index(self, files):
        temporary = self.index.with_suffix(".tmp")
        temporary.write_text(json.dumps(files, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.index)

    def list_files(self):
        return list(self._read_index().values())

    def upload_text(self, filename, content):
        file_id = f"local-{uuid4().hex}"
        (self.uploads / f"{file_id}.md").write_text(content, encoding="utf-8")
        return file_id

    def attach_many(self, files):
        index = self._read_index()
        for file in files:
            file_id = file["file_id"]
            index[file_id] = {
                "id": file_id,
                "status": "completed",
                "attributes": file["attributes"],
            }
        self._write_index(index)
        return f"local-batch-{uuid4().hex}"

    def wait_batch(self, batch_id):
        return None

    def delete_file(self, file_id):
        index = self._read_index()
        index.pop(file_id, None)
        self._write_index(index)
        (self.uploads / f"{file_id}.md").unlink(missing_ok=True)
