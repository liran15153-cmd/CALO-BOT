import { beforeEach, describe, expect, it } from 'vitest';

import { getStoredAuthSession, storeAuthSession } from './auth';

const SESSION_KEY = 'calo.supabase.session';

describe('auth session storage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('returns a stored session only when an access token exists', () => {
    storeAuthSession({ access_token: 'user-jwt', user: { id: 'auth-user-1' } });

    expect(getStoredAuthSession()?.access_token).toBe('user-jwt');
  });

  it('clears invalid stored sessions without an access token', () => {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify({ user: { id: 'auth-user-1' } }));

    expect(getStoredAuthSession()).toBeNull();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  it('clears malformed stored sessions', () => {
    window.localStorage.setItem(SESSION_KEY, '{not-json');

    expect(getStoredAuthSession()).toBeNull();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  it('clears expired stored sessions', () => {
    storeAuthSession({ access_token: 'expired-user-jwt', expires_at: 1 });

    expect(getStoredAuthSession()).toBeNull();
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  });
});
