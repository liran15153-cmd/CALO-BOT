import { RotateCcw, Send } from 'lucide-react';
import { useEffect, useState } from 'react';

import { createChatSession, fetchChatMessages, resetChatSession, sendChatMessage } from './api';

type Message = {
  role: 'user' | 'coach';
  content: string;
  providerStatus?: string | null;
  safetyFlagged?: boolean;
};

export function ChatPanel() {
  const [message, setMessage] = useState('');
  const [sessionId, setSessionId] = useState<number | undefined>();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'coach',
      content: 'Ask for a workout, log a meal, or summarize your week. If no AI key is configured, I will say so clearly.'
    }
  ]);
  const [status, setStatus] = useState<'idle' | 'sending' | 'error'>('idle');

  useEffect(() => {
    let active = true;
    createChatSession()
      .then(async (session) => {
        if (!active) return;
        setSessionId(session.id);
        const persisted = await fetchChatMessages(session.id);
        if (!active || persisted.length === 0) return;
        setMessages(
          persisted
            .filter((item): item is typeof item & { role: 'user' | 'coach' } => item.role === 'user' || item.role === 'coach')
            .map((item) => ({
              role: item.role,
              content: item.content,
              providerStatus: item.provider_status,
              safetyFlagged: item.safety_flagged
            }))
        );
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }
    setStatus('sending');
    setMessages((current) => [...current, { role: 'user', content: trimmed }]);
    setMessage('');
    try {
      const response = await sendChatMessage(trimmed, sessionId);
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        {
          role: 'coach',
          content: response.response,
          providerStatus: response.provider_status,
          safetyFlagged: response.safety_flagged
        }
      ]);
      setStatus('idle');
    } catch {
      setMessages((current) => [...current, { role: 'coach', content: 'Could not reach the coach API.' }]);
      setStatus('error');
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-heading split-heading">
        <div>
          <h3>Coach chat</h3>
          <p>Persistent coach conversations will use your compact profile and recent history.</p>
        </div>
        <button
          className="ghost-button"
          type="button"
          onClick={async () => {
            if (sessionId) {
              await resetChatSession(sessionId).catch(() => undefined);
            }
            const nextSession = await createChatSession('Coach chat').catch(() => null);
            setSessionId(nextSession?.id);
            setMessages([
              {
                role: 'coach',
                content: 'New chat started. Your profile and long-term memory are kept.'
              }
            ]);
          }}
        >
          <RotateCcw size={16} aria-hidden="true" />
          New chat
        </button>
      </div>

      <div className="message-list" aria-live="polite">
        {messages.map((item, index) => (
          <div key={`${item.role}-${index}-${item.content.slice(0, 12)}`} className={`message-bubble ${item.role}`}>
            {item.content}
            {(item.providerStatus || item.safetyFlagged) && (
              <small>
                {item.safetyFlagged ? 'Safety flagged' : item.providerStatus}
              </small>
            )}
          </div>
        ))}
        {status === 'sending' && <div className="message-bubble coach">Thinking...</div>}
        {status === 'error' && <div className="error-text">Request failed</div>}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <label htmlFor="coach-message">Message the coach</label>
        <div className="composer-row">
          <textarea
            id="coach-message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Ask for a workout, log a meal, or summarize your week."
          />
          <button className="primary-button icon-button" type="submit" disabled={status === 'sending'}>
            <Send size={17} aria-hidden="true" />
            Send
          </button>
        </div>
      </form>
    </section>
  );
}
