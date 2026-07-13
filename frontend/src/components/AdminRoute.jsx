import { Navigate } from "react-router-dom";
import { getToken, getUserRole } from "../api";


function AdminRoute({ children }) {
  const token = getToken();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (getUserRole() !== "admin") {

    return <Navigate to="/todos" replace />;
  }

  return children;
}

export default AdminRoute;
