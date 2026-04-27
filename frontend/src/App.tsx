import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAdmin } from "./hooks/useAdmin";
import ListPage from "./pages/ListPage";
import EditPage from "./pages/EditPage";
import DetailPage from "./pages/DetailPage";
import ChartPage from "./pages/ChartPage";

export default function App() {
  const { isAdmin, login, logout } = useAdmin();

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<ListPage isAdmin={isAdmin} onLogin={login} onLogout={logout} />}
        />
        <Route
          path="/restaurants/new"
          element={isAdmin ? <EditPage /> : <Navigate to="/" replace />}
        />
        <Route path="/restaurants/:id" element={<DetailPage isAdmin={isAdmin} />} />
        <Route
          path="/restaurants/:id/edit"
          element={isAdmin ? <EditPage /> : <Navigate to="/" replace />}
        />
        <Route path="/chart" element={<ChartPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
