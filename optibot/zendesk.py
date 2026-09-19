from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ZendeskClient:
    def __init__(self, session=None):
        if session is None:
            session = requests.Session()
            retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session = session

    def fetch_articles(self, section_ids):
        articles = {}
        for section_id in section_ids:
            url = (
                "https://support.optisigns.com/api/v2/help_center/en-us/sections/"
                f"{section_id}/articles.json?per_page=100"
            )
            seen_pages = set()
            while url:
                if url in seen_pages:
                    raise ValueError(f"Zendesk pagination loop: {url}")
                if urlparse(url).hostname != "support.optisigns.com":
                    raise ValueError(f"Unexpected Zendesk pagination host: {url}")
                seen_pages.add(url)
                response = self.session.get(url, timeout=20)
                response.raise_for_status()
                payload = response.json()
                for article in payload["articles"]:
                    if not article.get("draft") and article.get("body"):
                        articles[article["id"]] = article
                url = payload.get("next_page")
        return list(articles.values())
