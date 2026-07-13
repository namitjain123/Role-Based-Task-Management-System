import { Link, useNavigate, useLocation } from "react-router-dom";
import { getToken, clearToken, getUserRole } from "../api";

function Navbar() {
  const navigate = useNavigate();

  // Why call useLocation() even though we never use its return value?
  //
  // getToken() reads localStorage directly - it's not React state, so
  // changing it (in Login.jsx via setToken, or below via clearToken) does
  // NOT by itself make Navbar re-render. React only re-renders a component
  // when ITS OWN state changes, or a parent re-renders it.
  //
  // useLocation() subscribes this component to React Router's current URL.
  // Every time you navigate (login redirects to /todos, logout redirects to
  // /login), the location changes, which forces Navbar to re-render - and
  // on that re-render, getToken() below reads the fresh, current value.
  // It's a small trick, but a common and legitimate one.
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
            {/* Only admins ever see this link. Same RBAC idea as your old
                navbar.html: {% if user and user.role == 'admin' %} */}
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
