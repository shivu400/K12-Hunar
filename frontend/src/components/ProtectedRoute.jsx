import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { admin, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Checking authentication status...</p>
      </div>
    );
  }

  if (!admin) {
    // Redirect to login page while preserving intended destination
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  return children;
}
