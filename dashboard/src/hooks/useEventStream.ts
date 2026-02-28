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
}

export function useEventStream(): UseEventStreamReturn {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [mode, setMode] = useState<DemoMode>('replay');
  const [scenario, setScenario] = useState<string>('UC2');
  const [speed, setSpeed] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const scenarioEvents = useMemo(() => (demoScenarios as Record<string, { name: string; events: AgentEvent[] }>)[scenario]?.events || [], [scenario]);
  const totalEvents = scenarioEvents.length;

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

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
      // Reset and replay
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

  // Reset when scenario changes
  useEffect(() => {
    reset();
  }, [scenario, reset]);

  // Restart timer when speed changes during playback
  useEffect(() => {
    if (isPlaying) {
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
  }, [speed, isPlaying, scenarioEvents, stopTimer]);

  // Compute health from events
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
  };
}
