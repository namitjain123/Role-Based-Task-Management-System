import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiFetch } from "../api";

function AddTodo() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("1");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSaving(true);

    try {
      // Matches TodoRequest in Todoapp/routers/todos.py exactly - title and
      // description as strings, priority as a NUMBER (the <select> gives us
      // a string "1".."5", so we convert with Number(...) or the backend's
      // Pydantic validation will reject it), complete always false for a
      // brand-new todo.
      await apiFetch("/todos/todo/", {
        method: "POST",
        body: JSON.stringify({
          title,
          description,
          priority: Number(priority),
          complete: false,
        }),
      });
      navigate("/todos");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="container mt-4">
      <div className="card text-center">
        <div className="card-header">
          <h1>Add New Todo</h1>
        </div>
        <div className="card-body">
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title</label>
              <input
                type="text"
                className="form-control"
                placeholder="Enter title"
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
                placeholder="Enter description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Priority</label>
              {/* A <select>'s value in React works the same as text inputs -
                  it's controlled by state (priority) and onChange updates it. */}
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
            <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
              {saving ? "Adding..." : "Add Todo"}
            </button>{" "}
            <Link to="/todos" className="btn btn-secondary mt-3">
              Cancel
            </Link>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AddTodo;
