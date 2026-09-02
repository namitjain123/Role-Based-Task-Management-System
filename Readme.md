# Full-Stack Todo Application — React + FastAPI + Azure

A production-deployed full-stack Todo app: a **React single-page app** served by a **FastAPI** backend, backed by **Supabase PostgreSQL**, with JWT auth, role-based access control, AI-assisted task entry, and a full **CI/CD pipeline to Azure Container Apps**.

**Live:** https://todoapp.delightfulwater-01722cef.australiaeast.azurecontainerapps.io/

---

## Features

- **JWT Authentication** — register, login, protected routes
- **Role-Based Access Control (RBAC)** — `user` and `admin` roles, enforced on the server
- **Admin panel** — admins can view all registered users and manage any todo
- **Full CRUD** on todos (create, read, update, delete), scoped to the owning user
- **AI Quick-Add** — type a sentence in plain English and an LLM fills in the todo fields
- **Single-page React frontend** — client-side routing, no full page reloads
- **Automated CI/CD** — every push to `main` runs tests, builds, and deploys
- **24 automated tests** — including RBAC enforcement and side-effect checks

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, React Router 7, Vite, Bootstrap 5 |
| **Backend** | FastAPI, Uvicorn |
| **Database** | PostgreSQL (Supabase), SQLAlchemy ORM |
| **Auth** | JWT (`python-jose`), bcrypt password hashing |
| **AI** | Groq API (LLM natural-language task parsing) |
| **Testing** | Pytest (24 tests) |
| **Container** | Docker (multi-stage build) |
| **Cloud** | Azure Container Apps + Azure Container Registry |
| **CI/CD** | GitHub Actions (OIDC — no stored passwords) |

---

## Architecture

The React app and the API are served from **one origin** by a single FastAPI process. React owns the plain browser paths; the entire JSON API is namespaced under `/api/*` so the two never collide.

```text
                        ┌──────────────────────────────┐
   Browser              │   Azure Container App        │
 ┌──────────┐           │  ┌────────────────────────┐  │
 │  React   │  GET /    │  │      FastAPI           │  │
 │   SPA    │──────────►│  │                        │  │
 │          │           │  │  • serves React dist   │  │
 │ (Vite    │  /api/*   │  │    (SPA fallback)      │  │
 │  build)  │◄─────────►│  │  • JSON API @ /api/*   │  │
 └──────────┘   JSON    │  └───────┬────────┬───────┘  │
      │                 └──────────┼────────┼──────────┘
      │ JWT in                     │        │
      │ localStorage               ▼        ▼
      │ (Bearer header)      ┌──────────┐  ┌──────────┐
      └──────────────────────│ Supabase │  │   Groq   │
                             │ Postgres │  │   LLM    │
                             └──────────┘  └──────────┘
```

**Why `/api/*`?** Some paths exist in both worlds — `/admin/users` is both a React *page* and an API *endpoint*. Namespacing the API removes the ambiguity:

| Request | Served by | Returns |
|---|---|---|
| `GET /admin/users` | React (SPA fallback) | The HTML app shell |
| `GET /api/admin/users` | FastAPI | JSON list of users |

Any path that isn't `/api/*`, `/healthy`, or a real static file falls back to `index.html`, letting React Router handle it client-side (so refreshing on `/todos` works instead of 404ing).

---

## Authentication Flow

The React SPA stores the JWT in `localStorage` and sends it as an `Authorization: Bearer` header. (The backend also still accepts a cookie — `get_token_from_request` checks the header first, then falls back to a cookie.)

```text
Login form (React)
   ↓  POST /api/auth/token   (form-urlencoded)
authenticate_user()  →  bcrypt verifies password against stored hash
   ↓
create_access_token()  →  signs a JWT with SECRET_KEY
   ↓  { "sub": username, "user_id": 1, "role": "admin", "exp": ... }
Returned as JSON  →  React saves it to localStorage
   ↓
Every later request: apiFetch() attaches  Authorization: Bearer <token>
   ↓
get_token_from_request()  →  finds the token (header, else cookie)
   ↓
get_current_user()  →  jwt.decode() verifies the signature & expiry
   ↓
Route receives the authenticated user  ✅
```

