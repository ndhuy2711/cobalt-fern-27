# Cobalt Fern 27 — OptiBot knowledge sync

This once-and-exit job ingests 36 public OptiSigns Help Center articles from seven Zendesk sections into `articles/` and an OpenAI vector store. It uploads only new or changed articles. No keys are committed.

## Setup and local run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.sample .env
.venv/bin/python main.py
.venv/bin/python main.py  # unchanged articles are skipped
```

Set `OPENAI_API_KEY` in `.env` first. To create your own vector store:

```bash
.venv/bin/python main.py --create-store
# Copy the returned ID into OPENAI_VECTOR_STORE_ID in .env
.venv/bin/python main.py
```

API-free scrape: `python main.py --scrape-only`. API-free delta test: set `STORAGE_BACKEND=local` in `.env`. Docker: `docker build -t knowledge-sync . && docker run --rm --env-file .env knowledge-sync`.

The **Cobalt Fern OptiBot** prompt in OpenAI Playground uses the [required wording](prompt.txt) and `file_search` on the API-created store. The older Assistants API in the brief was [sunset](https://developers.openai.com/api/docs/assistants/migration); this uses Responses/file search.

## Delta and chunking

The Zendesk API supplies article bodies without navigation. Conversion preserves headings, code fences, images, and links, while removing editor notes. Each `<id>-<slug>.md` includes `Article URL:`. Upload pieces split at paragraphs, stay under 3,000 UTF-8 bytes, and repeat title and URL. OpenAI static chunking uses 4,096 tokens and zero overlap: one uploaded piece per vector chunk. Initial ingestion: **36 articles, 56 chunks**.

Vector file attributes store source ID and SHA-256. Each run compares hashes, indexes changed pieces, then removes old ones. JSON logs report `source_articles`, `added`, `updated`, `skipped`, and chunks uploaded that run.

## Daily job and evidence

The [daily workflow](https://github.com/ndhuy2711/cobalt-fern-27/actions/workflows/daily.yml) runs at 02:00 UTC. A [successful scheduled run and logs](https://github.com/ndhuy2711/cobalt-fern-27/actions/runs/35496939153) show `skipped: 36`; its [log artifact](https://github.com/ndhuy2711/cobalt-fern-27/actions/runs/35496939153/artifacts/10601371134) records counts. GitHub secrets provide the API key and store ID.

Evidence: [trial OptiBot chat](evidence/product/optibot-chat.png), [Playground answer with cited URL](evidence/answer.png). Tests: `.venv/bin/python -m unittest discover -s tests -v`.
