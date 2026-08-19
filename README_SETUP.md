# CRuX GPT

An AI-powered document analysis and retrieval system for insurance, legal, medical, HR, and
compliance documents. Upload PDFs/DOCX/TXT, ask questions, get grounded answers with citations.

```
crux-project/
├── frontend/   React + Vite (unchanged visual design, real backend wiring)
└── backend/    FastAPI + Gemini RAG pipeline
```

## 1. Backend setup

Try to use python 3.12 for this project cause newer versions may not support older dependencies.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Edit `backend/.env` and set:

```env
GEMINI_API_KEY=your-real-gemini-api-key
JWT_SECRET=some-long-random-string   # change this from the default
```

Get a Gemini API key at https://aistudio.google.com/apikey.

Run it:

```bash
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000/api
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

Run the test suite (uses an in-memory DB and mocked Gemini calls, so it needs no API key/network):

```bash
pytest -v
```

## 2. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_URL defaults to http://localhost:8000, adjust if needed
npm run dev
```

Open http://localhost:5173.

## 3. Try it end-to-end

1. Sign up via the "Sign In" button (switch to "Sign Up").
2. Open the chat, attach a PDF/DOCX/TXT policy document (10MB max), wait for it to reach "Ready".
3. Ask a question like "Does this policy cover knee surgery?" - the answer will cite the
   document's page/section.
4. Give the answer a 👍/👎 - it's saved to the backend.
5. Go to Chat History to see the conversation persisted; refresh the page and it's still there.
6. To see the admin dashboard, promote your user to admin directly in the database, e.g.:
   ```bash
   cd backend
   python3 -c "
   import asyncio
   from sqlalchemy import select
   from app.database import AsyncSessionLocal
   from models.user import User

   async def main():
       async with AsyncSessionLocal() as db:
           result = await db.execute(select(User).where(User.email == 'you@example.com'))
           user = result.scalar_one()
           user.role = 'admin'
           await db.commit()

   asyncio.run(main())
   "
   ```
   Then sign out and back in - the app now shows the admin dashboard for that account.

## 4. Multi-user isolation

Every document, chunk, conversation, and message is scoped to `user_id` server-side. Retrieval
always filters by the authenticated user - a document uploaded by one account is never
retrievable, listable, or citable by another. This is covered by automated tests
(`backend/tests/test_documents.py`, `backend/tests/test_chat.py`).

## 5. Swapping providers later

- **LLM / embeddings**: `backend/rag/generator.py` and `backend/rag/embeddings.py` are the only
  places that talk to Gemini. Swap in another provider by implementing the same interface.
- **Vector store**: `backend/rag/vector_store.py` does brute-force cosine similarity over
  embeddings stored in the `document_chunks` table - fine for an MVP's data volumes. Swap in
  FAISS/Qdrant/pgvector there without touching the rest of the RAG pipeline.
- **Database**: SQLite by default (`DATABASE_URL` in `.env`). Point it at Postgres
  (`postgresql+asyncpg://...`) with no model changes required.

## 6. Deployment notes

- Set `FRONTEND_URL` in the backend `.env` to your deployed frontend origin (CORS is locked to
  this, not `*`, since the API uses credentialed requests).
- Set `VITE_API_URL` in the frontend `.env` to your deployed backend URL before building
  (`npm run build`).
- Never commit real `.env` files - only `.env.example` is checked in.
