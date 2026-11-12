import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Scanner from "./pages/Scanner";
import { getSession } from "./auth";

function App() {
  const [user, setUser] = useState(() => {
    const session = getSession();
    return session ? session.user : null;
  });

  return (
    <Routes>
      <Route
        path="/login"
        element={
          user ? <Navigate to="/" replace /> : <Login onLogin={setUser} />
        }
      />

    <Route
      path="/scanner"
      element={
        user ? <Scanner /> : <Navigate to="/login" replace />
      }
    />

    <Route
      path="/"
      element={
        user ? (
          <Dashboard onLogout={() => setUser(null)} />
        ) : (
          <Navigate to="/login" replace />
        )
      }
   />
    </Routes>
  );
}

export default App;
