import unittest

from optibot.zendesk import ZendeskClient


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class Session:
    def __init__(self, pages):
        self.pages = pages
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        return Response(self.pages[url])


class ZendeskTests(unittest.TestCase):
    def test_fetches_every_page_and_deduplicates_articles(self):
        first = "https://support.optisigns.com/api/v2/help_center/en-us/sections/7/articles.json?per_page=100"
        second = "https://support.optisigns.com/api/v2/help_center/en-us/sections/7/articles.json?page=2"
        article = {"id": 1, "title": "One", "html_url": "https://example.com/1", "body": "<p>One</p>"}
        session = Session({
            first: {"articles": [article], "next_page": second},
            second: {"articles": [article, {"id": 2, "draft": True, "body": "draft"}], "next_page": None},
        })

        articles = ZendeskClient(session=session).fetch_articles([7])

        self.assertEqual([article], articles)
        self.assertEqual([first, second], session.urls)


if __name__ == "__main__":
    unittest.main()
