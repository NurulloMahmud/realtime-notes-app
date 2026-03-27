# Collab Notes

A real-time collaborative notes application. Multiple users can edit the same note simultaneously, see each other's cursors, and track the full version history of every document.

---

## Quick Start (Docker — recommended)

The entire stack (PostgreSQL, FastAPI backend, React frontend) starts with a single command.

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
# Clone / enter the project directory
cd realtime-notes-app

# Start everything
docker compose up --build
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend API | http://localhost:8000     |
| Swagger docs | http://localhost:8000/docs |

To stop everything:

```bash
docker compose down
```

To stop and delete the database volume (full reset):

```bash
docker compose down -v
```

---

## Local Development (without Docker)

Run the backend and frontend in separate terminals. You need Python 3.9+ and Node.js 18+ installed.

### 1. Backend

```bash
cd backend

# Create a virtual environment (first time only)
python3 -m venv ../env

# Activate it
source ../env/bin/activate          # macOS / Linux
# ../env/Scripts/activate           # Windows

# Install dependencies (first time only)
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
```

Edit `backend/.env` and set the values for your local PostgreSQL instance:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notesdb
JWT_SECRET=any-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
VERSION_HISTORY_LIMIT=10
```

Start a local PostgreSQL database, then run the backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend creates all database tables automatically on first startup.

### 2. Frontend

Open a second terminal:

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

The frontend runs on http://localhost:3000 and proxies all `/api/*` and `/ws/*` requests to the backend at port 8000, so no CORS configuration is needed.

---

## Environment Variables

All variables live in `backend/.env` (copy from `backend/.env.example`).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/notesdb` | PostgreSQL connection string. Use `@db:` inside Docker, `@localhost:` for local dev. |
| `JWT_SECRET` | `change-me-in-production` | Secret used to sign JWT tokens. Set a long random string in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | How long an access token is valid. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | How long a refresh token is valid. |
| `VERSION_HISTORY_LIMIT` | `10` | Maximum number of saved versions per note. |

---

## User Manual

### Creating an account

1. Open http://localhost:3000 in your browser.
2. You will be redirected to the **Sign in** page.
3. Click **Register** to go to the registration page.
4. Fill in a username (3–32 characters, letters/digits/underscore), your email address, and a password (minimum 8 characters).
5. Click **Create account**. You are logged in automatically.

### Creating a note

1. On the **My Notes** page, click the **New note** button in the top right.
2. Type a title and press **Create**.
3. You are taken directly into the note editor.

### Editing a note

- Click anywhere in the large text area and start typing.
- Changes are sent to the server automatically after a short pause (800 ms of inactivity). The status indicator in the top bar shows **Saved** or **Saving...**.
- To rename the note, click the title at the top, edit it, then click anywhere else. The title saves on blur.

### Real-time collaboration

Multiple users can edit the same note at the same time.

1. Open the note you want to share.
2. Click **People** in the top bar to open the collaborators panel.
3. Enter the email address of the person you want to invite and click **Add**. They must already have an account.
4. The invited user will now see the note in their **My Notes** list.

When two or more users have the same note open:

- Colored avatar initials appear in the top bar showing who is online.
- Colored pill badges appear above the text area showing each remote user's name and their current line number.
- Any edit a remote user makes appears in your editor within milliseconds.

### Removing a collaborator

1. Open the note and click **People**.
2. Hover over the collaborator you want to remove — a **Remove** button appears.
3. Click **Remove**. That user immediately loses access to the note.

### Version history

Every time the content of a note is saved, a version snapshot is created. Up to 10 versions are kept per note (older ones are pruned automatically).

1. Click **History** in the top bar to open the version history panel.
2. Each entry shows the timestamp, the editor's username, and a preview of the content.
3. The newest version is labeled **Current**.
4. To roll back to an older version, click **Restore** on that entry. The current content is replaced and a new version entry is created.

### Deleting a note

Only the note owner can delete a note.

1. Open the note.
2. Click **Delete** in the top bar.
3. Confirm the prompt. The note and all its version history are permanently deleted.

---

## Running Tests

Tests use SQLite in-memory so no database setup is required.

```bash
cd realtime-app

# Activate the virtual environment
source env/bin/activate

# Run all 117 tests
python -m pytest backend/ -v
```

---

## Project Structure

```
realtime-app/
├── backend/                  Python / FastAPI
│   ├── app/
│   │   ├── main.py           Application entry point
│   │   ├── config.py         Settings loaded from environment
│   │   ├── database.py       Async SQLAlchemy engine and session
│   │   ├── dependencies.py   Shared FastAPI dependencies (auth guard)
│   │   ├── models/           SQLAlchemy ORM models
│   │   ├── schemas/          Pydantic request / response schemas
│   │   ├── services/         Business logic and WebSocket manager
│   │   └── routers/          Route handlers
│   ├── tests/                pytest test suite (117 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 React / Vite
│   ├── src/
│   │   ├── api/              Axios wrappers for every endpoint
│   │   ├── context/          AuthContext — JWT storage and refresh
│   │   ├── hooks/            useWebSocket — connection lifecycle
│   │   ├── components/       ProtectedRoute
│   │   └── pages/            Login, Register, NotesList, NoteEditor
│   ├── nginx.conf            Proxies /api/* and /ws/* to backend
│   └── Dockerfile
└── docker-compose.yml        Runs db + app + frontend together
```

---

## API Reference

Interactive documentation with a built-in request tester is available at http://localhost:8000/docs once the backend is running.

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Log in and receive access + refresh tokens |
| POST | `/auth/refresh` | Exchange a refresh token for a new access token |
| GET | `/auth/me` | Get the currently authenticated user |

### Notes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/notes` | Create a note |
| GET | `/notes` | List all notes you own or collaborate on |
| GET | `/notes/{id}` | Get a note with its collaborator list |
| PATCH | `/notes/{id}` | Update title and/or content |
| DELETE | `/notes/{id}` | Delete a note (owner only) |

### Collaborators

| Method | Path | Description |
|--------|------|-------------|
| POST | `/notes/{id}/collaborators` | Add a collaborator by email or user ID (owner only) |
| GET | `/notes/{id}/collaborators` | List all collaborators |
| DELETE | `/notes/{id}/collaborators/{user_id}` | Remove a collaborator (owner only) |

### Version History

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notes/{id}/versions` | Get the last N versions (newest first) |
| POST | `/notes/{id}/versions/{version_id}/restore` | Restore a version |

### WebSocket

```
ws://localhost:8000/ws/notes/{note_id}?token=<access_token>
```

**Client → Server**

```json
{ "type": "edit",   "content": "updated text", "cursor_position": 42 }
{ "type": "cursor", "cursor_position": 42 }
```

**Server → Clients**

```json
{ "type": "update",   "user_id": "...", "username": "alice", "content": "...", "cursor_position": 42, "timestamp": "..." }
{ "type": "cursor",   "user_id": "...", "username": "alice", "cursor_position": 42 }
{ "type": "presence", "user_id": "...", "username": "alice", "status": "joined" }
{ "type": "presence", "user_id": "...", "username": "alice", "status": "left" }
```
