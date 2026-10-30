import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../api';

const USER_TYPES = ['Parent', 'Student', 'School'];
const CATEGORIES = ['Scholarship', 'Concert', 'Admission', 'General Query'];

export default function InquiryPage() {
  const [formData, setFormData] = useState({
    user_type: 'Student',
    category: 'Admission',
    name: '',
    email: '',
    phone: '',
    message: '',
  });

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [generalError, setGeneralError] = useState('');

  const validateFrontend = () => {
    const errs = {};
    if (!formData.name.trim() || formData.name.trim().length < 2) {
      errs.name = 'Full name is required (at least 2 characters).';
    }
    if (!formData.email.trim() || !/^\S+@\S+\.\S+$/.test(formData.email.trim())) {
      errs.email = 'Please provide a valid email address.';
    }
    const phoneRegex = /^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9()]{6,30}$/;
    if (!formData.phone.trim() || !phoneRegex.test(formData.phone.trim())) {
      errs.phone = 'Valid phone number required (e.g. +91 98765 43210 or 555-019-2834).';
    }
    if (!formData.message.trim() || formData.message.trim().length < 10) {
      errs.message = 'Please provide details for your inquiry (minimum 10 characters).';
    }
    return errs;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccessMessage('');
    setGeneralError('');

    const validationErrs = validateFrontend();
    if (Object.keys(validationErrs).length > 0) {
      setErrors(validationErrs);
      return;
    }

    setSubmitting(true);
    try {
      await apiRequest('/api/inquiries', {
        method: 'POST',
        body: {
          user_type: formData.user_type,
          category: formData.category,
          name: formData.name.trim(),
          email: formData.email.trim(),
          phone: formData.phone.trim(),
          message: formData.message.trim(),
        },
      });

      setSuccessMessage('Your inquiry has been logged successfully. Our admissions and student relations team will review it shortly.');
      setFormData({
        user_type: 'Student',
        category: 'Admission',
        name: '',
        email: '',
        phone: '',
        message: '',
      });
      setErrors({});
    } catch (err) {
      if (err.data?.errors) {
        setErrors(err.data.errors);
      } else {
        setGeneralError(err.message || 'Submission failed. Please check your network and try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="inquiry-layout">
      {/* Left Column: Context / Institution Details */}
      <div>
        <span className="brand-tag" style={{ textTransform: 'uppercase', letterSpacing: '0.06em', fontSize: '0.7rem' }}>
          Admissions & Outreach
        </span>
        <h1 className="page-title" style={{ fontSize: '2rem', marginTop: '0.75rem', lineHeight: 1.25 }}>
          Connect with Hunar EdTech
        </h1>
        <p className="page-subtitle" style={{ marginTop: '0.75rem', fontSize: '1rem' }}>
          Have inquiries regarding admissions, merit scholarships, annual student concerts, or academic partnerships? 
          Complete the form and our coordination office will follow up with verified documentation.
        </p>

        <div style={{ marginTop: '2.5rem', borderTop: '1px solid var(--border-light)', paddingTop: '1.75rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--badge-resolved-dot)' }} />
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Average inquiry response within 24 business hours
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--badge-progress-dot)' }} />
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Directly tracked in institutional PostgreSQL CRM
              </span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '2.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Authorized staff member? <Link to="/admin/login" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Access Admin Console →</Link>
        </div>
      </div>

      {/* Right Column: Clean Form Card */}
      <div className="card" style={{ padding: '2.25rem' }}>
        {successMessage && (
          <div className="alert alert-success">
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <div>{successMessage}</div>
          </div>
        )}
        {generalError && (
          <div className="alert alert-error">
            <div>{generalError}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label htmlFor="user_type" className="form-label">User Type</label>
              <select
                id="user_type"
                name="user_type"
                className="form-control"
                value={formData.user_type}
                onChange={handleChange}
                disabled={submitting}
              >
                {USER_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="category" className="form-label">Inquiry Category</label>
              <select
                id="category"
                name="category"
                className="form-control"
                value={formData.category}
                onChange={handleChange}
                disabled={submitting}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="name" className="form-label">Full Name</label>
            <input
              id="name"
              name="name"
              type="text"
              className={`form-control ${errors.name ? 'has-error' : ''}`}
              placeholder="e.g. Ananya Sharma"
              value={formData.name}
              onChange={handleChange}
              disabled={submitting}
              required
            />
            {errors.name && <div className="field-error">{errors.name}</div>}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                className={`form-control ${errors.email ? 'has-error' : ''}`}
                placeholder="ananya@example.com"
                value={formData.email}
                onChange={handleChange}
                disabled={submitting}
                required
              />
              {errors.email && <div className="field-error">{errors.email}</div>}
            </div>

            <div className="form-group">
              <label htmlFor="phone" className="form-label">Phone Number</label>
              <input
                id="phone"
                name="phone"
                type="tel"
                className={`form-control ${errors.phone ? 'has-error' : ''}`}
                placeholder="+91 98765 43210"
                value={formData.phone}
                onChange={handleChange}
                disabled={submitting}
                required
              />
              {errors.phone && <div className="field-error">{errors.phone}</div>}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="message" className="form-label">Message Details</label>
            <textarea
              id="message"
              name="message"
              rows="4"
              className={`form-control ${errors.message ? 'has-error' : ''}`}
              placeholder="Describe your inquiry or program requirement in detail..."
              value={formData.message}
              onChange={handleChange}
              disabled={submitting}
              required
            />
            {errors.message && <div className="field-error">{errors.message}</div>}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.75rem' }}
            disabled={submitting}
          >
            {submitting ? 'Submitting to Admissions...' : 'Submit Inquiry'}
          </button>
        </form>
      </div>
    </div>
  );
}
