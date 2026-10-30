import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import InquiryPage from './pages/InquiryPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './context/AuthContext';

export default function App() {
  const { admin } = useAuth();
  const location = useLocation();

  return (
    <div className="app-container">
      <header className="site-header">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div className="brand-wrapper">
            <div className="brand-symbol">H</div>
            <div>
              <span className="brand-title">Hunar EdTech</span>
              <span className="brand-tag" style={{ marginLeft: '0.5rem' }}>CRM</span>
            </div>
          </div>
        </Link>

        <nav className="nav-links">
          <Link
            to="/"
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Public Inquiry
          </Link>
          {admin ? (
            <Link
              to="/admin/dashboard"
              className={`nav-link ${location.pathname.startsWith('/admin') ? 'active' : ''}`}
            >
              Dashboard
            </Link>
          ) : (
            <Link
              to="/admin/login"
              className={`nav-link ${location.pathname === '/admin/login' ? 'active' : ''}`}
            >
              Staff Sign In
            </Link>
          )}
        </nav>
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<InquiryPage />} />
          <Route path="/admin/login" element={<LoginPage />} />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
}
