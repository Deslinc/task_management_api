# FastAPI + Firebase Auth + SQL Task Manager

A learning-friendly starter that uses **Firebase Authentication** for sign-up/login
and **SQL (MySql)** for the main app data (tasks). Built with **FastAPI**.

---

## What you'll learn

1. How to wire Firebase Authentication (Email/Password) to a FastAPI backend.
2. How to verify Firebase ID tokens on each request.
3. How to persist user profiles and tasks in SQL via SQLAlchemy.
4. A clean, extensible project structure.

---

## Prerequisites

- Python 3.10+
- A Firebase project (Console → Build → Authentication)
- Enable **Email/Password** sign-in provider.
- Download a **Service Account** key (Project settings → Service accounts → Generate new private key).
- Get your **Web API key** (Project settings → General tab).

---

## Quick start

```bash
# 1) Clone or unzip the project
cd fastapi-firebase-sql-tasks

# 2) Create and activate a virtualenv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv .venv
source .venv/bin/activate

# 3) Install deps
pip install -r requirements.txt

# 4) Configure environment
cp .env.example .env
# Edit .env:
# - Set FIREBASE_API_KEY
# - Put your serviceAccountKey.json at project root and ensure GOOGLE_APPLICATION_CREDENTIALS points to it
# - Optionally change DATABASE_URL (defaults to SQLite dev.db)

# 5) Run the server
uvicorn app.main:app --reload

# Visit docs
# http://127.0.0.1:8000/docs
```

> **Important:** Never commit `.env` or `serviceAccountKey.json` to source control.

---

## How authentication works (human-friendly)

- Clients call our `/auth/signup` or `/auth/login` endpoints.
- We proxy to **Firebase Identity Toolkit REST API** using your `FIREBASE_API_KEY`.
- Firebase returns an **ID token** (JWT). We give it back to the client.
- For protected routes, clients send `Authorization: Bearer <ID_TOKEN>`.
- The backend **verifies the token** using the Firebase Admin SDK. If valid, we extract the user's Firebase `uid` and email.
- We **upsert** a row in our local `users` table keyed by `firebase_uid` to tie tasks to users.

---



---

## Useful test flow (from Swagger UI)

1. `POST /auth/signup` → create a user (email + password). Copy `id_token` from the response.
2. Click the **Authorize** button (top-right in docs) and paste `Bearer <id_token>`
3. Now use the `/tasks` endpoints to create/read/update/delete your own tasks.

---

## Folder layout

```
app/
  core/
    config.py
  db/
    base.py
    session.py
  dependencies/
    auth.py
  models/
    task.py
    user.py
  routers/
    auth.py
    tasks.py
  schemas/
    task.py
    user.py
  main.py
.env.example
README.md
requirements.txt
```

---

## Learning checkpoints (what to study in this repo)

1. `app/routers/auth.py` → How sign-up/login proxy Firebase.
2. `app/dependencies/auth.py` → How we verify tokens + auto-create the SQL user.
3. `app/models/*` & `app/schemas/*` → Clear separation between DB models and API schemas.
4. `app/routers/tasks.py` → CRUD patterns with ownership checks and filters.
