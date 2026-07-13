

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";


export function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}


export function getUserRole() {
  const token = getToken();
  if (!token) return null;
  try {
    // 1. grab the middle (payload) part
    let payload = token.split(".")[1];

    payload = payload.replace(/-/g, "+").replace(/_/g, "/");
    while (payload.length % 4) payload += "=";
    // 3. atob() decodes base64 to a string; JSON.parse turns it into an object
    const claims = JSON.parse(atob(payload));
    return claims.role ?? null;
  } catch {
    return null; // malformed token -> treat as "no known role"
  }
}

async function readBody(response) {
  const raw = await response.text();
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}



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
