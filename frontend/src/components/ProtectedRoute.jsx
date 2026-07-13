import { Navigate } from "react-router-dom";
import { getToken } from "../api";

// A "wrapper" component: it doesn't render its own UI, it decides whether to
// render whatever was passed inside it (its "children"), or redirect instead.
//
// Usage in App.jsx:
//   <Route path="/todos" element={
//     <ProtectedRoute><TodosPage /></ProtectedRoute>
//   } />
//
// This is the client-side version of what your old todos.py route did:
//   if user is None:
//       return RedirectResponse("/auth/login-page")
// Same idea, just running in the browser instead of on the server.
function ProtectedRoute({ children }) {
  const token = getToken();

  if (!token) {
    // No token in localStorage -> definitely not logged in -> bounce to login.
    return <Navigate to="/login" replace />;
  }

  // We only check "does a token exist" here, not "is it still valid".
  // That's intentional: checking validity requires asking the backend, and
  // it's not worth doing on every single navigation. The real security
  // boundary is still the backend - if this token is expired or fake, the
  // very first API call the page makes will get a 401 from FastAPI. In
  // Step 6 we'll teach apiFetch to catch that 401 and redirect too, so an
  // expired token still gets you bounced, just one request later.
  return children;
}

export default ProtectedRoute;
