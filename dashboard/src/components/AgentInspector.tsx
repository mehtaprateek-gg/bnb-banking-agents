import React from 'react';
import { AgentEvent } from '../types';

interface Props {
  event: AgentEvent | null;
  onClose: () => void;
}

const AgentInspector: React.FC<Props> = ({ event, onClose }) => {
  if (!event) return null;

  const metrics = [
    { label: 'Tokens Used', value: event.tokensUsed, color: '#60a5fa' },
    { label: 'Latency', value: `${event.latencyMs}ms`, color: event.latencyMs > 500 ? '#fbbf24' : '#4ade80' },
    { label: 'Confidence', value: `${(event.confidence * 100).toFixed(0)}%`, color: event.confidence > 0.9 ? '#4ade80' : '#fbbf24' },
  ];

  return (
    <div style={{
      position: 'fixed', right: 0, top: 0, bottom: 0, width: 420,
      background: '#1e1e2e', borderLeft: '2px solid #4ade80',
      display: 'flex', flexDirection: 'column', zIndex: 1000,
      boxShadow: '-4px 0 20px rgba(0,0,0,0.5)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '12px 16px', borderBottom: '1px solid #333',
      }}>
        <span style={{ fontWeight: 700, fontSize: 15, color: '#e2e8f0' }}>
          🔍 Agent Inspector
        </span>
        <button
          onClick={onClose}
          style={{
            background: '#333', border: 'none', color: '#e2e8f0', cursor: 'pointer',
            borderRadius: 4, padding: '4px 10px', fontSize: 14,
          }}
        >
          ✕
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        {/* Agent info */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0' }}>{event.agentName}</div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
            {event.agentId} · {event.eventType.toUpperCase()} · {event.useCase}
          </div>
        </div>

        {/* Action */}
        <div style={{ marginBottom: 16 }}>
          <div style={sectionTitle}>Action</div>
          <div style={{ color: '#cbd5e1', fontSize: 13 }}>{event.action}</div>
        </div>

        {/* Metrics */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
          {metrics.map((m) => (
            <div key={m.label} style={{
              flex: 1, background: '#2a2a3e', borderRadius: 8, padding: '8px 10px', textAlign: 'center',
            }}>
              <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>{m.label}</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: m.color, marginTop: 2 }}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* Reasoning */}
        <div style={{ marginBottom: 16 }}>
          <div style={sectionTitle}>Reasoning</div>
          <div style={{
            color: '#94a3b8', fontSize: 13, lineHeight: 1.5,
            background: '#2a2a3e', borderRadius: 6, padding: 10,
          }}>
            {event.reasoning}
          </div>
        </div>

        {/* Input Data */}
        <div style={{ marginBottom: 16 }}>
          <div style={sectionTitle}>Input Data</div>
          <pre style={jsonBlock}>{JSON.stringify(event.inputData, null, 2)}</pre>
        </div>

        {/* Output Data */}
        <div style={{ marginBottom: 16 }}>
          <div style={sectionTitle}>Output Data</div>
          <pre style={jsonBlock}>{JSON.stringify(event.outputData, null, 2)}</pre>
        </div>

        {/* Metadata */}
        <div style={{ marginBottom: 16 }}>
          <div style={sectionTitle}>Metadata</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Tag label="Channel" value={event.channel} />
            <Tag label="Language" value={event.metadata.language} />
            <Tag label="Sentiment" value={event.metadata.sentiment} />
            <Tag label="Customer" value={event.customerId} />
          </div>
        </div>

        {/* Next agents */}
        {event.nextAgents.length > 0 && (
          <div>
            <div style={sectionTitle}>Next Agents</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {event.nextAgents.map((a) => (
                <span key={a} style={{
                  background: '#3b3b5c', color: '#c084fc', padding: '3px 10px',
                  borderRadius: 12, fontSize: 12,
                }}>
                  → {a}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const sectionTitle: React.CSSProperties = {
  fontSize: 11, color: '#64748b', textTransform: 'uppercase',
  letterSpacing: 1, fontWeight: 600, marginBottom: 6,
};

const jsonBlock: React.CSSProperties = {
  background: '#0d1117', color: '#7ee787', fontSize: 12,
  padding: 10, borderRadius: 6, overflow: 'auto',
  maxHeight: 180, fontFamily: 'Consolas, monospace',
  margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
};

const Tag: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <span style={{
    background: '#2a2a3e', padding: '3px 10px', borderRadius: 12,
    fontSize: 12, color: '#94a3b8',
  }}>
    <span style={{ color: '#64748b' }}>{label}:</span> {value}
  </span>
);

export default AgentInspector;
