import React from 'react';
import { SystemHealth as SystemHealthType } from '../types';

interface Props {
  health: SystemHealthType;
}

const SystemHealth: React.FC<Props> = ({ health }) => {
  const agentRatio = health.activeAgents / health.totalAgents;
  const agentColor = agentRatio > 0.7 ? '#4ade80' : agentRatio > 0.3 ? '#fbbf24' : '#f87171';
  const latencyColor = health.totalLatencyMs < 1000 ? '#4ade80' : health.totalLatencyMs < 3000 ? '#fbbf24' : '#f87171';

  const stats = [
    { label: 'Active Agents', value: `${health.activeAgents}/${health.totalAgents}`, color: agentColor },
    { label: 'Messages In Flight', value: health.messagesInFlight, color: health.messagesInFlight > 10 ? '#fbbf24' : '#4ade80' },
    { label: 'Total Latency', value: `${health.totalLatencyMs}ms`, color: latencyColor },
    { label: 'Channel', value: health.channel || '—', color: '#60a5fa' },
    { label: 'Language', value: health.language || '—', color: '#c084fc' },
  ];

  return (
    <div style={{
      display: 'flex', gap: 16, padding: '12px 20px',
      background: '#1e1e2e', borderBottom: '1px solid #333',
      alignItems: 'center', flexWrap: 'wrap',
    }}>
      <span style={{ fontSize: 20, fontWeight: 700, color: '#e2e8f0', marginRight: 12 }}>
        🏦 BNB Agent Orchestration Dashboard
      </span>
      {stats.map((s) => (
        <div key={s.label} style={{
          background: '#2a2a3e', borderRadius: 8, padding: '8px 16px',
          minWidth: 130, textAlign: 'center',
        }}>
          <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 }}>{s.label}</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: s.color, marginTop: 2 }}>{s.value}</div>
        </div>
      ))}
      {health.activeSession && (
        <div style={{ marginLeft: 'auto', fontSize: 12, color: '#64748b' }}>
          Session: {health.activeSession}
        </div>
      )}
    </div>
  );
};

export default SystemHealth;
