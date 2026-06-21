import { afterEach, describe, expect, it, vi } from 'vitest';

import { clearApiAccessToken, fetchHealth, sendChatMessage, setApiAccessToken } from './api';

describe('API client errors', () => {
  afterEach(() => {
    clearApiAccessToken();
    vi.unstubAllGlobals();
  });

  it('throws Hebrew health check errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 503)));

    await expect(fetchHealth()).rejects.toThrow('503');
  });

  it('throws Hebrew chat request errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 500)));

    await expect(sendChatMessage('שלום')).rejects.toThrow('500');
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
