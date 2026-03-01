import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || '';

interface Customer {
  customer_id: string;
  name: string;
  phone: string;
  email: string;
  aadhaar_masked: string;
  pan_masked: string;
  segment: string;
  rm_name: string;
}

interface CustomerListProps {
  onRefreshRequest?: number;
}

const CustomerList: React.FC<CustomerListProps> = ({ onRefreshRequest }) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await fetch(`${API_BASE}/api/cosmos/customers`);
      const data = await resp.json();
      setCustomers(Array.isArray(data) ? data : data.customers || []);
    } catch (err: any) {
      setError('Failed to load customers');
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteCustomer = async (customerId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this customer?')) return;
    setDeleting(customerId);
    try {
      const resp = await fetch(`${API_BASE}/api/cosmos/customers/${customerId}`, { method: 'DELETE' });
      if (resp.ok) {
        setCustomers(prev => prev.filter(c => c.customer_id !== customerId));
        setExpanded(null);
      } else {
        const data = await resp.json();
        alert(data.error || 'Delete failed');
      }
    } catch {
      alert('Delete failed');
    } finally {
      setDeleting(null);
    }
  };

  const isFixedPersona = (id: string) => id.startsWith('CUST-00');

  useEffect(() => { fetchCustomers(); }, [fetchCustomers, onRefreshRequest]);

  const scenarioTag = (id: string) => {
    if (id.includes('ANANYA')) return { label: 'Onboarding', color: '#60a5fa' };
    if (id.includes('PRIYA')) return { label: 'Dispute', color: '#fbbf24' };
    if (id.includes('RAJESH')) return { label: 'Financial', color: '#4ade80' };
    return { label: 'Custom', color: '#c084fc' };
  };

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      background: '#1a1a2e', borderLeft: '1px solid #2a2a3e',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #2a2a3e',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14 }}>👥</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
            Customers
          </span>
          <span style={{
            background: '#2a2a3e', color: '#94a3b8', fontSize: 11,
            padding: '2px 8px', borderRadius: 10, fontWeight: 500,
          }}>
            {customers.length}
          </span>
        </div>
        <button
          onClick={fetchCustomers}
          title="Refresh"
          style={{
            background: 'none', border: 'none', color: '#64748b',
            cursor: 'pointer', fontSize: 14, padding: 4,
          }}
        >
          🔄
        </button>
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {loading && (
          <div style={{ textAlign: 'center', color: '#64748b', padding: 24, fontSize: 12 }}>
            Loading...
          </div>
        )}
        {error && (
          <div style={{ textAlign: 'center', color: '#f87171', padding: 24, fontSize: 12 }}>
            ⚠️ {error}
          </div>
        )}
        {!loading && !error && customers.map((c) => {
          const tag = scenarioTag(c.customer_id);
          const isExpanded = expanded === c.customer_id;
          return (
            <div
              key={c.customer_id}
              onClick={() => setExpanded(isExpanded ? null : c.customer_id)}
              style={{
                padding: '10px 16px', cursor: 'pointer',
                borderBottom: '1px solid #1e1e32',
                background: isExpanded ? '#222240' : 'transparent',
                transition: 'background 0.15s',
              }}
            >
              {/* Summary row */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>
                    {c.name}
                  </div>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                    📱 {c.phone}
                  </div>
                </div>
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: '2px 8px',
                  borderRadius: 4, color: tag.color,
                  background: `${tag.color}20`,
                }}>
                  {tag.label}
                </span>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div style={{
                  marginTop: 10, padding: 10, background: '#16162a',
                  borderRadius: 6, fontSize: 11, color: '#94a3b8', lineHeight: 1.8,
                }}>
                  <div><strong style={{ color: '#64748b' }}>ID:</strong> {c.customer_id}</div>
                  <div><strong style={{ color: '#64748b' }}>Email:</strong> {c.email}</div>
                  <div><strong style={{ color: '#64748b' }}>Aadhaar:</strong> {c.aadhaar_masked}</div>
                  <div><strong style={{ color: '#64748b' }}>PAN:</strong> {c.pan_masked}</div>
                  <div><strong style={{ color: '#64748b' }}>Segment:</strong> {c.segment}</div>
                  <div><strong style={{ color: '#64748b' }}>RM:</strong> {c.rm_name}</div>
                  {!isFixedPersona(c.customer_id) && (
                    <button
                      onClick={(e) => deleteCustomer(c.customer_id, e)}
                      disabled={deleting === c.customer_id}
                      style={{
                        marginTop: 8, padding: '4px 12px', fontSize: 11,
                        background: '#dc262620', color: '#f87171', border: '1px solid #f8717140',
                        borderRadius: 4, cursor: 'pointer', fontWeight: 500,
                      }}
                    >
                      {deleting === c.customer_id ? 'Deleting...' : '🗑️ Delete Customer'}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CustomerList;
