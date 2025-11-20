HEAD
# support-ticket-triage-llm

        # Support Ticket Triage — Take-home Assignment (LLM-enabled)


        This repo implements a small AI agent for triaging support tickets using OpenAI.

## What it does

- Extracts `summary`, `category`, `severity` from free-text ticket.
- Searches a small KB of known issues and returns top matches.
- Uses an LLM (OpenAI) to decide `known_issue` vs `new_issue` and suggest next action.
- Exposes a FastAPI endpoint `POST /triage` with body `{ "description": "..." }`.

## Quick start

1. Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`.

2. Create venv and activate:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

4. Call the endpoint:

```bash
curl -X POST "http://localhost:8000/triage" -H "Content-Type: application/json" -d '{"description":"Checkout failing with 500 on mobile"}'
```

## Production considerations

- Containerize (Dockerfile included) and deploy to Cloud Run/ECS.
- Store secrets in a secrets manager (AWS Secrets Manager / GCP Secret Manager) and not in code.
- Add logging, metrics (Prometheus), and tracing.
- Use a vector DB for semantic KB search in production.
- Add retries and rate limiting around LLM calls to control cost.

## Design notes

- `agent/orchestrator.py` orchestrates the flow: KB search -> LLM prompt -> parse JSON.
- `tools/kb_search.py` implements a simple Jaccard-based matching; easy to replace with TF-IDF or embeddings.
- LLM calls live in `agent/llm.py` and require `OPENAI_API_KEY` and `OPENAI_MODEL` env vars.

## Tests

Run `pytest -q`. Tests that require OpenAI will fail if `OPENAI_API_KEY` isn't set; they check error handling for missing key.

9d27742 (Initial commit: Support ticket triage project)
