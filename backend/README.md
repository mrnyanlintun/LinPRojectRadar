# lin-project-radar — Stage 2 backend (FastAPI)

A FastAPI port of the Apps Script (v9) endpoints. It runs **alongside** the
existing Apps Script demo — the front end is not switched over by this PR. Storage
is a simple JSON file (`data/projects.json`); Stage 3 swaps it for Postgres.

`apiVersion`: **`lin-project-radar-backend-v2.0`**

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/health` | `{ ok, apiVersion }` |
| GET  | `/list`, `/listarchived`, `/get?id=` | project reads |
| POST | `/create`, `/save`, `/archive`, `/restore` | project writes |
| POST | `/chat` | OpenAI assistant (optional governance synthesis when `signal_array` is sent) |
| POST | `/analyze` | document-risk summary (+ optional spec compare) |
| POST | `/extractsignals` | pypdf text → OpenAI extraction → multimodal fallback; Isolation-Forest pre-screen |
| POST | `/overwritesignal`, `/resetsignals` | signal corrections / clear |
| POST | `/simulate` | five Python simulation models (PERT/LOB/CCPM/RCF/DSM) |
| POST | `/ingestcorpus`, GET `/listcorpus?id=`, POST `/audit` | Technical Auditor RAG |
| POST | `/tts` | placeholder (TTS stays client-side this tier) |

## Local run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add OPENAI_API_KEY
uvicorn main:app --reload --port 8080
# → http://localhost:8080/health
```

All OpenAI calls read `OPENAI_API_KEY` from the environment — **no keys in
source**. Without a key the service still runs: extraction falls back to regex,
`/simulate` and the governance router are fully offline, and chat/analyze/audit
return a clear "AI not configured" message.

## Docker

```bash
cd backend
docker build -t lpr-backend .
docker run -p 8080:8080 --env-file .env lpr-backend
```

## Deploy

- **Cloud Run:** `gcloud run deploy lpr-backend --source backend --region <r> --set-env-vars OPENAI_API_KEY=...` (container listens on `$PORT`).
- **Render:** `render.yaml` is a Blueprint — set `OPENAI_API_KEY` (and `HF_API_KEY`) as dashboard secrets; health check is `/health`.

## Notes

- CORS is open (`allow_origins=["*"]`) to match the Apps Script behaviour.
- Corpus files + `requirements_db.json` are written under `data/corpus/<projectId>/`
  (git-ignored). Item 23's RAG retrieval reads that store during `/audit`.
- The five simulation models mirror the front-end `simulations.js`; `/simulate`
  returns the same `{ method_class, status_color, evidence_metric, … }` shape.
