export interface AgentEvent {
  eventId: string;
  timestamp: string;
  sessionId: string;
  useCase: string;
  agentId: string;
  agentName: string;
  eventType: 'action' | 'decision' | 'error' | 'handoff';
  action: string;
  inputData: Record<string, any>;
  outputData: Record<string, any>;
  reasoning: string;
  tokensUsed: number;
  latencyMs: number;
  confidence: number;
  nextAgents: string[];
  channel: 'whatsapp' | 'voice' | 'mobile';
  customerId: string;
  metadata: {
    language: 'hi' | 'en' | 'hi-en';
    sentiment: 'positive' | 'neutral' | 'negative' | 'frustrated';
  };
}

export interface AgentNode {
  id: string;
  name: string;
  type: 'router' | 'channel' | 'specialist';
  status: 'active' | 'idle' | 'error';
  useCases: string[];
  lastActive?: string;
  calls24h: number;
  avgLatencyMs: number;
}

export interface SystemHealth {
  activeAgents: number;
  totalAgents: number;
  messagesInFlight: number;
  totalLatencyMs: number;
  channel: string;
  language: string;
  activeSession?: string;
}

export type DemoMode = 'live' | 'replay';
