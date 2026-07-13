import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiFetch } from "../api";

function AddTodo() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("1");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);


  const [quickText, setQuickText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState(null);

  const navigate = useNavigate();

  async function handleQuickAdd(event) {
    event.preventDefault();
    setParseError(null);
    setParsing(true);
    try {
      const suggestion = await apiFetch("/todos/parse", {
        method: "POST",
        body: JSON.stringify({ text: quickText }),
      });
      setTitle(suggestion.title);
      setDescription(suggestion.description);
      setPriority(String(suggestion.priority)); // number -> string, for the <select>
    } catch (err) {
      setParseError(err.message);
    } finally {
      setParsing(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSaving(true);

    try {

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
          <div className="card bg-light mb-4">
            <div className="card-body">
              <h6 className="card-title">Quick Add with AI</h6>
              {parseError && <div className="alert alert-danger py-2">{parseError}</div>}
              <form onSubmit={handleQuickAdd} className="d-flex gap-2">
                <input
                  type="text"
                  className="form-control"
                  placeholder='Try: "email the design team about Q3 report by friday, high priority"'
                  value={quickText}
                  onChange={(e) => setQuickText(e.target.value)}
                />
                <button
                  type="submit"
                  className="btn btn-outline-primary text-nowrap"
                  disabled={parsing || quickText.trim().length < 3}
                >
                  {parsing ? "Thinking..." : "Fill with AI"}
                </button>
              </form>
            </div>
          </div>

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
