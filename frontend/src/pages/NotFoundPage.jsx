import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div style={{ maxWidth: '440px', margin: '4rem auto', textAlign: 'center' }}>
      <div className="card" style={{ padding: '3rem 2rem' }}>
        <span className="brand-tag" style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}>
          Error 404
        </span>
        <h1 className="page-title" style={{ fontSize: '1.5rem', marginTop: '1rem', marginBottom: '0.5rem' }}>
          Page Not Located
        </h1>
        <p className="page-subtitle" style={{ fontSize: '0.9rem', marginBottom: '2rem' }}>
          The institutional resource or pipeline view you requested is unavailable or has moved.
        </p>
        <Link to="/" className="btn btn-primary" style={{ width: '100%' }}>
          Return to Public Portal
        </Link>
      </div>
    </div>
  );
}
