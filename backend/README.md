# Collaborative Notes API

Real-time collaborative notes application backend built with FastAPI, WebSockets, and PostgreSQL.

## Running the Project

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.
Swagger docs: `http://localhost:8000/docs`

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/notesdb` | PostgreSQL connection string |
| `JWT_SECRET` | `change-me-in-production` | Secret key for JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime in days |
| `VERSION_HISTORY_LIMIT` | `10` | Max versions stored per note |

## API Overview

Full interactive documentation available at `/docs` after starting the server.

| Method | Path | Description |
|---|---|---|
| POST | /auth/register | Register a new user |
| POST | /auth/login | Login and receive tokens |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Get current user |
| POST | /notes | Create a note |
| GET | /notes | List accessible notes |
| GET | /notes/{id} | Get note with collaborators |
| PATCH | /notes/{id} | Update note |
| DELETE | /notes/{id} | Delete note (owner only) |
| POST | /notes/{id}/collaborators | Add collaborator (owner only) |
| GET | /notes/{id}/collaborators | List collaborators |
| DELETE | /notes/{id}/collaborators/{user_id} | Remove collaborator (owner only) |
| GET | /notes/{id}/versions | Get version history |
| POST | /notes/{id}/versions/{version_id}/restore | Restore a version |
| WS | /ws/notes/{id}?token=... | Real-time editing WebSocket |

## WebSocket Protocol

Connect with a valid JWT access token as a query parameter:

```
ws://localhost:8000/ws/notes/{note_id}?token=<access_token>
```

Send edits:

```json
{"type": "edit", "content": "updated text", "cursor_position": 42}
```

Receive broadcasts:

```json
{"type": "update", "user_id": "...", "username": "john", "content": "...", "timestamp": "..."}
{"type": "presence", "user_id": "...", "username": "john", "status": "joined"}
```

## Project Structure

```
app/
├── main.py          - FastAPI app and startup
├── config.py        - Settings from environment variables
├── database.py      - SQLAlchemy async engine and session
├── dependencies.py  - Shared FastAPI dependencies
├── models/          - SQLAlchemy ORM models
├── schemas/         - Pydantic request/response schemas
├── services/        - Business logic
└── routers/         - Route handlers
tests/               - pytest test suite
```

## Running Tests

```bash
pip install -r requirements.txt
pytest
```