**A JWT is signed, not encrypted** — anyone can read its payload, but nobody can forge one without `SECRET_KEY`. That's what makes the `role` claim trustworthy.

### RBAC — two layers, one real lock

- **Frontend** (`AdminRoute`, the admin-only navbar link) decides *what to show*. It reads the `role` claim by decoding the JWT client-side. This is **UX only** — it can be bypassed.
- **Backend** (`require_admin()`) decides *what's allowed*. This is the actual security boundary: a non-admin token gets a `403` regardless of what the frontend does.

---

## API Reference

All endpoints are prefixed with `/api`. Access: **public** = no auth, **auth** = any logged-in user, **admin** = admin role only.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/auth/` | public | Register a new user |
| `POST` | `/api/auth/token` | public | Log in, returns a JWT |
| `GET` | `/api/todos/` | auth | List your todos |
| `GET` | `/api/todos/todo/{id}` | auth | Get one todo |
| `POST` | `/api/todos/todo/` | auth | Create a todo |
| `PUT` | `/api/todos/todo/{id}` | auth | Update a todo |
| `DELETE` | `/api/todos/todo/{id}` | auth | Delete a todo |
| `POST` | `/api/todos/parse` | auth | **AI:** natural language → structured todo fields |
| `GET` | `/api/admin/users` | admin | List all users (no password hashes) |
| `GET` | `/api/admin/users/{id}` | admin | Get one user |
| `GET` | `/api/admin/todo/` | admin | List every user's todos |
| `DELETE` | `/api/admin/todo/{id}` | admin | Delete any todo |

| `PUT` | `/api/user/user/password` | auth | Change password |
| `GET` | `/healthy` | public | Health check (used by Azure) |



Interactive API docs (Swagger): **`/docs`**

---

## AI Quick-Add

On the **Add Todo** page, type a sentence like:

> *"email the design team about the Q3 report by friday, high priority"*

`POST /api/todos/parse` sends it to a Groq-hosted LLM with a JSON-mode prompt, which returns structured fields that pre-fill the form for review:

```json
{ "title": "Email design team re: Q3 report", "description": "...", "priority": 5 }
```

It **suggests only** — nothing is saved until you submit the normal form. The backend clamps `priority` to 1–5 and falls back to your raw text if the model returns something unusable, so a bad LLM response can never produce an invalid todo.

---

## Project Structure

```text
todoapp/
├── Todoapp/                     # FastAPI backend
│   ├── routers/
│   │   ├── auth.py              # register, login, JWT creation & verification
│   │   ├── todos.py             # todo CRUD + AI /parse endpoint
│   │   ├── admin.py             # admin-only routes + require_admin()
│   │   └── users.py             # profile, change password
│   ├── test/                    # 24 pytest tests
│   │   ├── conftest.py          # fixtures: test DB, fake auth, RBAC role-switching
│   │   ├── test_todos.py
│   │   ├── test_admin.py
│   │   └── test_main.py
│   ├── database.py              # SQLAlchemy engine/session (Supabase)
│   ├── models.py                # Users, Todos tables
│   ├── main.py                  # app setup, /api routers, React SPA serving
│   └── requirements.txt
│
├── frontend/                    # React SPA (Vite)
│   ├── src/
│   │   ├── api.js               # apiFetch(), login(), token storage, getUserRole()
│   │   ├── App.jsx              # routes
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx  # requires a token
│   │   │   ├── AdminRoute.jsx      # requires the admin role
│   │   │   └── Navbar.jsx
│   │   └── pages/
│   │       ├── Login.jsx  Register.jsx
│   │       ├── Todos.jsx  AddTodo.jsx  EditTodo.jsx
│   │       └── AdminUsers.jsx
│   └── .env.production          # VITE_API_URL=/api  (same-origin in prod)
│
├── .github/workflows/deploy.yml # CI/CD: test → build → push → deploy
├── Dockerfile                   # multi-stage: Node builds React, Python serves it
└── .dockerignore
```

---

## Local Development

Requires **Python 3.11+** and **Node 20.19+/22.12+**.

**1. Backend**
```bash
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r Todoapp/requirements.txt
```

Create a `.env` in the project root:
```env
DATABASE_URL=postgresql://user:password@host:5432/postgres
SECRET_KEY=<generate: openssl rand -hex 32>
ALGORITHM=HS256
GROQ_API_KEY=<your groq api key>
```

Run it:
```bash
uvicorn Todoapp.main:app --reload      # → http://localhost:8000  (API at /api/*)
```

**2. Frontend** (in a second terminal)
```bash
cd frontend
npm install
npm run dev                            # → http://localhost:5173
```

Open **http://localhost:5173**. In dev the two run as separate servers (Vite proxies nothing — the frontend calls `http://localhost:8000/api` directly, which CORS allows). In production they're the same origin.

