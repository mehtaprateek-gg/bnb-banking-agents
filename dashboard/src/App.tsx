import React, { useState } from 'react';
import SystemHealth from './components/SystemHealth';
import AgentGraph from './components/AgentGraph';
import EventTimeline from './components/EventTimeline';
import AgentInspector from './components/AgentInspector';
import DemoControls from './components/DemoControls';
import CustomerList from './components/CustomerList';
import WhatsAppChat from './components/WhatsAppChat';
import { useEventStream } from './hooks/useEventStream';
import { AgentEvent } from './types';

function App() {
  const {
    events, health, mode, setMode, scenario, setScenario,
    speed, setSpeed, isPlaying, play, pause, step, reset, totalEvents,
  } = useEventStream();

  const [selectedEvent, setSelectedEvent] = useState<AgentEvent | null>(null);
  const [rightPanel, setRightPanel] = useState<'timeline' | 'customers'>('timeline');

  const handleSelectAgent = (agentId: string) => {
    const agentEvents = events.filter((e) => e.agentId === agentId);
    if (agentEvents.length > 0) {
      setSelectedEvent(agentEvents[agentEvents.length - 1]);
    }
  };

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100vh',
      background: '#0f0f1a', color: '#e2e8f0', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      {/* Top bar */}
      <SystemHealth health={health} />

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Agent Graph - 45% */}
        <div style={{ flex: 45, minWidth: 0 }}>
          <AgentGraph events={events} onSelectAgent={handleSelectAgent} />
        </div>
        {/* WhatsApp Chat - 25% */}
        <div style={{ flex: 25, minWidth: 280 }}>
          <WhatsAppChat />
        </div>
        {/* Right panel with tab switcher - 30% */}
        <div style={{ flex: 30, minWidth: 250, display: 'flex', flexDirection: 'column' }}>
          {/* Tab switcher */}
          <div style={{
            display: 'flex', borderBottom: '1px solid #2a2a3e',
            background: '#1a1a2e',
          }}>
            {(['timeline', 'customers'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setRightPanel(tab)}
                style={{
                  flex: 1, padding: '8px 0', border: 'none', cursor: 'pointer',
                  fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                  letterSpacing: 1,
                  background: rightPanel === tab ? '#222240' : 'transparent',
                  color: rightPanel === tab ? '#e2e8f0' : '#64748b',
                  borderBottom: rightPanel === tab ? '2px solid #7c3aed' : '2px solid transparent',
                }}
              >
                {tab === 'timeline' ? '📋 Events' : '👥 Customers'}
              </button>
            ))}
          </div>
          {/* Panel content */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            {rightPanel === 'timeline' ? (
              <EventTimeline events={events} onSelectEvent={setSelectedEvent} />
            ) : (
              <CustomerList />
            )}
          </div>
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
