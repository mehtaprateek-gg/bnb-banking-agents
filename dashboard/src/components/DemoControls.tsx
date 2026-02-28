import React from 'react';
import { DemoMode } from '../types';

interface Props {
  mode: DemoMode;
  onModeChange: (mode: DemoMode) => void;
  scenario: string;
  onScenarioChange: (scenario: string) => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
  isPlaying: boolean;
  onPlay: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: () => void;
  eventCount: number;
  totalEvents: number;
}

const DemoControls: React.FC<Props> = ({
  mode, onModeChange, scenario, onScenarioChange,
  speed, onSpeedChange, isPlaying, onPlay, onPause, onStep, onReset,
  eventCount, totalEvents,
}) => {
  const speeds = [0.5, 1, 2];

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '10px 20px',
      background: '#1e1e2e', borderTop: '1px solid #333', flexWrap: 'wrap',
    }}>
      {/* Mode toggle */}
      <div style={{ display: 'flex', borderRadius: 6, overflow: 'hidden', border: '1px solid #444' }}>
        {(['replay', 'live'] as DemoMode[]).map((m) => (
          <button
            key={m}
            onClick={() => onModeChange(m)}
            style={{
              padding: '6px 14px', fontSize: 12, fontWeight: 600,
              border: 'none', cursor: 'pointer', textTransform: 'uppercase',
              background: mode === m ? '#4ade80' : '#2a2a3e',
              color: mode === m ? '#000' : '#94a3b8',
            }}
          >
            {m === 'replay' ? '🔄 Replay' : '🔴 Live'}
          </button>
        ))}
      </div>

      {/* Scenario selector */}
      <select
        value={scenario}
        onChange={(e) => onScenarioChange(e.target.value)}
        disabled={mode === 'live'}
        style={{
          background: '#2a2a3e', color: '#e2e8f0', border: '1px solid #444',
          borderRadius: 6, padding: '6px 10px', fontSize: 12, cursor: 'pointer',
        }}
      >
        <option value="UC1">UC1: Ananya Onboarding</option>
        <option value="UC2">UC2: Priya Dispute</option>
        <option value="UC3">UC3: Rajesh Financial Health</option>
      </select>

      {/* Playback controls */}
      <div style={{ display: 'flex', gap: 6 }}>
        <CtrlBtn onClick={isPlaying ? onPause : onPlay} disabled={mode === 'live'}>
          {isPlaying ? '⏸' : '▶️'}
        </CtrlBtn>
        <CtrlBtn onClick={onStep} disabled={mode === 'live' || isPlaying}>⏭</CtrlBtn>
        <CtrlBtn onClick={onReset} disabled={mode === 'live'}>🔄</CtrlBtn>
      </div>

      {/* Speed */}
      <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: '#64748b' }}>Speed:</span>
        {speeds.map((s) => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            style={{
              padding: '3px 8px', fontSize: 11, borderRadius: 4, border: 'none',
              cursor: 'pointer', fontWeight: 600,
              background: speed === s ? '#60a5fa' : '#2a2a3e',
              color: speed === s ? '#000' : '#94a3b8',
            }}
          >
            {s}x
          </button>
        ))}
      </div>

      {/* Progress */}
      <div style={{ marginLeft: 'auto', fontSize: 12, color: '#64748b' }}>
        Event {eventCount}/{totalEvents}
      </div>
    </div>
  );
};

const CtrlBtn: React.FC<{ onClick: () => void; disabled?: boolean; children: React.ReactNode }> = ({
  onClick, disabled, children,
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      background: disabled ? '#1a1a2e' : '#2a2a3e',
      border: '1px solid #444', borderRadius: 6,
      color: disabled ? '#444' : '#e2e8f0',
      cursor: disabled ? 'not-allowed' : 'pointer',
      padding: '4px 10px', fontSize: 16,
    }}
  >
    {children}
  </button>
);

export default DemoControls;
