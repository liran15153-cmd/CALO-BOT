import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchHealth, sendChatMessage } from './api';

describe('API client errors', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('throws Hebrew health check errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 503)));

    await expect(fetchHealth()).rejects.toThrow('בדיקת תקינות נכשלה: 503');
  });

  it('throws Hebrew chat request errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({}, 500)));

    await expect(sendChatMessage('שלום')).rejects.toThrow("בקשת הצ'אט נכשלה: 500");
  });
});

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body
  } as Response;
}
