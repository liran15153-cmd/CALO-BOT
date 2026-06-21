import { LogIn, UserPlus } from 'lucide-react';
import { FormEvent, useState } from 'react';

import { signInWithPassword, signUpWithPassword, storeAuthSession, type SupabaseAuthSession } from './auth';

type AuthPanelProps = {
  onAuthenticated: (session: SupabaseAuthSession) => void;
};

export function AuthPanel({ onAuthenticated }: AuthPanelProps) {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'busy' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus('busy');
    setMessage('');
    try {
      const session =
        mode === 'signin' ? await signInWithPassword(email.trim(), password) : await signUpWithPassword(email.trim(), password);
      storeAuthSession(session);
      onAuthenticated(session);
      setStatus('idle');
    } catch {
      setStatus('error');
      setMessage(mode === 'signin' ? 'התחברות נכשלה' : 'יצירת משתמש נכשלה');
    }
  }

  return (
    <section className="panel auth-panel" dir="rtl" lang="he">
      <div className="panel-heading">
        <h3>כניסה ל-CALO Coach</h3>
        <p>הנתונים האישיים נשמרים לפי משתמש Supabase מחובר.</p>
      </div>

      <div className="segmented-control" role="tablist" aria-label="מצב התחברות">
        <button className={mode === 'signin' ? 'active' : ''} type="button" onClick={() => setMode('signin')}>
          <LogIn size={16} aria-hidden="true" />
          כניסה
        </button>
        <button className={mode === 'signup' ? 'active' : ''} type="button" onClick={() => setMode('signup')}>
          <UserPlus size={16} aria-hidden="true" />
          הרשמה
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          אימייל
          <input autoComplete="email" dir="ltr" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          סיסמה
          <input
            autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
            dir="ltr"
            minLength={6}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button className="primary-button" type="submit" disabled={status === 'busy'}>
          {mode === 'signin' ? 'כניסה' : 'יצירת משתמש'}
        </button>
      </form>

      {message ? <p className={status === 'error' ? 'error-text' : 'success-text'}>{message}</p> : null}
    </section>
  );
}
