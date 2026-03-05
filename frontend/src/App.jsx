import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage      from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import AdminPage     from './pages/Adminpage';
import authApi       from './service/auth.service';

/* ── Route guards ────────────────────────────────────── */

/**
 * Защищённый маршрут — только для авторизованных пользователей.
 * Если не залогинен — редиректит на главную.
 */
const PrivateRoute = ({ children }) => {
  return authApi.isAuthenticated() ? children : <Navigate to="/" replace />;
};

/**
 * Маршрут только для администраторов.
 * Если залогинен, но не админ — редиректит в личный кабинет.
 */
const AdminRoute = ({ children }) => {
  if (!authApi.isAuthenticated()) return <Navigate to="/" replace />;
  if (!authApi.isAdmin())         return <Navigate to="/dashboard" replace />;
  return children;
};

/* ── App ─────────────────────────────────────────────── */
const App = () => (
  <BrowserRouter>
    <Routes>
      {/* Публичная главная страница */}
      <Route path="/" element={<HomePage />} />

      {/* Личный кабинет — только для авторизованных */}
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardPage />
          </PrivateRoute>
        }
      />

      {/* Панель администратора — только для admin */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminPage />
          </AdminRoute>
        }
      />

      {/* Fallback — редирект на главную */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </BrowserRouter>
);

export default App;