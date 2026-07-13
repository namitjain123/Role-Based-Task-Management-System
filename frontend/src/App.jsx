import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Todos from "./pages/Todos";
import AddTodo from "./pages/AddTodo";
import EditTodo from "./pages/EditTodo";
import AdminUsers from "./pages/AdminUsers";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminRoute from "./components/AdminRoute";

function App() {
  return (
    // Navbar sits OUTSIDE <Routes>, so it renders on every page no matter
    // which route matches - same job your old layout.html did with
    // {% include "navbar.html" %} on every template.
    <>
      <Navbar />
      <Routes>
        {/* <Routes> looks at the browser's current URL and renders whichever
            <Route> matches - this is React's replacement for FastAPI deciding
            which @router.get(...) function to run based on the URL path. */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/todos"
          element={
            <ProtectedRoute>
              <Todos />
            </ProtectedRoute>
          }
        />
        <Route
          path="/todos/add"
          element={
            <ProtectedRoute>
              <AddTodo />
            </ProtectedRoute>
          }
        />
        <Route
          path="/todos/edit/:todoId"
          element={
            <ProtectedRoute>
              <EditTodo />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <AdminUsers />
            </AdminRoute>
          }
        />
      </Routes>
    </>
  );
}

export default App;