---

## Testing

```bash
python -m pytest Todoapp/test -v          # all 24 tests
python -m pytest Todoapp/test/test_admin.py -v
python -m pytest Todoapp/test -k delete   # only tests matching "delete"
```

Tests run against a throwaway SQLite database — never your real data. `conftest.py` provides fixtures that fake authentication, and the `as_non_admin` / `as_logged_out` fixtures let tests **prove** RBAC actually rejects unauthorized users (rather than assuming it).

---

## Deployment

Every push to `main` triggers `.github/workflows/deploy.yml`:

```text
push to main
   │
   ├─► test job ─────────────► pytest (24 tests)
   │                              │ fails → pipeline stops, nothing deploys
   │                              ▼ passes
   └─► build-and-deploy job
          ├─ azure/login          (OIDC — no stored password)
          ├─ az acr login
          ├─ docker build         ┌ stage 1: Node  → npm ci && npm run build (React)
          │                       └ stage 2: Python → serves the built dist + API
          ├─ docker push          → Azure Container Registry (tagged with the commit SHA)
          └─ az containerapp update → new revision goes live
```

**Security notes**
- **OIDC federated credentials** — GitHub proves its identity to Azure with a short-lived signed token. No Azure password is ever stored in GitHub.
- **Managed identity** — the Container App pulls images from ACR using its own identity (`AcrPull` role), not a registry password.
- **Secrets** (`DATABASE_URL`, `SECRET_KEY`, `GROQ_API_KEY`) live as **Azure Container App secrets**, injected as env vars at runtime. They're never in the repo, the Docker image, or the workflow file.

---

## Key Concepts Demonstrated

- FastAPI dependency injection (`Depends`, `Annotated`)
- JWT auth: signing, verification, expiry, and the signed-not-encrypted distinction
- RBAC with a real server-side enforcement boundary
- SPA architecture: client-side routing, SPA fallback, same-origin API namespacing
- React fundamentals: `useState`, `useEffect`, controlled inputs, route guards
- Multi-stage Docker builds
- CI/CD with passwordless (OIDC) cloud authentication
- LLM integration with defensive output validation

---

## Screenshots



| | |
|---|---|
| ![Login](./assets/login.png) | ![Register](./assets/register.png) |
| ![Todos](./assets/home.png) | ![Edit](./assets/addtodo.png) |
| ![Admin](./assets/allusers.png) |

**Database schema**

![Schema](./assets/schema.png)

---

## Possible Next Steps

- Admin activity log (audit trail of who changed what)
- Personal analytics dashboard (completion rate, priority breakdown)
- Refresh tokens (currently a 30-minute expiry requires re-login)

---

## Author

**Namit Jain** — AI Engineer
