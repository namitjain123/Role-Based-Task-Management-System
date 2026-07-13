import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { apiFetch } from "../api";

function EditTodo() {

  const { todoId } = useParams();
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("1");
  const [complete, setComplete] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);


  useEffect(() => {
    async function loadTodo() {
      try {
        const todo = await apiFetch(`/todos/todo/${todoId}`);
        setTitle(todo.title);
        setDescription(todo.description);
        setPriority(String(todo.priority));
        setComplete(todo.complete);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadTodo();
  }, [todoId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSaving(true);

    try {
      await apiFetch(`/todos/todo/${todoId}`, {
        method: "PUT",
        body: JSON.stringify({
          title,
          description,
          priority: Number(priority),
          complete,
        }),
      });
      navigate("/todos");
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  async function handleDelete() {
    setError(null);
    try {
      await apiFetch(`/todos/todo/${todoId}`, { method: "DELETE" });
      navigate("/todos");
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <p>Loading todo...</p>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <div className="card text-center">
        <div className="card-header">
          <h1>Edit Todo</h1>
        </div>
        <div className="card-body">
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title</label>
              <input
                type="text"
                className="form-control"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                rows="3"
                className="form-control"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select
                className="form-control"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                required
              >
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
              </select>
            </div>
            <div className="form-group form-check">
              <input
                type="checkbox"
                className="form-check-input"
                id="completeCheck"
                checked={complete}
                onChange={(e) => setComplete(e.target.checked)}
              />
              <label className="form-check-label" htmlFor="completeCheck">
                Complete
              </label>
            </div>
            <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
              {saving ? "Saving..." : "Edit your todo"}
            </button>{" "}
            <button
              type="button"
              className="btn btn-danger mt-3"
              onClick={handleDelete}
            >
              Delete
            </button>{" "}
            <Link to="/todos" className="btn btn-success mt-3">
              Cancel
            </Link>
          </form>
        </div>
      </div>
    </div>
  );
}

export default EditTodo;
