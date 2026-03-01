import React, { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || '';

interface AddedCustomer {
  customer_id: string;
  name: string;
  phone: string;
  aadhaar_masked: string;
  pan_masked: string;
  account_number: string;
  rm_name: string;
}

const AddCustomerForm: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AddedCustomer | null>(null);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!name.trim() || !phone.trim()) {
      setError('Name and phone number are required');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const resp = await fetch(`${API_BASE}/api/customers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), phone: phone.trim() }),
      });
      const data = await resp.json();
      if (data.status === 'created') {
        setResult(data.customer);
        setName('');
        setPhone('');
      } else {
        setError(data.error || 'Failed to create customer');
      }
    } catch (err: any) {
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        style={{
          background: '#7c3aed', color: '#fff', border: 'none', borderRadius: 6,
          padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 4,
        }}
      >
        👤+ Add Demo Customer
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center',
      justifyContent: 'center', zIndex: 1000,
    }}
      onClick={() => setIsOpen(false)}
    >
      <div
        style={{
          background: '#1e1e2e', borderRadius: 12, padding: 24, width: 400,
          border: '1px solid #444', boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ margin: '0 0 4px', color: '#e2e8f0', fontSize: 16 }}>
          👤 Register Demo Customer
        </h3>
        <p style={{ margin: '0 0 16px', color: '#64748b', fontSize: 12 }}>
          Enter a real phone number for WhatsApp testing. All other data (Aadhaar, PAN, account) will be auto-generated.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input
            type="text"
            placeholder="Full Name (e.g., Prateem Mehta)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={inputStyle}
          />
          <input
            type="tel"
            placeholder="WhatsApp Number (e.g., 9920195780)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            style={inputStyle}
          />

          {error && (
            <div style={{ color: '#f87171', fontSize: 12 }}>⚠️ {error}</div>
          )}

          {result && (
            <div style={{
              background: '#064e3b', borderRadius: 8, padding: 12,
              fontSize: 12, color: '#6ee7b7', lineHeight: 1.6,
            }}>
              ✅ <strong>{result.name}</strong> registered!<br />
              ID: {result.customer_id}<br />
              Phone: {result.phone}<br />
              Aadhaar: {result.aadhaar_masked} | PAN: {result.pan_masked}<br />
              Account: {result.account_number} | RM: {result.rm_name}<br />
              <span style={{ color: '#94a3b8', fontSize: 11 }}>
                Now send a WhatsApp message from this number to test.
              </span>
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button onClick={() => setIsOpen(false)} style={cancelBtnStyle}>
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              style={{
                ...submitBtnStyle,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? '⏳ Creating...' : '✨ Register'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  background: '#2a2a3e', color: '#e2e8f0', border: '1px solid #444',
  borderRadius: 6, padding: '8px 12px', fontSize: 13, outline: 'none',
};

const cancelBtnStyle: React.CSSProperties = {
  background: '#2a2a3e', color: '#94a3b8', border: '1px solid #444',
  borderRadius: 6, padding: '6px 14px', fontSize: 12, cursor: 'pointer',
};

const submitBtnStyle: React.CSSProperties = {
  background: '#7c3aed', color: '#fff', border: 'none',
  borderRadius: 6, padding: '6px 14px', fontSize: 12, fontWeight: 600,
};

export default AddCustomerForm;
