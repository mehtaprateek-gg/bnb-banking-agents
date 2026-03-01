import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  Position,
  Handle,
  NodeProps,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AgentEvent } from '../types';

interface Props {
  events: AgentEvent[];
  onSelectAgent: (agentId: string) => void;
}

// Professional color palette per layer
const layerColors: Record<string, { bg: string; border: string; glow: string }> = {
  customer:    { bg: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', border: '#475569', glow: '#60a5fa' },
  channel:     { bg: 'linear-gradient(135deg, #1a2332 0%, #1e3a4f 100%)', border: '#2563eb', glow: '#3b82f6' },
  router:      { bg: 'linear-gradient(135deg, #1f1835 0%, #312e5c 100%)', border: '#7c3aed', glow: '#8b5cf6' },
  specialist:  { bg: 'linear-gradient(135deg, #1a2e1a 0%, #1f3d2b 100%)', border: '#16a34a', glow: '#4ade80' },
  service:     { bg: 'linear-gradient(135deg, #2d1f1a 0%, #3d2b1f 100%)', border: '#d97706', glow: '#fbbf24' },
};

function CustomNode({ data }: NodeProps) {
  const layer = data.layer || 'specialist';
  const colors = layerColors[layer] || layerColors.specialist;
  const isActive = data.isActive;
  const isTouched = data.isTouched;

  return (
    <div style={{
      background: isActive ? colors.bg : isTouched ? colors.bg : 'linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%)',
      border: `2px solid ${isActive ? colors.glow : isTouched ? colors.border : '#333'}`,
      borderRadius: 12,
      padding: '10px 16px',
      minWidth: 130,
      textAlign: 'center',
      boxShadow: isActive
        ? `0 0 25px ${colors.glow}50, 0 0 50px ${colors.glow}30, 0 0 80px ${colors.glow}15`
        : isTouched ? `0 0 12px ${colors.border}40` : 'none',
      transition: 'all 0.4s ease',
      animation: isActive ? 'pulse 2s ease-in-out infinite' : 'none',
    }}>
      <Handle type="target" position={Position.Top} style={{ background: isActive ? colors.glow : '#555', width: 6, height: 6 }} />
      <div style={{ fontSize: 22, filter: isActive ? 'none' : isTouched ? 'none' : 'grayscale(0.5) opacity(0.7)' }}>
        {data.emoji || '🤖'}
      </div>
      <div style={{
        fontSize: 11, fontWeight: 600,
        color: isActive ? '#fff' : isTouched ? '#e2e8f0' : '#94a3b8',
        marginTop: 3,
      }}>
        {data.label}
      </div>
      {(isActive || isTouched) && data.confidence > 0 && (
        <div style={{
          fontSize: 9, marginTop: 4, color: colors.glow,
          background: `${colors.glow}15`, borderRadius: 4,
          padding: '1px 6px', display: 'inline-block',
        }}>
          {(data.confidence * 100).toFixed(0)}% · {data.latency}ms
        </div>
      )}
      {isActive && (
        <div style={{
          fontSize: 8, marginTop: 3, color: colors.glow,
          textTransform: 'uppercase', letterSpacing: 1.5, fontWeight: 700,
        }}>
          ● ACTIVE
        </div>
      )}
      {isActive && data.action && (
        <div style={{
          fontSize: 8, marginTop: 2, color: '#94a3b8',
          maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {data.action}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: isActive ? colors.glow : '#555', width: 6, height: 6 }} />
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

// Layer label nodes
const layerLabels: Node[] = [
  { id: 'label-channels', position: { x: -30, y: 88 }, type: 'default', data: { label: 'CHANNELS' }, style: { background: 'transparent', border: 'none', color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: 2, width: 80 }, selectable: false, draggable: false },
  { id: 'label-intelligence', position: { x: -30, y: 208 }, type: 'default', data: { label: 'ROUTING' }, style: { background: 'transparent', border: 'none', color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: 2, width: 80 }, selectable: false, draggable: false },
  { id: 'label-specialists', position: { x: -30, y: 348 }, type: 'default', data: { label: 'AGENTS' }, style: { background: 'transparent', border: 'none', color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: 2, width: 80 }, selectable: false, draggable: false },
  { id: 'label-services', position: { x: -30, y: 488 }, type: 'default', data: { label: 'SERVICES' }, style: { background: 'transparent', border: 'none', color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: 2, width: 80 }, selectable: false, draggable: false },
];

const defaultNodes: Node[] = [
  { id: 'customer', position: { x: 400, y: 0 }, data: { label: 'Customer', emoji: '👤', layer: 'customer' }, type: 'custom' },
  // Channel layer
  { id: 'whatsapp-agent', position: { x: 120, y: 100 }, data: { label: 'WhatsApp', emoji: '📱', layer: 'channel' }, type: 'custom' },
  { id: 'voice-agent', position: { x: 400, y: 100 }, data: { label: 'Voice', emoji: '🎙️', layer: 'channel' }, type: 'custom' },
  { id: 'mobile-agent', position: { x: 680, y: 100 }, data: { label: 'Mobile App', emoji: '📲', layer: 'channel' }, type: 'custom' },
  // Router layer
  { id: 'language-agent', position: { x: 120, y: 220 }, data: { label: 'Language NLP', emoji: '🌐', layer: 'router' }, type: 'custom' },
  { id: 'orchestrator', position: { x: 400, y: 220 }, data: { label: 'Orchestrator', emoji: '🧠', layer: 'router' }, type: 'custom' },
  // Specialist layer
  { id: 'customer360-agent', position: { x: 60, y: 360 }, data: { label: 'Customer 360', emoji: '👤', layer: 'specialist' }, type: 'custom' },
  { id: 'transaction-agent', position: { x: 220, y: 360 }, data: { label: 'Transaction', emoji: '🔍', layer: 'specialist' }, type: 'custom' },
  { id: 'fraud-analysis-agent', position: { x: 380, y: 360 }, data: { label: 'Fraud Analysis', emoji: '🛡️', layer: 'specialist' }, type: 'custom' },
  { id: 'card-management-agent', position: { x: 540, y: 360 }, data: { label: 'Card Mgmt', emoji: '💳', layer: 'specialist' }, type: 'custom' },
  { id: 'case-management-agent', position: { x: 700, y: 360 }, data: { label: 'Case Mgmt', emoji: '📋', layer: 'specialist' }, type: 'custom' },
  // Service layer
  { id: 'kyc-agent', position: { x: 60, y: 500 }, data: { label: 'KYC / AML', emoji: '🪪', layer: 'service' }, type: 'custom' },
  { id: 'document-agent', position: { x: 220, y: 500 }, data: { label: 'Document AI', emoji: '📄', layer: 'service' }, type: 'custom' },
  { id: 'account-agent', position: { x: 380, y: 500 }, data: { label: 'Account', emoji: '🏦', layer: 'service' }, type: 'custom' },
  { id: 'financial-analysis-agent', position: { x: 540, y: 500 }, data: { label: 'Analytics', emoji: '📊', layer: 'service' }, type: 'custom' },
  { id: 'product-recommendation-agent', position: { x: 700, y: 500 }, data: { label: 'Product Rec', emoji: '🎯', layer: 'service' }, type: 'custom' },
  // Notification
  { id: 'notification-agent', position: { x: 400, y: 620 }, data: { label: 'Notification', emoji: '🔔', layer: 'service' }, type: 'custom' },
  ...layerLabels,
];

const defaultEdges: Edge[] = [
  // Customer to channels
  { id: 'e-cust-wa', source: 'customer', target: 'whatsapp-agent', style: { stroke: '#334' } },
  { id: 'e-cust-voice', source: 'customer', target: 'voice-agent', style: { stroke: '#334' } },
  { id: 'e-cust-mobile', source: 'customer', target: 'mobile-agent', style: { stroke: '#334' } },
  // Channels to orchestrator
  { id: 'e-wa-lang', source: 'whatsapp-agent', target: 'language-agent', style: { stroke: '#334' } },
  { id: 'e-wa-orch', source: 'whatsapp-agent', target: 'orchestrator', style: { stroke: '#334' } },
  { id: 'e-voice-orch', source: 'voice-agent', target: 'orchestrator', style: { stroke: '#334' } },
  { id: 'e-mobile-orch', source: 'mobile-agent', target: 'orchestrator', style: { stroke: '#334' } },
  { id: 'e-lang-orch', source: 'language-agent', target: 'orchestrator', style: { stroke: '#334' } },
  // Orchestrator to specialists
  { id: 'e-orch-c360', source: 'orchestrator', target: 'customer360-agent', style: { stroke: '#334' } },
  { id: 'e-orch-txn', source: 'orchestrator', target: 'transaction-agent', style: { stroke: '#334' } },
  { id: 'e-orch-fraud', source: 'orchestrator', target: 'fraud-analysis-agent', style: { stroke: '#334' } },
  { id: 'e-orch-card', source: 'orchestrator', target: 'card-management-agent', style: { stroke: '#334' } },
  { id: 'e-orch-case', source: 'orchestrator', target: 'case-management-agent', style: { stroke: '#334' } },
  // Orchestrator to services
  { id: 'e-orch-kyc', source: 'orchestrator', target: 'kyc-agent', style: { stroke: '#334' } },
  { id: 'e-orch-doc', source: 'orchestrator', target: 'document-agent', style: { stroke: '#334' } },
  { id: 'e-orch-acc', source: 'orchestrator', target: 'account-agent', style: { stroke: '#334' } },
  { id: 'e-orch-fin', source: 'orchestrator', target: 'financial-analysis-agent', style: { stroke: '#334' } },
  { id: 'e-orch-prod', source: 'orchestrator', target: 'product-recommendation-agent', style: { stroke: '#334' } },
  // To notification
  { id: 'e-card-notif', source: 'card-management-agent', target: 'notification-agent', style: { stroke: '#334' } },
  { id: 'e-case-notif', source: 'case-management-agent', target: 'notification-agent', style: { stroke: '#334' } },
  { id: 'e-acc-notif', source: 'account-agent', target: 'notification-agent', style: { stroke: '#334' } },
  { id: 'e-prod-notif', source: 'product-recommendation-agent', target: 'notification-agent', style: { stroke: '#334' } },
];

const AgentGraph: React.FC<Props> = ({ events, onSelectAgent }) => {
  // Track which agents have been activated and their metrics
  const agentMetrics = useMemo(() => {
    const metrics: Record<string, { confidence: number; latency: number }> = {};
    events.forEach((e) => {
      metrics[e.agentId] = {
        confidence: e.confidence || metrics[e.agentId]?.confidence || 0,
        latency: e.latencyMs || metrics[e.agentId]?.latency || 0,
      };
    });
    return metrics;
  }, [events]);

  const activeAgentIds = useMemo(() => {
    const ids = new Set<string>();
    events.forEach((e) => ids.add(e.agentId));
    return ids;
  }, [events]);

  const lastEvent = events[events.length - 1];
  const currentAgentId = lastEvent?.agentId;

  const nodes = useMemo(() => {
    return defaultNodes.map((node) => {
      if (node.type !== 'custom') return node;
      const metrics = agentMetrics[node.id];
      // Find latest action for this agent
      const lastAgentEvent = [...events].reverse().find(e => e.agentId === node.id);
      return {
        ...node,
        data: {
          ...node.data,
          isActive: node.id === currentAgentId,
          isTouched: activeAgentIds.has(node.id),
          confidence: metrics?.confidence || 0,
          latency: Math.round(metrics?.latency || 0),
          action: lastAgentEvent?.action?.replace(/_/g, ' ') || '',
        },
      };
    });
  }, [activeAgentIds, currentAgentId, agentMetrics, events]);

  const edges = useMemo(() => {
    // Build set of recently active agent IDs (last 5 events) for flow visualization
    const recentIds = new Set<string>();
    events.slice(-5).forEach((e) => recentIds.add(e.agentId));

    return defaultEdges.map((edge) => {
      const sourceIsActive = edge.source === currentAgentId;
      const targetIsActive = edge.target === currentAgentId;
      const bothTouched = activeAgentIds.has(edge.source) && activeAgentIds.has(edge.target);
      const recentFlow = recentIds.has(edge.source) && recentIds.has(edge.target);

      // Edge TO/FROM currently active agent: bright green, animated, glowing
      if (sourceIsActive || targetIsActive) {
        return {
          ...edge,
          animated: true,
          style: {
            stroke: '#4ade80',
            strokeWidth: 3,
            filter: 'drop-shadow(0 0 8px #4ade8090)',
          },
        };
      }
      // Edge between recently active agents: blue, animated
      if (recentFlow) {
        return {
          ...edge,
          animated: true,
          style: {
            stroke: '#60a5fa',
            strokeWidth: 2,
            filter: 'drop-shadow(0 0 4px #60a5fa60)',
          },
        };
      }
      // Edge between any previously touched agents: subtle glow
      if (bothTouched) {
        return {
          ...edge,
          style: {
            stroke: '#475569',
            strokeWidth: 1.5,
          },
        };
      }
      // Inactive edge
      return {
        ...edge,
        style: { stroke: '#1e293b', strokeWidth: 1 },
      };
    });
  }, [events, currentAgentId, activeAgentIds]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    if (node.type === 'custom') onSelectAgent(node.id);
  }, [onSelectAgent]);

  return (
    <div style={{ width: '100%', height: '100%', background: '#0f0f1a' }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); filter: brightness(1); }
          50% { transform: scale(1.06); filter: brightness(1.3); }
        }
        @keyframes glowRing {
          0% { box-shadow: 0 0 5px currentColor, 0 0 10px currentColor; }
          50% { box-shadow: 0 0 20px currentColor, 0 0 40px currentColor, 0 0 60px currentColor; }
          100% { box-shadow: 0 0 5px currentColor, 0 0 10px currentColor; }
        }
      `}</style>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        minZoom={0.3}
        maxZoom={1.5}
      >
        <Background color="#1a1a2e" gap={24} size={1} />
        <Controls
          style={{ background: '#1e1e2e', borderRadius: 8, border: '1px solid #333' }}
        />
      </ReactFlow>
    </div>
  );
};

export default AgentGraph;
