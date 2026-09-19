import hashlib
import re
import unicodedata
from collections import defaultdict

from .content import article_to_markdown, split_markdown


MANAGED_BY = "cobalt-fern-27"


def _filename(article):
    plain = unicodedata.normalize("NFKD", article["title"]).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:70]
    return f"{article['id']}-{slug or 'article'}.md"


def sync_articles(articles, store, articles_dir):
    """Write the corpus and replace only changed articles in the vector store."""
    articles_dir.mkdir(parents=True, exist_ok=True)
    existing = defaultdict(list)
    for file in store.list_files():
        attributes = file.get("attributes") or {}
        if attributes.get("managed_by") == MANAGED_BY:
            existing[str(attributes["article_id"])].append(file)

    counts = {"added": 0, "updated": 0, "skipped": 0, "chunks": 0}
    for article in articles:
        markdown = article_to_markdown(article)
        name = _filename(article)
        (articles_dir / name).write_text(markdown, encoding="utf-8")
        digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        parts = split_markdown(markdown)
        if not parts:
            raise ValueError(f"Article {article['id']} has no usable content")
        old_files = existing.get(str(article["id"]), [])
        if len(old_files) == len(parts) and all(
            file.get("status") == "completed"
            and (file.get("attributes") or {}).get("digest") == digest
            for file in old_files
        ):
            counts["skipped"] += 1
            continue

        attachments = []
        for number, content in enumerate(parts, start=1):
            upload_name = name.removesuffix(".md") + f"-part-{number}.md"
            file_id = store.upload_text(upload_name, content)
            attachments.append({
                "file_id": file_id,
                "attributes": {
                    "managed_by": MANAGED_BY,
                    "article_id": str(article["id"]),
                    "article_url": article["html_url"],
                    "digest": digest,
                    "part": number,
                    "parts": len(parts),
                },
            })
        batch_id = store.attach_many(attachments)
        store.wait_batch(batch_id)
        for file in old_files:
            store.delete_file(file["id"])

        counts["updated" if old_files else "added"] += 1
        counts["chunks"] += len(parts)
    return counts
