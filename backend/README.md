# Backend PoC

This folder contains a minimal FastAPI PoC for the Multi-Tenant Customer Support platform.

Quick start (Windows PowerShell):

```powershell
cd "c:\Users\yukai\114-project\backend"
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Endpoints (PoC):
- POST /v1/tenants/{tenant_id}/chat
- POST /v1/tenants/{tenant_id}/documents/upload
- POST /v1/tenants/{tenant_id}/models
- GET  /v1/tenants/{tenant_id}/analytics

Notes:
- This PoC uses in-memory stores and stubbed model calls. It's intended as a starting point for API and integration tests.
- For production, replace storage with persistent DB, implement real embeddings/vector DB, secure token validation, and add observability.
