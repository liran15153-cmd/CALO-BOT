import { RotateCcw, Send } from 'lucide-react';
import { useState } from 'react';

import { createChatSession, resetChatSession, sendChatMessage } from './api';
import { formatProviderStatus } from './formatters';

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
      content: 'בקש אימון, תעד ארוחה או בקש סיכום שבועי. אם ספק הבינה המלאכותית לא מוגדר, אגיד את זה בצורה ברורה.'
    }
  ]);
  const [status, setStatus] = useState<'idle' | 'sending' | 'error'>('idle');

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
      setMessages((current) => [...current, { role: 'coach', content: 'לא הצלחתי להגיע לשרת המאמן.' }]);
      setStatus('error');
    }
  }

  async function handleNewChat() {
    try {
      if (sessionId) {
        await resetChatSession(sessionId).catch(() => undefined);
      }
      const nextSession = await createChatSession('צ\'אט מאמן');
      setSessionId(nextSession.id);
      setMessages([
        {
          role: 'coach',
          content: 'צ\'אט חדש התחיל. הפרופיל והמידע הבטיחותי השמור ימשיכו להשפיע על ההמלצות.'
        }
      ]);
      setStatus('idle');
    } catch {
      setMessages((current) => [...current, { role: 'coach', content: 'לא הצלחתי להתחיל צ\'אט חדש. נסה שוב בעוד רגע.' }]);
      setStatus('error');
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-heading split-heading">
        <div>
          <h3>צ'אט מאמן</h3>
          <p>השיחות משתמשות בפרופיל המצומצם ובהיסטוריה האחרונה שלך.</p>
        </div>
        <button
          className="ghost-button"
          type="button"
          onClick={handleNewChat}
        >
          <RotateCcw size={16} aria-hidden="true" />
          צ'אט חדש
        </button>
      </div>

      <div className="message-list" aria-live="polite">
        {messages.map((item, index) => (
          <div key={`${item.role}-${index}-${item.content.slice(0, 12)}`} className={`message-bubble ${item.role}`}>
            <span>{item.content}</span>
            {(item.providerStatus || item.safetyFlagged) && (
              <>
                {' '}
                <small>
                {item.safetyFlagged ? 'נדרשה זהירות בטיחותית' : formatProviderStatus(item.providerStatus)}
                </small>
              </>
            )}
          </div>
        ))}
        {status === 'sending' && <div className="message-bubble coach">חושב...</div>}
        {status === 'error' && <div className="error-text">הבקשה נכשלה</div>}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <label htmlFor="coach-message">הודעה למאמן</label>
        <div className="composer-row">
          <textarea
            id="coach-message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="בקש אימון, תעד ארוחה או בקש סיכום שבועי."
          />
          <button className="primary-button icon-button" type="submit" disabled={status === 'sending'}>
            <Send size={17} aria-hidden="true" />
            שליחה
          </button>
        </div>
      </form>
    </section>
  );
}
