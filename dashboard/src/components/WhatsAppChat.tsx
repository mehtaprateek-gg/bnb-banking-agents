import React, { useEffect, useRef, useState } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || '';

interface ChatMessage {
  id: string;
  phone: string;
  message: string;
  direction: 'inbound' | 'outbound';
  timestamp: number;
}

const WhatsAppChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sseRef = useRef<EventSource | null>(null);
  const msgCounter = useRef(0);

  useEffect(() => {
    const sse = new EventSource(`${API_BASE}/api/events/stream`);
    sseRef.current = sse;

    sse.onmessage = (evt) => {
      try {
        const raw = JSON.parse(evt.data);
        if (raw.type === 'chat') {
          msgCounter.current += 1;
          const chatMsg: ChatMessage = {
            id: `chat-${msgCounter.current}`,
            phone: raw.phone || '',
            message: raw.message || '',
            direction: raw.direction || 'inbound',
            timestamp: raw.timestamp || Date.now() / 1000,
          };
          setMessages((prev) => [...prev, chatMsg]);
        }
      } catch { /* ignore */ }
    };

    return () => { sse.close(); sseRef.current = null; };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (ts: number) => {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      background: '#0b141a', borderLeft: '1px solid #2a2a3e',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 16px', background: '#202c33',
        borderBottom: '1px solid #2a3942',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'linear-gradient(135deg, #00a884 0%, #25d366 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18, color: '#fff', fontWeight: 700,
        }}>B</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e9edef' }}>
            BNB Bank WhatsApp
          </div>
          <div style={{ fontSize: 11, color: '#8696a0' }}>
            +91 99879 61115
          </div>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <span style={{
            fontSize: 10, padding: '3px 8px', borderRadius: 10,
            background: messages.length > 0 ? '#00a88433' : '#2a2a3e',
            color: messages.length > 0 ? '#00a884' : '#64748b',
            fontWeight: 600,
          }}>
            {messages.length > 0 ? '● LIVE' : '○ WAITING'}
          </span>
        </div>
      </div>

      {/* Chat area */}
      <div style={{
        flex: 1, overflowY: 'auto', padding: '12px 16px',
        backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23111b21\' fill-opacity=\'0.4\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        backgroundColor: '#0b141a',
      }}>
        {messages.length === 0 && (
          <div style={{
            textAlign: 'center', marginTop: 60, color: '#8696a0', fontSize: 12,
          }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>💬</div>
            <div>Send a WhatsApp message to</div>
            <div style={{ fontWeight: 600, color: '#e9edef', marginTop: 4 }}>
              +91 99879 61115
            </div>
            <div style={{ marginTop: 8, color: '#667781', fontSize: 11 }}>
              Try: "I want to open an account"
            </div>
          </div>
        )}

        {messages.map((msg) => {
          const isCustomer = msg.direction === 'inbound';
          return (
            <div key={msg.id} style={{
              display: 'flex',
              justifyContent: isCustomer ? 'flex-start' : 'flex-end',
              marginBottom: 4,
            }}>
              <div style={{
                maxWidth: '85%',
                padding: '6px 10px 4px',
                borderRadius: isCustomer ? '0 8px 8px 8px' : '8px 0 8px 8px',
                background: isCustomer ? '#202c33' : '#005c4b',
                color: '#e9edef',
                fontSize: 12,
                lineHeight: 1.5,
                boxShadow: '0 1px 1px rgba(0,0,0,0.13)',
                position: 'relative',
              }}>
                {isCustomer && (
                  <div style={{
                    fontSize: 10, fontWeight: 600, marginBottom: 2,
                    color: '#00a884',
                  }}>
                    Customer ({msg.phone.slice(-4)})
                  </div>
                )}
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {msg.message}
                </div>
                <div style={{
                  fontSize: 9, color: '#8696a0', textAlign: 'right',
                  marginTop: 2,
                }}>
                  {formatTime(msg.timestamp)}
                  {!isCustomer && (
                    <span style={{ marginLeft: 4, color: '#53bdeb' }}>✓✓</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default WhatsAppChat;
