// Every request to our FastAPI backend goes through this file.
// Why centralize it? So we write the "attach the token" and "handle errors"
// logic ONCE, instead of repeating it in every component.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Token storage
//
// Your old Jinja app's JavaScript stored the token in a cookie. Here we use
// localStorage instead - it's the standard choice for a React app talking to
// a separate API. It persists across page reloads and we control it fully in
// JS (no server needs to set it).
// ---------------------------------------------------------------------------

export function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

// ---------------------------------------------------------------------------
// getUserRole: read the "role" claim out of the JWT, client-side.
//
// Remember from the auth walkthrough: a JWT is three base64 parts joined by
// dots - header.payload.signature - and the middle part is just base64-encoded
// JSON like {"sub":"namit","role":"admin","exp":...}. So we can decode it in
// the browser WITHOUT asking the backend, just to know what to show in the UI.
//
// IMPORTANT - this is for UI convenience only, NOT security. A user could edit
// their localStorage or this code to fake "admin" and reveal the Users link.
// That doesn't matter, because the real lock is on the backend: /admin/users
// still checks the role on the server, and they can't forge a valid admin
// token without your SECRET_KEY. This just decides what's worth *showing*.
// ---------------------------------------------------------------------------

export function getUserRole() {
  const token = getToken();
  if (!token) return null;
  try {
    // 1. grab the middle (payload) part
    let payload = token.split(".")[1];
    // 2. JWT uses "base64url" (- and _ instead of + and /); convert it back,
    //    and pad the length to a multiple of 4 so atob() can decode it.
    payload = payload.replace(/-/g, "+").replace(/_/g, "/");
    while (payload.length % 4) payload += "=";
    // 3. atob() decodes base64 to a string; JSON.parse turns it into an object
    const claims = JSON.parse(atob(payload));
    return claims.role ?? null;
  } catch {
    return null; // malformed token -> treat as "no known role"
  }
}

// ---------------------------------------------------------------------------
// readBody: read a Response body EXACTLY ONCE.
//
// A Response body is a one-time stream. Calling response.json() (or .text())
// a second time throws "body stream already read". So we read it as text a
// single time here, then parse. This makes that whole class of bug impossible.
// Returns: a parsed object for JSON, the raw string if it isn't JSON, or
// null for an empty body (e.g. 204 No Content from delete / password change).
// ---------------------------------------------------------------------------

async function readBody(response) {
  const raw = await response.text();
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

// ---------------------------------------------------------------------------
// apiFetch: the one function nearly every component will call.
//
// It wraps the browser's built-in fetch() and automatically adds:
//   Authorization: Bearer <token>
// This is the EXACT same header your old base.js sent manually, and your
// backend's get_token_from_request() already checks it first - so the
// backend needs zero changes for this to work.
// ---------------------------------------------------------------------------

export async function apiFetch(path, options = {}) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await readBody(response);

  // A 401 means the token is missing, expired, or invalid - get_current_user
  // on the backend already made that call. There's no recovering from this
  // client-side (we're not building refresh tokens), so we handle it in ONE
  // place instead of every page: clear the stale token and send the browser
  // back to login. api.js is a plain module, not a component, so it can't
  // use React Router's useNavigate() - window.location.href is the plain
  // browser way to change page from outside React.
  if (response.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired - please log in again.");
  }

  // FastAPI sends { "detail": "..." } on other errors (403, 404, 422...).
  // Surface that message so components can show something meaningful.
  if (!response.ok) {
    const detail = (data && data.detail) || response.statusText;
    throw new Error(detail);
  }

  return data;
}

// ---------------------------------------------------------------------------
// login: separate from apiFetch because FastAPI's /auth/token endpoint
// expects an OAuth2 form (form-urlencoded), not JSON - same reason your
// old base.js built a URLSearchParams body for login specifically.
// ---------------------------------------------------------------------------

export async function login(username, password) {
  const body = new URLSearchParams();
  body.append("grant_type", "password");
  body.append("username", username);
  body.append("password", password);

  const response = await fetch(`${API_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  const data = await readBody(response);

  if (!response.ok) {
    throw new Error((data && data.detail) || "Login failed");
  }

  setToken(data.access_token); // save it so future apiFetch calls send it
  return data;
}
