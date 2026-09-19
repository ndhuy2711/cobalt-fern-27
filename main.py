import argparse
import json
import os
from pathlib import Path

from optibot.content import article_to_markdown
from optibot.store import OpenAIStore
from optibot.sync import _filename, sync_articles
from optibot.zendesk import ZendeskClient


PROJECT_DIR = Path(__file__).resolve().parent
ENV_FILE = PROJECT_DIR / ".env"
ARTICLES_DIR = PROJECT_DIR / "articles"
MIN_ARTICLES = 30
SECTION_IDS = [
    26318906819091,  # How To Use Apps
    26324076807315,  # YouTube & Other Video Platforms
    26324652803475,  # Playlist
    26324698105235,  # Schedule
    26319069331219,  # Files/Assets Management
    26398357451923,  # Getting Started
    27458218745235,  # Screens Management
]


def load_env_file(path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def run_once(client, store, articles_dir, section_ids, min_articles=30):
    articles = client.fetch_articles(section_ids)
    if len(articles) < min_articles:
        raise ValueError(f"Expected at least {min_articles} source articles, found {len(articles)}")
    counts = sync_articles(articles, store, articles_dir)
    return {"source_articles": len(articles), **counts}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Daily OptiBot knowledge-base sync")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scrape-only", action="store_true", help="write Markdown without OpenAI upload")
    mode.add_argument("--create-store", action="store_true", help="create an OpenAI vector store")
    args = parser.parse_args(argv)
    load_env_file(ENV_FILE)

    if args.create_store:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            raise ValueError("Set OPENAI_API_KEY or API_KEY in .env or the environment")
        store_id = OpenAIStore.create_vector_store(api_key, "Cobalt Fern support knowledge")
        print(json.dumps({"vector_store_id": store_id}))
        return

    if args.scrape_only:
        articles = ZendeskClient().fetch_articles(SECTION_IDS)
        if len(articles) < MIN_ARTICLES:
            raise ValueError(f"Expected at least {MIN_ARTICLES} source articles, found {len(articles)}")
        ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
        for article in articles:
            (ARTICLES_DIR / _filename(article)).write_text(
                article_to_markdown(article), encoding="utf-8"
            )
        print(json.dumps({"source_articles": len(articles), "markdown_files": len(articles)}))
        return

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY or API_KEY in .env or the environment")
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID") or os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        raise ValueError("Set OPENAI_VECTOR_STORE_ID or VECTOR_STORE_ID")

    result = run_once(
        ZendeskClient(), OpenAIStore(api_key, vector_store_id), ARTICLES_DIR, SECTION_IDS, MIN_ARTICLES
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
