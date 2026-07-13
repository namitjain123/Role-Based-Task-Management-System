import { Navigate } from "react-router-dom";
import { getToken } from "../api";

function ProtectedRoute({ children }) {
  const token = getToken();

  if (!token) {
    // No token in localStorage -> definitely not logged in -> bounce to login.
    return <Navigate to="/login" replace />;
  }


  return children;
}

export default ProtectedRoute;
