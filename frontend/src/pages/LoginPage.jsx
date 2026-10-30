import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/admin/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid credentials or login failure.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '420px', margin: '3rem auto' }}>
      <div className="card" style={{ padding: '2.5rem' }}>
        <div style={{ marginBottom: '1.75rem', textAlign: 'center' }}>
          <div className="brand-symbol" style={{ margin: '0 auto 1rem', width: 36, height: 36, fontSize: '1rem' }}>
            H
          </div>
          <h1 className="page-title" style={{ fontSize: '1.35rem', marginBottom: '0.35rem' }}>
            Administrator Sign In
          </h1>
          <p className="page-subtitle" style={{ fontSize: '0.85rem' }}>
            Access protected institutional records and inquiry pipelines.
          </p>
        </div>

        {error && (
          <div className="alert alert-error">
            <div>{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="admin_email" className="form-label">Work Email</label>
            <input
              id="admin_email"
              type="email"
              className="form-control"
              placeholder="admin@edtech.org"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="admin_password" className="form-label">Password</label>
            <input
              id="admin_password"
              type="password"
              className="form-control"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.75rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.825rem', borderTop: '1px solid var(--border-light)', paddingTop: '1.25rem' }}>
          <Link to="/" style={{ color: 'var(--text-muted)' }}>← Return to Public Portal</Link>
        </div>
      </div>
    </div>
  );
}
