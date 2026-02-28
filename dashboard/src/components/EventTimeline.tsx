import React, { useEffect, useRef } from 'react';
import { AgentEvent } from '../types';

interface Props {
  events: AgentEvent[];
  onSelectEvent: (event: AgentEvent) => void;
}

const agentEmoji: Record<string, string> = {
  'whatsapp-agent': '📱',
  'voice-agent': '📞',
  'mobile-agent': '📲',
  'orchestrator': '🧠',
  'card-management-agent': '💳',
  'customer360-agent': '👤',
  'transaction-agent': '🔍',
  'fraud-analysis-agent': '🔒',
  'case-management-agent': '📝',
  'notification-agent': '📲',
  'language-agent': '🌐',
  'kyc-agent': '🪪',
  'document-agent': '📄',
  'account-agent': '🏦',
  'financial-analysis-agent': '📊',
  'product-recommendation-agent': '🎯',
};

const typeColor: Record<string, string> = {
  action: '#60a5fa',
  decision: '#c084fc',
  error: '#f87171',
  handoff: '#fb923c',
};

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

const EventTimeline: React.FC<Props> = ({ events, onSelectEvent }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#1a1a2e', borderLeft: '1px solid #333',
    }}>
      <div style={{
        padding: '10px 16px', fontWeight: 700, fontSize: 14, color: '#e2e8f0',
        borderBottom: '1px solid #333', background: '#1e1e2e',
      }}>
        📋 Event Timeline ({events.length})
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
        {events.length === 0 && (
          <div style={{ color: '#64748b', textAlign: 'center', marginTop: 40 }}>
            No events yet. Select a scenario and press Play.
          </div>
        )}
        {events.map((evt) => (
          <div
            key={evt.eventId}
            onClick={() => onSelectEvent(evt)}
            style={{
              display: 'flex', gap: 10, padding: '8px 10px', marginBottom: 4,
              borderRadius: 6, cursor: 'pointer', borderLeft: `3px solid ${typeColor[evt.eventType]}`,
              background: '#2a2a3e', transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = '#333355'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = '#2a2a3e'; }}
          >
            <span style={{ fontSize: 20, lineHeight: '24px' }}>
              {agentEmoji[evt.agentId] || '🤖'}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: 13, color: '#e2e8f0' }}>{evt.agentName}</span>
                <span style={{ fontSize: 11, color: '#64748b', fontFamily: 'monospace' }}>{formatTime(evt.timestamp)}</span>
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {evt.action}
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <span style={{
                  fontSize: 10, padding: '1px 6px', borderRadius: 4,
                  background: typeColor[evt.eventType] + '22', color: typeColor[evt.eventType],
                  textTransform: 'uppercase', fontWeight: 600,
                }}>
                  {evt.eventType}
                </span>
                {evt.confidence < 1 && (
                  <span style={{ fontSize: 10, color: '#64748b' }}>
                    conf: {(evt.confidence * 100).toFixed(0)}%
                  </span>
                )}
                <span style={{ fontSize: 10, color: '#64748b' }}>{evt.latencyMs}ms</span>
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default EventTimeline;
