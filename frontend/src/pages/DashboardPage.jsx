import React, { useState, useEffect, useRef } from 'react';
import { apiRequest } from '../api';
import { useAuth } from '../context/AuthContext';

const STATUS_OPTIONS = ['New', 'In Progress', 'Resolved'];
const CATEGORY_OPTIONS = ['Scholarship', 'Concert', 'Admission', 'General Query'];
const USER_TYPE_OPTIONS = ['Parent', 'Student', 'School'];

export default function DashboardPage() {
  const { admin, logout } = useAuth();

  // Filters & Search state
  const [category, setCategory] = useState('');
  const [userType, setUserType] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const limit = 10;

  // Data & loading state
  const [inquiries, setInquiries] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Selected inquiry for detail modal
  const [selectedInquiry, setSelectedInquiry] = useState(null);
  const [statusUpdating, setStatusUpdating] = useState(false);

  // Stale request race condition prevention
  const latestRequestId = useRef(0);

  useEffect(() => {
    const fetchInquiries = async () => {
      const currentId = ++latestRequestId.current;
      setLoading(true);
      setError('');

      try {
        const queryParams = new URLSearchParams();
        if (category) queryParams.set('category', category);
        if (userType) queryParams.set('userType', userType);
        if (searchTerm.trim()) queryParams.set('search', searchTerm.trim());
        queryParams.set('page', page.toString());
        queryParams.set('limit', limit.toString());

        const data = await apiRequest(`/api/inquiries?${queryParams.toString()}`);

        if (currentId === latestRequestId.current) {
          setInquiries(data.items);
          setTotal(data.total);
          setTotalPages(data.total_pages);
        }
      } catch (err) {
        if (currentId === latestRequestId.current) {
          setError(err.message || 'Failed to fetch inquiries.');
        }
      } finally {
        if (currentId === latestRequestId.current) {
          setLoading(false);
        }
      }
    };

    const timeoutId = setTimeout(fetchInquiries, 350);
    return () => clearTimeout(timeoutId);
  }, [category, userType, searchTerm, page]);

  const handleClearFilters = () => {
    setCategory('');
    setUserType('');
    setSearchTerm('');
    setPage(1);
  };

  const handleStatusChange = async (inquiryId, newStatus) => {
    setStatusUpdating(true);
    try {
      const updated = await apiRequest(`/api/inquiries/${inquiryId}/status`, {
        method: 'PATCH',
        body: { status: newStatus },
      });

      setInquiries((prev) =>
        prev.map((item) => (item.id === inquiryId ? { ...item, status: updated.status } : item))
      );

      if (selectedInquiry && selectedInquiry.id === inquiryId) {
        setSelectedInquiry(updated);
      }
    } catch (err) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setStatusUpdating(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '—';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'New':
        return 'status-new';
      case 'In Progress':
        return 'status-progress';
      case 'Resolved':
        return 'status-resolved';
      default:
        return 'status-new';
    }
  };

  return (
    <div>
      {/* Dashboard Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Inquiries & Admissions Pipeline</h1>
          <p className="page-subtitle">
            Authenticated administrator: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{admin?.email}</span>
          </p>
        </div>
        <button onClick={logout} className="btn btn-secondary btn-sm" id="logout-btn">
          Sign Out
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem', alignItems: 'end' }}>
          <div>
            <label htmlFor="search_input" className="form-label">Search Inquirer</label>
            <input
              id="search_input"
              type="text"
              className="form-control"
              placeholder="Search by name or phone..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
            />
          </div>

          <div>
            <label htmlFor="category_filter" className="form-label">Inquiry Category</label>
            <select
              id="category_filter"
              className="form-control"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Categories</option>
              {CATEGORY_OPTIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="user_type_filter" className="form-label">User Type</label>
            <select
              id="user_type_filter"
              className="form-control"
              value={userType}
              onChange={(e) => {
                setUserType(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All User Types</option>
              {USER_TYPE_OPTIONS.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>

          <div>
            <button
              onClick={handleClearFilters}
              className="btn btn-secondary"
              style={{ width: '100%' }}
              disabled={!category && !userType && !searchTerm}
            >
              Reset Filters
            </button>
          </div>
        </div>
      </div>

      {/* Main Table Content */}
      <div className="table-container">
        {error && <div className="alert alert-error" style={{ margin: '1rem' }}>{error}</div>}

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Date Logged</th>
                <th>Inquirer</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Role</th>
                <th>Category</th>
                <th>Current Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '3.5rem', color: 'var(--text-muted)' }}>
                    Loading records from database...
                  </td>
                </tr>
              ) : inquiries.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '3.5rem', color: 'var(--text-muted)' }}>
                    {category || userType || searchTerm
                      ? 'No inquiries match your active filter criteria.'
                      : 'No inquiries recorded yet. Submissions from the public form will appear here.'}
                  </td>
                </tr>
              ) : (
                inquiries.map((inq) => (
                  <tr key={inq.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                      {formatDate(inq.created_at)}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {inq.name}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{inq.phone}</td>
                    <td>{inq.email}</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-light)' }}>
                        {inq.user_type}
                      </span>
                    </td>
                    <td>{inq.category}</td>
                    <td>
                      <select
                        aria-label={`Update status for ${inq.name}`}
                        className={`status-pill ${getStatusClass(inq.status)}`}
                        value={inq.status}
                        onChange={(e) => handleStatusChange(inq.id, e.target.value)}
                        disabled={statusUpdating}
                      >
                        {STATUS_OPTIONS.map((st) => (
                          <option key={st} value={st}>{st}</option>
                        ))}
                      </select>
                    </td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelectedInquiry(inq)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Server-Side Pagination */}
        {total > 0 && (
          <div className="pagination-bar">
            <span style={{ color: 'var(--text-muted)' }}>
              Showing <strong>{inquiries.length > 0 ? (page - 1) * limit + 1 : 0}</strong> to{' '}
              <strong>{Math.min(page * limit, total)}</strong> of <strong>{total}</strong> inquiries
            </span>

            <div className="pagination-controls">
              <button
                className="btn btn-secondary btn-sm"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
              >
                Previous
              </button>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 0.5rem' }}>
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages || loading}
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedInquiry && (
        <div className="modal-overlay" onClick={() => setSelectedInquiry(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Inquiry Record Details</h2>
              <button className="close-btn" onClick={() => setSelectedInquiry(null)} aria-label="Close modal">
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Inquirer Name</div>
                <div style={{ fontWeight: 600 }}>{selectedInquiry.name}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Role Type</div>
                <div>{selectedInquiry.user_type}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Email Address</div>
                <div>{selectedInquiry.email}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Phone Number</div>
                <div style={{ fontFamily: 'monospace' }}>{selectedInquiry.phone}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Category</div>
                <div>{selectedInquiry.category}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Status</div>
                <select
                  aria-label="Modal status select"
                  className={`status-pill ${getStatusClass(selectedInquiry.status)}`}
                  value={selectedInquiry.status}
                  onChange={(e) => handleStatusChange(selectedInquiry.id, e.target.value)}
                  disabled={statusUpdating}
                >
                  {STATUS_OPTIONS.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1.75rem' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                Full Message / Inquiry Body
              </div>
              <div style={{ 
                background: '#f8fafc', 
                padding: '1.15rem', 
                borderRadius: 'var(--radius-md)', 
                border: '1px solid var(--border-light)', 
                whiteSpace: 'pre-wrap', 
                lineHeight: '1.6',
                fontSize: '0.9rem',
                color: 'var(--text-primary)'
              }}>
                {selectedInquiry.message}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Received on {formatDate(selectedInquiry.created_at)}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedInquiry(null)}>
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
