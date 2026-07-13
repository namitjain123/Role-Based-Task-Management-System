import { Navigate } from "react-router-dom";
import { getToken, getUserRole } from "../api";

// Like ProtectedRoute, but stricter: you must be logged in AND be an admin.
// This mirrors your backend's render_users_page in admin.py:
//   if user is None:            -> redirect to login
//   if user.role != "admin":    -> redirect to /todos
// Same two-step decision, running in the browser.
function AdminRoute({ children }) {
  const token = getToken();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (getUserRole() !== "admin") {
    // Logged in, but not an admin -> send them to their own todos, exactly
    // like the backend bounces non-admins away from the users page.
    return <Navigate to="/todos" replace />;
  }

  return children;
}

export default AdminRoute;
