import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Todos from "./pages/Todos";
import ProtectedRoute from "./components/ProtectedRoute";

// Placeholder pages - we replace these with real components in later steps.
// They exist now just so links/redirects have somewhere valid to land.
function RegisterPlaceholder() {
  return <div className="container mt-5"><h1>Register page - coming later</h1></div>;
}

function App() {
  return (
    // <Routes> looks at the browser's current URL and renders whichever
    // <Route> matches - this is React's replacement for FastAPI deciding
    // which @router.get(...) function to run based on the URL path.
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/todos"
        element={
          <ProtectedRoute>
            <Todos />
          </ProtectedRoute>
        }
      />
      <Route path="/register" element={<RegisterPlaceholder />} />
    </Routes>
  );
}

export default App;
