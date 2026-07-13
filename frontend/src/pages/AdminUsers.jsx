import { useState, useEffect } from "react";
import { apiFetch } from "../api";

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Same fetch-on-mount pattern as Todos.jsx. Hits GET /admin/users, which
  // your backend returns via the UserResponse model - so no hashed_password
  // is ever sent to the browser (the backend strips it).
  useEffect(() => {
    async function loadUsers() {
      try {
        const data = await apiFetch("/admin/users");
        setUsers(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadUsers();
  }, []);

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <p>Loading users...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <div className="card">
        <div className="card-header text-center">
          <h1>All Users</h1>
        </div>
        <div className="card-body">
          <h5 className="card-title">Registered users ({users.length})</h5>
          <p className="card-text">Admin view - everyone who has an account.</p>
          <div className="table-responsive">
            <table className="table table-striped">
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Username</th>
                  <th scope="col">Name</th>
                  <th scope="col">Email</th>
                  <th scope="col">Role</th>
                  <th scope="col">Active</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.username}</td>
                    <td>
                      {u.first_name} {u.last_name}
                    </td>
                    <td>{u.email}</td>
                    <td>
                      {/* A "badge" is just a small colored label from Bootstrap.
                          We pick the color based on the role value - this is
                          the JSX way of doing an if/else inside markup. */}
                      <span
                        className={
                          u.role === "admin"
                            ? "badge bg-primary"
                            : "badge bg-secondary"
                        }
                      >
                        {u.role}
                      </span>
                    </td>
                    <td>
                      <span
                        className={u.is_active ? "badge bg-success" : "badge bg-danger"}
                      >
                        {u.is_active ? "yes" : "no"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminUsers;
