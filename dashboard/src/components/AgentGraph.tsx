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

const statusColor: Record<string, string> = {
  active: '#4ade80',
  idle: '#64748b',
  error: '#f87171',
};

function CustomNode({ data }: NodeProps) {
  const bg = data.isActive ? '#2d4a3e' : '#2a2a3e';
  const borderColor = data.isActive ? '#4ade80' : '#444';
  return (
    <div style={{
      background: bg, border: `2px solid ${borderColor}`, borderRadius: 10,
      padding: '8px 14px', minWidth: 120, textAlign: 'center',
      boxShadow: data.isActive ? '0 0 12px rgba(74,222,128,0.3)' : 'none',
      transition: 'all 0.3s',
    }}>
      <Handle type="target" position={Position.Top} style={{ background: '#555' }} />
      <div style={{ fontSize: 20 }}>{data.emoji || '🤖'}</div>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#e2e8f0', marginTop: 2 }}>{data.label}</div>
      {data.status && (
        <div style={{
          fontSize: 9, marginTop: 3, color: statusColor[data.status] || '#64748b',
          textTransform: 'uppercase', letterSpacing: 1,
        }}>
          ● {data.status}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: '#555' }} />
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

const defaultNodes: Node[] = [
  { id: 'customer', position: { x: 400, y: 0 }, data: { label: 'Customer', emoji: '👤', status: 'idle' }, type: 'custom' },
  // Channel layer
  { id: 'whatsapp-agent', position: { x: 100, y: 100 }, data: { label: 'WhatsApp', emoji: '📱', status: 'idle' }, type: 'custom' },
  { id: 'voice-agent', position: { x: 400, y: 100 }, data: { label: 'Voice', emoji: '📞', status: 'idle' }, type: 'custom' },
  { id: 'mobile-agent', position: { x: 700, y: 100 }, data: { label: 'Mobile App', emoji: '📲', status: 'idle' }, type: 'custom' },
  // Language
  { id: 'language-agent', position: { x: 100, y: 220 }, data: { label: 'Language', emoji: '🌐', status: 'idle' }, type: 'custom' },
  // Orchestrator
  { id: 'orchestrator', position: { x: 400, y: 220 }, data: { label: 'Orchestrator', emoji: '🧠', status: 'idle' }, type: 'custom' },
  // Specialist layer
  { id: 'customer360-agent', position: { x: 50, y: 360 }, data: { label: 'Customer 360', emoji: '👤', status: 'idle' }, type: 'custom' },
  { id: 'transaction-agent', position: { x: 210, y: 360 }, data: { label: 'Transaction', emoji: '🔍', status: 'idle' }, type: 'custom' },
  { id: 'fraud-analysis-agent', position: { x: 370, y: 360 }, data: { label: 'Fraud Analysis', emoji: '🔒', status: 'idle' }, type: 'custom' },
  { id: 'card-management-agent', position: { x: 530, y: 360 }, data: { label: 'Card Mgmt', emoji: '💳', status: 'idle' }, type: 'custom' },
  { id: 'case-management-agent', position: { x: 690, y: 360 }, data: { label: 'Case Mgmt', emoji: '📝', status: 'idle' }, type: 'custom' },
  // Lower specialist layer
  { id: 'kyc-agent', position: { x: 50, y: 490 }, data: { label: 'KYC', emoji: '🪪', status: 'idle' }, type: 'custom' },
  { id: 'document-agent', position: { x: 210, y: 490 }, data: { label: 'Documents', emoji: '📄', status: 'idle' }, type: 'custom' },
  { id: 'account-agent', position: { x: 370, y: 490 }, data: { label: 'Account', emoji: '🏦', status: 'idle' }, type: 'custom' },
  { id: 'financial-analysis-agent', position: { x: 530, y: 490 }, data: { label: 'Financial Analysis', emoji: '📊', status: 'idle' }, type: 'custom' },
  { id: 'product-recommendation-agent', position: { x: 690, y: 490 }, data: { label: 'Product Rec', emoji: '🎯', status: 'idle' }, type: 'custom' },
  // Notification
  { id: 'notification-agent', position: { x: 400, y: 610 }, data: { label: 'Notification', emoji: '🔔', status: 'idle' }, type: 'custom' },
];

const defaultEdges: Edge[] = [
  // Customer to channels
  { id: 'e-cust-wa', source: 'customer', target: 'whatsapp-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-cust-voice', source: 'customer', target: 'voice-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-cust-mobile', source: 'customer', target: 'mobile-agent', animated: false, style: { stroke: '#444' } },
  // Channels to orchestrator
  { id: 'e-wa-lang', source: 'whatsapp-agent', target: 'language-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-wa-orch', source: 'whatsapp-agent', target: 'orchestrator', animated: false, style: { stroke: '#444' } },
  { id: 'e-voice-orch', source: 'voice-agent', target: 'orchestrator', animated: false, style: { stroke: '#444' } },
  { id: 'e-mobile-orch', source: 'mobile-agent', target: 'orchestrator', animated: false, style: { stroke: '#444' } },
  { id: 'e-lang-orch', source: 'language-agent', target: 'orchestrator', animated: false, style: { stroke: '#444' } },
  // Orchestrator to specialists
  { id: 'e-orch-c360', source: 'orchestrator', target: 'customer360-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-txn', source: 'orchestrator', target: 'transaction-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-fraud', source: 'orchestrator', target: 'fraud-analysis-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-card', source: 'orchestrator', target: 'card-management-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-case', source: 'orchestrator', target: 'case-management-agent', animated: false, style: { stroke: '#444' } },
  // Orchestrator to lower specialists
  { id: 'e-orch-kyc', source: 'orchestrator', target: 'kyc-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-doc', source: 'orchestrator', target: 'document-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-acc', source: 'orchestrator', target: 'account-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-fin', source: 'orchestrator', target: 'financial-analysis-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-orch-prod', source: 'orchestrator', target: 'product-recommendation-agent', animated: false, style: { stroke: '#444' } },
  // To notification
  { id: 'e-card-notif', source: 'card-management-agent', target: 'notification-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-case-notif', source: 'case-management-agent', target: 'notification-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-acc-notif', source: 'account-agent', target: 'notification-agent', animated: false, style: { stroke: '#444' } },
  { id: 'e-prod-notif', source: 'product-recommendation-agent', target: 'notification-agent', animated: false, style: { stroke: '#444' } },
];

const AgentGraph: React.FC<Props> = ({ events, onSelectAgent }) => {
  const activeAgentIds = useMemo(() => {
    const ids = new Set<string>();
    events.forEach((e) => ids.add(e.agentId));
    return ids;
  }, [events]);

  const lastEvent = events[events.length - 1];
  const currentAgentId = lastEvent?.agentId;

  const nodes = useMemo(() => {
    return defaultNodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        status: node.id === currentAgentId ? 'active' : activeAgentIds.has(node.id) ? 'active' : 'idle',
        isActive: node.id === currentAgentId,
      },
    }));
  }, [activeAgentIds, currentAgentId]);

  const edges = useMemo(() => {
    const activeEdgeSet = new Set<string>();
    for (let i = 0; i < events.length; i++) {
      const evt = events[i];
      if (i > 0) {
        const prev = events[i - 1];
        activeEdgeSet.add(`${prev.agentId}->${evt.agentId}`);
      }
    }
    return defaultEdges.map((edge) => {
      const key = `${edge.source}->${edge.target}`;
      const isActive = activeEdgeSet.has(key);
      return {
        ...edge,
        animated: isActive,
        style: { stroke: isActive ? '#4ade80' : '#444', strokeWidth: isActive ? 2 : 1 },
      };
    });
  }, [events]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    onSelectAgent(node.id);
  }, [onSelectAgent]);

  return (
    <div style={{ width: '100%', height: '100%', background: '#16162a' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        minZoom={0.3}
        maxZoom={1.5}
      >
        <Background color="#333" gap={20} />
        <Controls
          style={{ background: '#2a2a3e', borderRadius: 8, border: '1px solid #444' }}
        />
      </ReactFlow>
    </div>
  );
};

export default AgentGraph;
