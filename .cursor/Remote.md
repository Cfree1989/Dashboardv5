# Remote (Home) Setup

## Prerequisites
- Docker Desktop and Git (recommended)
- Optional (non-Docker): Python 3.11+, Node.js 18+

## Option 1 — Docker (recommended)
1. Clone and start:
   ```powershell
   git clone <your-repo-url> C:\Dashboardv5
   cd C:\Dashboardv5
   docker compose up -d --build
   ```
2. DB migrate and optional seed:
   ```powershell
   docker compose exec backend flask db upgrade
   docker compose exec backend flask seed-data
   ```
3. Open:
   - Frontend: http://localhost:3000
   - API health: http://localhost:5000/health
4. Login (sample):
   - Workstation: front-desk
   - Password: password123
5. Stop/Logs:
   ```powershell
   docker compose down
   docker compose logs backend -f
   ```

## Option 2 — Without Docker (local dev)
Backend (Flask + SQLite by default):
```powershell
cd C:\Dashboardv5
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
$env:FLASK_APP="run.py"
$env:FLASK_ENV="development"
flask db upgrade
python run.py
```

Frontend (Next.js):
- Either map host `backend` → `127.0.0.1` (Notepad as Admin → edit `C:\Windows\System32\drivers\etc\hosts`):
  ```
  127.0.0.1 backend
  ```
  Then:
  ```powershell
  cd C:\Dashboardv5\frontend
  npm install
  npm run dev
  ```
- Or change `frontend/next.config.js` rewrite destination to `http://localhost:5000/api/v1` and restart `npm run dev`.

Open http://localhost:3000. Login with `front-desk` / `password123`.

## Running tests
```powershell
cd C:\Dashboardv5
.\.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

## Notes
- Email is optional; if `MAIL_*` isn’t set, sends are skipped.
- Files save under `storage\`.
- Health check: http://localhost:5000/health