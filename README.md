# Claritax

Initial full-stack project scaffold with separate `backend/` and `frontend/` folders.

## Requirements
- Python 3.11+
- Node.js 20+ and npm

## Backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000  
Health: http://127.0.0.1:8000/health  
Swagger: http://127.0.0.1:8000/docs

## Frontend
Open a second terminal:
```bash
cd frontend
npm install
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
npm run dev
```
Frontend: http://localhost:5173

## Notes
This is a setup scaffold for Task 1. OCR, tax extraction, LLM workflows, persistence, authentication, and production security are not implemented yet.
