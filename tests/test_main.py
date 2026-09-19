import os
import tempfile
import unittest
from contextlib import ExitStack
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from main import load_env_file, main, run_once


class Client:
    def fetch_articles(self, section_ids):
        return [{
            "id": 1,
            "title": "Guide",
            "html_url": "https://support.optisigns.com/hc/en-us/articles/1",
            "body": "<p>Instructions</p>",
        }]


class Store:
    def list_files(self):
        return []

    def upload_text(self, filename, content):
        return "file-1"

    def attach_many(self, files):
        return "batch-1"

    def wait_batch(self, batch_id):
        pass


class MainTests(unittest.TestCase):
    def test_create_store_command_outputs_new_id(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True))
            stack.enter_context(patch("main.ENV_FILE", Path("/missing/.env")))
            creator = stack.enter_context(patch("main.OpenAIStore.create_vector_store", return_value="vs-new"))
            output = stack.enter_context(patch("sys.stdout", new_callable=StringIO))

            main(["--create-store"])

        creator.assert_called_once()
        self.assertIn("vs-new", output.getvalue())

    def test_default_command_requires_api_configuration(self):
        with patch.dict(os.environ, {}, clear=True), patch("main.ENV_FILE", Path("/missing/.env")):
            with self.assertRaisesRegex(ValueError, "API_KEY"):
                main([])

    def test_scrape_only_writes_markdown_without_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            with ExitStack() as stack:
                stack.enter_context(patch.dict(os.environ, {}, clear=True))
                stack.enter_context(patch("main.ENV_FILE", Path(directory) / ".env"))
                stack.enter_context(patch("main.ARTICLES_DIR", Path(directory) / "articles"))
                stack.enter_context(patch("main.MIN_ARTICLES", 1))
                stack.enter_context(patch("main.ZendeskClient", return_value=Client()))
                main(["--scrape-only"])
            self.assertEqual(1, len(list((Path(directory) / "articles").glob("*.md"))))

    def test_rejects_too_small_a_corpus_before_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "at least 2"):
                run_once(Client(), Store(), Path(directory), [7], min_articles=2)

    def test_run_once_reports_source_article_count(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_once(Client(), Store(), Path(directory), [7], min_articles=1)

        self.assertEqual(1, result["source_articles"])
        self.assertEqual(1, result["added"])

    def test_env_file_supplies_missing_values_without_overriding_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("API_KEY=from-file\nVECTOR_STORE_ID=vs-demo\n")
            with patch.dict(os.environ, {"API_KEY": "already-set"}, clear=True):
                load_env_file(path)
                self.assertEqual("already-set", os.environ["API_KEY"])
                self.assertEqual("vs-demo", os.environ["VECTOR_STORE_ID"])


if __name__ == "__main__":
    unittest.main()
