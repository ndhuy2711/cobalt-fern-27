import re

from bs4 import BeautifulSoup
from markdownify import markdownify


def article_to_markdown(article):
    """Convert a Zendesk article body into a source-labelled Markdown file."""
    soup = BeautifulSoup(article.get("body") or "", "html.parser")
    for element in soup.select("nav, aside, header, footer, script, style, .advertisement, .ads"):
        element.decompose()
    for paragraph in soup.find_all(["p", "span"]):
        note = paragraph.get_text(" ", strip=True).lower()
        if note.startswith(("editor’s note", "editor's note")):
            paragraph.decompose()
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        if not heading.get_text(" ", strip=True):
            heading.decompose()
            continue
        strong = heading.find("strong")
        if strong and heading.get_text(" ", strip=True) == strong.get_text(" ", strip=True):
            strong.unwrap()

    code_blocks = {}
    for number, pre in enumerate(soup.find_all("pre")):
        for line_break in pre.find_all("br"):
            line_break.replace_with("\n")
        code = pre.find("code")
        language = ""
        if code:
            for css_class in code.get("class", []):
                if css_class.startswith("language-"):
                    language = css_class.removeprefix("language-")
                    break
        raw_code = (code or pre).get_text().strip("\n")
        marker = f"OPTIBOTCODEBLOCK{number}END"
        code_blocks[marker] = f"```{language}\n{raw_code}\n```"
        pre.replace_with(marker)

    body = markdownify(str(soup), heading_style="ATX", bullets="-")
    for marker, fenced_code in code_blocks.items():
        body = body.replace(marker, f"\n\n{fenced_code}\n\n")
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    title = str(article["title"]).strip()
    if body.startswith(f"# {title}\n"):
        body = body[len(title) + 3 :].lstrip()
    url = str(article["html_url"]).strip()
    return f"# {title}\n\nArticle URL: {url}\n\n{body}\n"


def split_markdown(markdown, max_bytes=3000):
    """Create upload files small enough for one 4096-token static vector chunk."""
    title, source, body = markdown.strip().split("\n\n", 2)
    prefix = f"{title}\n\n{source}\n\n"
    capacity = max_bytes - len(prefix.encode("utf-8")) - 1  # final newline
    if capacity < 16:
        raise ValueError("max_bytes is too small for article metadata")

    pieces = []
    for block in re.split(r"\n{2,}", body.strip()):
        if not block:
            continue
        if len(block.encode("utf-8")) <= capacity:
            pieces.append(block)
            continue
        words = block.split()
        current = ""
        for word in words:
            if len(word.encode("utf-8")) > capacity:
                if current:
                    pieces.append(current)
                    current = ""
                segment = ""
                for character in word:
                    if len((segment + character).encode("utf-8")) > capacity:
                        pieces.append(segment)
                        segment = character
                    else:
                        segment += character
                if segment:
                    pieces.append(segment)
                continue
            candidate = f"{current} {word}" if current else word
            if len(candidate.encode("utf-8")) > capacity and current:
                pieces.append(current)
                current = word
            else:
                current = candidate
        if current:
            pieces.append(current)

    chunks = []
    current = ""
    for piece in pieces:
        candidate = f"{current}\n\n{piece}" if current else piece
        if len(candidate.encode("utf-8")) > capacity and current:
            chunks.append(prefix + current + "\n")
            current = piece
        else:
            current = candidate
    if current:
        chunks.append(prefix + current + "\n")
    return chunks
