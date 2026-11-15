"""
End-to-end (browser) test setup.

Unlike Todoapp/test (which fakes the logged-in user with dependency overrides),
these tests run the REAL app: a uvicorn server is started in a subprocess with
its own throwaway SQLite database, it serves the built React app from
frontend/dist, and Playwright drives a real browser against it.

Prerequisite: build the frontend first ->  cd frontend && npm run build
"""
import os
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
E2E_DB = PROJECT_ROOT / "e2e_test.db"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_healthy(url: str, proc: subprocess.Popen, timeout: float = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("uvicorn exited early - check the server output above")
        try:
            with urllib.request.urlopen(f"{url}/healthy", timeout=1) as r:
                if r.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError(f"Server at {url} did not become healthy in {timeout}s")


@pytest.fixture(scope="session")
def live_server():
    """Starts the real FastAPI app on a free port for the whole test session."""
    if not (FRONTEND_DIST / "index.html").exists():
        pytest.exit(
            "frontend/dist not found. Build the React app first:\n"
            "    cd frontend && npm ci && npm run build",
            returncode=1,
        )

    E2E_DB.unlink(missing_ok=True)  # start from an empty database every run

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{E2E_DB}",
        "SECRET_KEY": "e2e-only-secret-key",
        "ALGORITHM": "HS256",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "Todoapp.main:app",
         "--host", "127.0.0.1", "--port", str(port)],
        cwd=PROJECT_ROOT,
        env=env,
    )
    try:
        _wait_until_healthy(url, proc)
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        E2E_DB.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def base_url(live_server):
    """
    pytest-playwright reads this fixture, so page.goto("/login") resolves
    against the live server automatically.
    """
    return live_server


@pytest.fixture
def new_user():
    """Unique credentials per test so tests never collide on username/email."""
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@example.com",
        "password": "Passw0rd!",
    }


@pytest.fixture
def register(page):
    """Registers a user through the UI. Usage: register(new_user, role="user")."""
    def _register(user: dict, role: str = "user"):
        page.goto("/register")
        page.get_by_placeholder("Enter email").fill(user["email"])
        page.get_by_placeholder("Enter username").fill(user["username"])
        page.get_by_placeholder("Enter first name").fill("Test")
        page.get_by_placeholder("Enter last name").fill("User")
        page.locator("select").select_option(role)
        page.get_by_placeholder("Enter password").fill(user["password"])
        page.get_by_placeholder("Confirm password").fill(user["password"])
        page.get_by_role("button", name="Register").click()
        page.wait_for_url("**/login")
        # The URL changes slightly before React swaps the form, so wait for the
        # Login page to actually render - otherwise a test that types right
        # after this can land its input in the disappearing Register form.
        page.get_by_role("heading", name="Login").wait_for()
    return _register


@pytest.fixture
def login(page):
    """Logs in through the UI and waits for the todos page."""
    def _login(user: dict):
        page.goto("/login")
        page.locator("input[type=text]").fill(user["username"])
        page.locator("input[type=password]").fill(user["password"])
        page.get_by_role("button", name="Login").click()
        page.wait_for_url("**/todos")
    return _login
