import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api";

function Login() {
  // useState gives us a piece of memory that React "watches". When we call
  // setUsername(...), React automatically re-renders this component with the
  // new value. This replaces what Jinja did with <input value="{{...}}"> -
  // except here WE own the value, not the server.
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // useNavigate is react-router's way of changing pages from JS code -
  // the equivalent of your old base.js doing window.location.href = "...".
  const navigate = useNavigate();

  async function handleSubmit(event) {
    // Forms reload the whole page by default when submitted. preventDefault()
    // stops that, same reason your old base.js called event.preventDefault().
    event.preventDefault();

    setError(null);
    setLoading(true);

    try {
      await login(username, password); // this saves the token internally (api.js)
      navigate("/todos"); // success -> go to the todos page
    } catch (err) {
      setError(err.message); // show whatever FastAPI's "detail" message was
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mt-5">
      <div className="card mx-auto" style={{ maxWidth: "420px" }}>
        <div className="card-header">
          <h1>Login</h1>
        </div>
        <div className="card-body">
          {error && <div className="alert alert-danger">{error}</div>}

          {/* React forms: instead of the browser collecting field values on
              submit, each input is "controlled" - its value comes FROM
              username/password state, and typing calls setUsername/setPassword
              to update that state. This two-way wiring is the biggest mental
              shift from plain HTML forms. */}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                className="form-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group mt-2">
              <label>Password</label>
              <input
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary mt-3" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>
        </div>
        <div className="card-footer">
          <p className="mb-0">
            Don't have an account? <Link to="/register">Register</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
