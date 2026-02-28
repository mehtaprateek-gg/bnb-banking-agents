import React, { useState } from 'react';
import SystemHealth from './components/SystemHealth';
import AgentGraph from './components/AgentGraph';
import EventTimeline from './components/EventTimeline';
import AgentInspector from './components/AgentInspector';
import DemoControls from './components/DemoControls';
import { useEventStream } from './hooks/useEventStream';
import { AgentEvent } from './types';

function App() {
  const {
    events, health, mode, setMode, scenario, setScenario,
    speed, setSpeed, isPlaying, play, pause, step, reset, totalEvents,
  } = useEventStream();

  const [selectedEvent, setSelectedEvent] = useState<AgentEvent | null>(null);

  const handleSelectAgent = (agentId: string) => {
    const agentEvents = events.filter((e) => e.agentId === agentId);
    if (agentEvents.length > 0) {
      setSelectedEvent(agentEvents[agentEvents.length - 1]);
    }
  };

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100vh',
      background: '#16162a', color: '#e2e8f0', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      {/* Top bar */}
      <SystemHealth health={health} />

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Agent Graph - 60% */}
        <div style={{ flex: 6, minWidth: 0 }}>
          <AgentGraph events={events} onSelectAgent={handleSelectAgent} />
        </div>
        {/* Event Timeline - 40% */}
        <div style={{ flex: 4, minWidth: 300 }}>
          <EventTimeline events={events} onSelectEvent={setSelectedEvent} />
        </div>
      </div>

      {/* Bottom controls */}
      <DemoControls
        mode={mode}
        onModeChange={setMode}
        scenario={scenario}
        onScenarioChange={setScenario}
        speed={speed}
        onSpeedChange={setSpeed}
        isPlaying={isPlaying}
        onPlay={play}
        onPause={pause}
        onStep={step}
        onReset={reset}
        eventCount={events.length}
        totalEvents={totalEvents}
      />

      {/* Inspector panel */}
      <AgentInspector event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}

export default App;
