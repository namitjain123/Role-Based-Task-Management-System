import { useState, useEffect } from "react";
import { apiFetch } from "../api";

function Todos() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // useEffect runs code AFTER the component renders, as a "side effect"
  // (something outside of just returning JSX - here, a network call).
  //
  // Why do we need this at all? Your old Jinja route queried the DB and
  // handed the template fully-formed data before anything was sent to the
  // browser - the page arrived already populated. React works the opposite
  // way: the component renders first (with todos = [], the initial state),
  // THEN useEffect fires and fetches the real data, and calling setTodos(...)
  // triggers a second render with the real list. That's why we need a
  // loading state - there's a brief moment where we have no data yet.
  //
  // The [] second argument is the "dependency array" - it tells React "only
  // run this effect once, right after the first render" (an empty array
  // means "nothing this effect depends on ever changes, so never re-run it").
  useEffect(() => {
    async function loadTodos() {
      try {
        const data = await apiFetch("/todos/"); // same endpoint your old todos.py read_all used
        setTodos(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadTodos();
  }, []);

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <p>Loading your todos...</p>
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

  const incomplete = todos.filter((t) => !t.complete);
  const complete = todos.filter((t) => t.complete);

  return (
    <div className="container mt-4">
      <div className="card text-center">
        <div className="card-header">
          <h1>Todo List</h1>
        </div>
        <div className="card-body">
          <h5 className="card-title">Your Todos</h5>
          <p className="card-text">Here are your current todos:</p>

          {todos.length === 0 ? (
            <p className="text-muted">You have no todos yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Info</th>
                </tr>
              </thead>
              <tbody>
                {/* .map() turns each todo into a table row - the React
                    equivalent of Jinja's {% for todo in todos %}. React
                    needs a unique "key" prop on each item in a list so it
                    can track which row is which across re-renders - here
                    todo.id (from the database) is the natural choice. */}
                {incomplete.map((todo, index) => (
                  <tr key={todo.id}>
                    <td style={{ width: "60px" }}>{index + 1}</td>
                    <td>{todo.title}</td>
                  </tr>
                ))}
                {complete.map((todo) => (
                  <tr key={todo.id} className="alert alert-success">
                    <td colSpan="2" style={{ textDecoration: "line-through" }}>
                      {todo.title}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default Todos;
