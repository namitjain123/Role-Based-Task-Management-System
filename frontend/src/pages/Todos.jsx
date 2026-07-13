import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api";

function Todos() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
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
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {incomplete.map((todo, index) => (
                  <tr key={todo.id}>
                    <td style={{ width: "60px" }}>{index + 1}</td>
                    <td>{todo.title}</td>
                    <td>
                      <Link to={`/todos/edit/${todo.id}`} className="btn btn-info">
                        Edit
                      </Link>
                    </td>
                  </tr>
                ))}
                {complete.map((todo) => (
                  <tr key={todo.id} className="alert alert-success">
                    <td style={{ textDecoration: "line-through" }}>{todo.title}</td>
                    <td style={{ textDecoration: "line-through" }}>done</td>
                    <td>
                      <Link to={`/todos/edit/${todo.id}`} className="btn btn-info">
                        Edit
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <Link to="/todos/add" className="btn btn-primary">
            Add New Todo
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Todos;
