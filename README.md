# Cobalt Fern 27 — OptiBot knowledge sync

This job reads 36 public OptiSigns Help Center articles from seven Zendesk sections, saves clean Markdown in `articles/`, and uploads only new or changed content to an OpenAI vector store. It runs once and exits. No keys are committed.

## Setup and local run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py  # .env uses a persistent local test store
.venv/bin/python main.py  # unchanged articles are skipped
```

For the real vector store, copy `.env.sample` to `.env`, set `OPENAI_API_KEY`, then run:

```bash
.venv/bin/python main.py --create-store
# Copy the returned ID into OPENAI_VECTOR_STORE_ID in .env
.venv/bin/python main.py
```

Use `python main.py --scrape-only` to refresh Markdown without any store. For Docker: `docker build -t knowledge-sync .`, then `docker run --rm --env-file .env knowledge-sync`. Local mode simulates indexing and does not call OpenAI; only the `openai` backend satisfies the API-upload requirement.

The **Cobalt Fern OptiBot** prompt was published in OpenAI Playground with the **exact** text in [`prompt.txt`](prompt.txt) and `file_search` attached to the API-created vector store. Asking **“How do I add a YouTube video?”** returned a step-by-step answer with the source article URL. The older Assistants API named in the brief was [sunset on August 26, 2026](https://developers.openai.com/api/docs/assistants/migration); this submission uses the current Playground chat interface with Responses/file search.

## Delta and chunking

The public Zendesk API supplies article bodies without site navigation. The converter preserves headings, code fences, images, and links, and removes editor notes. Each article becomes one `<id>-<slug>.md` file with an `Article URL:` line. For upload, each file is split by paragraphs into UTF-8 pieces of at most 3,000 bytes; every piece repeats the title and URL. OpenAI uses static 4,096-token chunks with zero overlap, so each uploaded piece forms one chunk. The first corpus has **36 article files and 56 upload chunks**.

Vector file attributes hold the source ID and SHA-256 of the normalized Markdown. A daily run compares these attributes, uploads changed pieces, waits for indexing, then removes superseded pieces. Its JSON log reports `source_articles`, `added`, `updated`, `skipped`, and `chunks` embedded on that run.

## Daily job and evidence

[Daily job runs and logs](https://github.com/ndhuy2711/cobalt-fern-27/actions/workflows/daily.yml) run at 02:00 UTC and can be triggered manually. The workflow builds the Docker image and saves `job.log` as a run artifact. Set repository secrets `OPENAI_API_KEY` and `OPENAI_VECTOR_STORE_ID` before triggering it.

Sample Playground answer and cited URL: [`evidence/answer.png`](evidence/answer.png). Run tests with `.venv/bin/python -m unittest discover -s tests -v`.
