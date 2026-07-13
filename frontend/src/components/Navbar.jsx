import { Link, useNavigate, useLocation } from "react-router-dom";
import { getToken, clearToken, getUserRole } from "../api";

function Navbar() {
  const navigate = useNavigate();

  useLocation();

  const token = getToken();
  const role = getUserRole();

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">
          TodoApp
        </Link>

        <div className="collapse navbar-collapse d-flex justify-content-between">
          <ul className="navbar-nav me-auto">
            {token && (
              <li className="nav-item">
                <Link className="nav-link" to="/todos">
                  Home
                </Link>
              </li>
            )}

            {token && role === "admin" && (
              <li className="nav-item">
                <Link className="nav-link" to="/admin/users">
                  Users
                </Link>
              </li>
            )}
          </ul>

          <ul className="navbar-nav ms-auto">
            {token ? (
              <li className="nav-item">
                <button className="btn btn-outline-light" onClick={handleLogout}>
                  Logout
                </button>
              </li>
            ) : (
              <>
                <li className="nav-item">
                  <Link className="nav-link" to="/login">
                    Login
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" to="/register">
                    Register
                  </Link>
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
