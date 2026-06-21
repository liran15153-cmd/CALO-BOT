const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL ?? '';
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? '';
const SESSION_KEY = 'calo.supabase.session';

export type SupabaseAuthSession = {
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
  user?: {
    id?: string;
    email?: string;
  };
};

export function isSupabaseAuthConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_PUBLISHABLE_KEY);
}

export function getStoredAuthSession(): SupabaseAuthSession | null {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as SupabaseAuthSession) : null;
  } catch {
    return null;
  }
}

export function storeAuthSession(session: SupabaseAuthSession): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredAuthSession(): void {
  window.localStorage.removeItem(SESSION_KEY);
}

export async function signInWithPassword(email: string, password: string): Promise<SupabaseAuthSession> {
  return requestAuth('/auth/v1/token?grant_type=password', { email, password });
}

export async function signUpWithPassword(email: string, password: string): Promise<SupabaseAuthSession> {
  return requestAuth('/auth/v1/signup', { email, password });
}

async function requestAuth(path: string, body: Record<string, string>): Promise<SupabaseAuthSession> {
  if (!isSupabaseAuthConfigured()) {
    throw new Error('Supabase Auth is not configured');
  }
  const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}${path}`, {
    method: 'POST',
    headers: {
      apikey: SUPABASE_PUBLISHABLE_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`Supabase Auth failed: ${response.status}`);
  }
  const payload = (await response.json()) as SupabaseAuthSession;
  if (!payload.access_token) {
    throw new Error('Supabase Auth did not return an access token');
  }
  return payload;
}
