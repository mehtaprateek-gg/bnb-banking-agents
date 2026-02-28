import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { AgentEvent, SystemHealth, DemoMode } from '../types';
import { demoScenarios } from '../data/demoScenarios';

interface UseEventStreamReturn {
  events: AgentEvent[];
  health: SystemHealth;
  mode: DemoMode;
  setMode: (mode: DemoMode) => void;
  scenario: string;
  setScenario: (scenario: string) => void;
  speed: number;
  setSpeed: (speed: number) => void;
  isPlaying: boolean;
  play: () => void;
  pause: () => void;
  step: () => void;
  reset: () => void;
  totalEvents: number;
  sendMessage: (message: string, customerId?: string) => Promise<void>;
}

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function useEventStream(): UseEventStreamReturn {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [mode, setMode] = useState<DemoMode>('replay');
  const [scenario, setScenario] = useState<string>('UC2');
  const [speed, setSpeed] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const scenarioEvents = useMemo(() => (demoScenarios as Record<string, { name: string; events: AgentEvent[] }>)[scenario]?.events || [], [scenario]);
  const totalEvents = mode === 'replay' ? scenarioEvents.length : events.length;

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // --- SSE for live mode ---
  useEffect(() => {
    if (mode === 'live') {
      const sse = new EventSource(`${API_BASE}/api/events/stream`);
      sseRef.current = sse;
      sse.onmessage = (evt) => {
        try {
          const raw = JSON.parse(evt.data);
          const mapped: AgentEvent = {
            eventId: raw.event_id,
            timestamp: raw.timestamp,
            sessionId: raw.session_id,
            useCase: raw.use_case || 'demo',
            agentId: raw.agent_id,
            agentName: raw.agent_name,
            eventType: raw.event_type || 'action',
            action: raw.action,
            inputData: raw.input_data || {},
            outputData: raw.output_data || {},
            reasoning: raw.reasoning || '',
            tokensUsed: raw.tokens_used || 0,
            latencyMs: raw.latency_ms || 0,
            confidence: raw.confidence || 0,
            channel: raw.channel || 'mobile',
            customerId: raw.customer_id || '',
            nextAgents: raw.next_agents || [],
            metadata: {
              language: raw.language || 'en',
              sentiment: raw.sentiment || 'neutral',
            },
          };
          setEvents((prev) => [...prev, mapped]);
        } catch { /* ignore parse errors */ }
      };
      return () => { sse.close(); sseRef.current = null; };
    } else {
      if (sseRef.current) { sseRef.current.close(); sseRef.current = null; }
    }
  }, [mode]);

  // --- Send message to backend (live mode) ---
  const sendMessage = useCallback(async (message: string, customerId?: string) => {
    await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        customer_id: customerId || 'CUST-002-PRIYA',
        channel: 'whatsapp',
      }),
    });
  }, []);

  // --- Replay mode logic (unchanged) ---
  const step = useCallback(() => {
    if (indexRef.current < scenarioEvents.length) {
      const nextEvent = scenarioEvents[indexRef.current];
      setEvents((prev) => [...prev, nextEvent]);
      indexRef.current += 1;
    } else {
      stopTimer();
      setIsPlaying(false);
    }
  }, [scenarioEvents, stopTimer]);

  const play = useCallback(() => {
    if (indexRef.current >= scenarioEvents.length) {
      indexRef.current = 0;
      setEvents([]);
    }
    setIsPlaying(true);
    stopTimer();
    const delay = 1500 / speed;
    timerRef.current = setInterval(() => {
      if (indexRef.current < scenarioEvents.length) {
        const nextEvent = scenarioEvents[indexRef.current];
        setEvents((prev) => [...prev, nextEvent]);
        indexRef.current += 1;
      } else {
        stopTimer();
        setIsPlaying(false);
      }
    }, delay);
  }, [scenarioEvents, speed, stopTimer]);

  const pause = useCallback(() => {
    setIsPlaying(false);
    stopTimer();
  }, [stopTimer]);

  const reset = useCallback(() => {
    stopTimer();
    setIsPlaying(false);
    indexRef.current = 0;
    setEvents([]);
  }, [stopTimer]);

  useEffect(() => { reset(); }, [scenario, reset]);

  useEffect(() => {
    if (isPlaying && mode === 'replay') {
      stopTimer();
      const delay = 1500 / speed;
      timerRef.current = setInterval(() => {
        if (indexRef.current < scenarioEvents.length) {
          const nextEvent = scenarioEvents[indexRef.current];
          setEvents((prev) => [...prev, nextEvent]);
          indexRef.current += 1;
        } else {
          stopTimer();
          setIsPlaying(false);
        }
      }, delay);
    }
    return () => stopTimer();
  }, [speed, isPlaying, mode, scenarioEvents, stopTimer]);

  // Compute health
  const lastEvent = events[events.length - 1];
  const uniqueAgents = new Set(events.map((e) => e.agentId));
  const health: SystemHealth = {
    activeAgents: uniqueAgents.size,
    totalAgents: 16,
    messagesInFlight: isPlaying ? Math.min(events.length, 3) : 0,
    totalLatencyMs: events.reduce((sum, e) => sum + e.latencyMs, 0),
    channel: lastEvent?.channel || '—',
    language: lastEvent?.metadata.language || '—',
    activeSession: lastEvent?.sessionId,
  };

  return {
    events, health, mode, setMode, scenario, setScenario,
    speed, setSpeed, isPlaying, play, pause, step, reset, totalEvents,
    sendMessage,
  };
}
