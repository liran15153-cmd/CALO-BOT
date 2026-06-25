import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  clearApiAccessToken,
  createChatSession,
  fetchHealth,
  fetchSettings,
  sendChatMessage,
  setApiAccessToken
} from './api';

describe('API client', () => {
  afterEach(() => {
    clearApiAccessToken();
    vi.unstubAllGlobals();
  });

  it('throws Hebrew API failure errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 503)));

    await expect(fetchSettings()).rejects.toThrow('בקשת API נכשלה: 503');
  });

  it('throws the shared Hebrew error from health checks', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 503)));

    await expect(fetchHealth()).rejects.toThrow('בקשת API נכשלה: 503');
  });

  it('throws the shared Hebrew error from chat requests', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 500)));

    await expect(sendChatMessage('שלום')).rejects.toThrow('בקשת API נכשלה: 500');
  });

  it('uses a Hebrew default chat title', async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ id: 1, title: "צ'אט מאמן", is_active: true }));
    vi.stubGlobal('fetch', fetchMock);

    await createChatSession();

    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ title: "צ'אט מאמן" });
  });

  it('attaches a Supabase bearer token when configured', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({
        session_id: 1,
        user_message_id: 2,
        coach_message_id: 3,
        response: 'ok',
        safety_flagged: false,
        provider_status: 'local_tool'
      })
    );
    vi.stubGlobal('fetch', fetchMock);
    setApiAccessToken('test-access-token');

    await sendChatMessage('שלום');

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-access-token'
        })
      })
    );
  });
});

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body
  } as Response;
}
