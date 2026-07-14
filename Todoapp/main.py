import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .database import SessionLocal, engine
from .models import Base

from .routers import auth, todos, admin, users

from fastapi.responses import FileResponse

app = FastAPI()

# CORS is still needed for LOCAL DEV, where the Vite dev server (:5173) and the
# API (:8000) are different origins. In production the React app is served from
# THIS same app (same origin), so CORS isn't required there - but keeping it is
# harmless. Override FRONTEND_ORIGINS via env var if you ever host separately.
frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## create the database
Base.metadata.create_all(bind=engine)


@app.get("/healthy")
def healthy():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# API routes live under /api/*
#
# The React app owns the plain browser paths (/login, /todos, /admin/users...),
# so the whole JSON API is namespaced under /api to avoid name collisions.
# e.g. GET /api/todos/  -> JSON, while the browser path /todos -> the React page.
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api")
app.include_router(todos.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(users.router, prefix="/api")


# ---------------------------------------------------------------------------
# Serve the built React app (production only)
#
# `npm run build` produces frontend/dist. When that folder exists (inside the
# Docker image, or after you build locally), FastAPI serves it:
#   - a request that maps to a real built file (JS/CSS/favicon) returns that file
#   - anything else returns index.html, so React Router can take over on the
#     client. Without this "SPA fallback", refreshing the browser on /todos
#     would 404, because the server has no /todos route.
#
# In local dev you DON'T build - the Vite dev server serves React on :5173, and
# this block simply does nothing because frontend/dist doesn't exist yet.
# ---------------------------------------------------------------------------
FRONTEND_DIST = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
)

if os.path.isdir(FRONTEND_DIST):

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Never let the SPA fallback swallow API or health-check requests.
        if full_path.startswith("api") or full_path == "healthy":
            raise HTTPException(status_code=404, detail="Not found")

        # If the path maps to a real built file, serve it (assets, favicon...).
        candidate = os.path.normpath(os.path.join(FRONTEND_DIST, full_path))
        # Guard against path traversal: candidate must stay inside FRONTEND_DIST.
        if candidate.startswith(FRONTEND_DIST) and os.path.isfile(candidate):
            return FileResponse(candidate)

        # Otherwise it's a client-side route -> hand back the app shell.
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
