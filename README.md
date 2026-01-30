
# Movies & Characters Backend

A FastAPI backend providing movies and characters management with JWT authentication, WebSocket notifications, and SQLite via SQLAlchemy. Designed for local development and automated tests.

## Features

- REST API for Movies and Characters
- JWT based authentication (login / register)
- WebSocket notifications broadcasting operations and data
- Background tasks for generation operations
- Simple SQLAlchemy-based persistence (`SessionLocalMovies`)
- Unit tests included (`tests.py`)

## Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn
- SQLAlchemy
- jose (JWT)
- pytest / unittest (tests)

## Requirements

Install dependencies (example):

```bash
python -m venv .venv
source .venv/Scripts/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If no `requirements.txt` present, install the main packages:

```bash
pip install fastapi uvicorn sqlalchemy python-jose passlib
```

## Configuration / Environment

Set these environment variables for production-like behavior:

- `SECRET_KEY` — JWT secret
- `ALGORITHM` — JWT algorithm (e.g. `HS256`)
- `DATABASE_URL` — optional DB URL; default uses the local DB configured in the project

The project file `main.py` will create the DB schema on start if using the local engine.

## Run (development)

Start with automatic reload so code changes take effect:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Or within `main.py` (for quick debug) ensure `uvicorn.run(..., reload=True)` is used.

API docs:
- OpenAPI UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Running tests

Run unit tests included in `tests.py`:

```bash
python tests.py
```

Or with pytest (if tests converted):

```bash
pytest
```

## Authentication

- Register: `POST /auth/register/` (body: `username`, `hashedPassword`)
- Login: `POST /auth/login/` (body: `username`, `hashedPassword`) — returns a JWT token

Include JWT in requests:

Header:
```
Authorization: Bearer <token>
```

Endpoints that require auth use `Depends(oauth2_scheme)` and `EntitiesRepo().verify_token(...)` or `verify_admin_token(...)`.

## WebSocket Notifications

WebSocket endpoint: `ws://127.0.0.1:8000/ws`

Server sends JSON messages with this shape:

```json
{
  "operation": "add" | "update" | "delete" | "delete_bulk" | ...,
  "data": { /* operation-specific payload */ }
}
```

Example: after deleting a movie the server may send:
```json
{ "operation": "delete", "data": { "id": 123 } }
```

## Common Endpoints (quick reference)

- Movies
  - `GET /movies` — list (pagination)
  - `GET /movies/{id}` — get by id
  - `POST /movies` — create
  - `PUT /movies/{id}` — update
  - `DELETE /movies/{id}` — delete
  - `POST /movies/bulk/` — add many
  - `POST /movies/generate/{number}` — generate in background

- Characters
  - `GET /characters` — list
  - `GET /characters/{id}` — get
  - `POST /characters` — create
  - `PUT /characters/{id}` — update
  - `DELETE /characters/{id}` — delete
  - `POST /characters/bulk/` — add many

- Users / Admin
  - `POST /auth/login/`
  - `POST /auth/register/`
  - `GET /users/nonAdmin/` — admin-only

All endpoint paths above are implemented in `main.py`.

## Notes & Tips

- To see code changes reflected, run with `--reload` or enable reload in debug configuration inside `PyCharm`.
- To remove authentication from specific endpoints, remove the `Depends(oauth2_scheme)` parameter and any explicit token verification call (`verify_token` / `verify_admin_token`) for those handlers.
- Use WebSocket clients (browser dev tools, `wscat`, or a small JS client) to observe broadcast messages.

## Project Files

- `main.py` — FastAPI application and routes
- `EntitiesRepository.py` — data access and business logic
- `models.py` — SQLAlchemy models
- `schemas.py` — Pydantic models
- `auth_token.py` — JWT utilities
- `tests.py` — unit tests

