import unittest

from optibot.content import article_to_markdown, split_markdown


class ContentTests(unittest.TestCase):
    def test_article_conversion_preserves_structure_and_source(self):
        article = {
            "id": 123,
            "title": "Add a YouTube video",
            "html_url": "https://support.optisigns.com/hc/en-us/articles/123-youtube",
            "body": (
                '<nav>Menu</nav><h2>Setup</h2><p>Open '
                '<a href="/hc/en-us/articles/456">this guide</a>.</p>'
                '<pre><code class="language-python">print("hi")\n</code></pre>'
                '<aside>Advertisement</aside>'
            ),
        }

        markdown = article_to_markdown(article)

        self.assertIn("# Add a YouTube video", markdown)
        self.assertIn("Article URL: https://support.optisigns.com/hc/en-us/articles/123-youtube", markdown)
        self.assertIn("## Setup", markdown)
        self.assertIn("[this guide](/hc/en-us/articles/456)", markdown)
        self.assertIn('```python\nprint("hi")\n```', markdown)
        self.assertNotIn("Menu", markdown)
        self.assertNotIn("Advertisement", markdown)

    def test_chunking_repeats_article_url_and_limits_bytes(self):
        url = "https://support.optisigns.com/hc/en-us/articles/123-youtube"
        markdown = "# Add a YouTube video\n\nArticle URL: " + url + "\n\n"
        markdown += "\n\n".join(f"Paragraph {number}: " + "words " * 60 for number in range(8))

        chunks = split_markdown(markdown, max_bytes=750)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.encode("utf-8")) <= 750 for chunk in chunks))
        self.assertTrue(all(f"Article URL: {url}" in chunk for chunk in chunks))
        for number in range(8):
            self.assertIn(f"Paragraph {number}:", "\n".join(chunks))

    def test_editorial_notes_are_removed_from_public_article_body(self):
        article = {
            "id": 123,
            "title": "Playlist settings",
            "html_url": "https://support.optisigns.com/hc/en-us/articles/123",
            "body": (
                "<h2><strong>Settings</strong></h2>"
                "<p>Choose a duration.</p>"
                "<p><strong>EDITOR’S NOTE — delete before publishing</strong></p>"
                "<ul><li>Keep this setting.<br>"
                "<span><strong>EDITOR’S NOTE — also delete this note</strong></span>"
                "</li></ul>"
            ),
        }

        markdown = article_to_markdown(article)

        self.assertIn("## Settings", markdown)
        self.assertIn("Choose a duration.", markdown)
        self.assertIn("Keep this setting.", markdown)
        self.assertNotIn("EDITOR", markdown)

    def test_chunk_byte_limit_includes_final_newline(self):
        prefix = "# Guide\n\nArticle URL: https://example.com/guide\n\n"
        max_bytes = len(prefix.encode("utf-8")) + 100
        markdown = prefix + "x" * 100

        chunks = split_markdown(markdown, max_bytes=max_bytes)

        self.assertTrue(all(len(chunk.encode("utf-8")) <= max_bytes for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
