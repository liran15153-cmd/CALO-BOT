import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Chat UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders a chat workspace with message composer controls', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Chat/i }));

    expect(screen.getByLabelText(/Message the coach/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /New chat/i })).toBeInTheDocument();
  });

  it('sends a message and renders the coach response', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/health')) {
        return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
      }
      if (url.endsWith('/api/chat') && init?.method === 'POST') {
        return jsonResponse({
          session_id: 1,
          user_message_id: 1,
          coach_message_id: 2,
          response: 'AI provider is not configured.',
          safety_flagged: false,
          provider_status: 'not_configured'
        });
      }
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Chat/i }));
    fireEvent.change(screen.getByLabelText(/Message the coach/i), { target: { value: 'Build me a plan' } });
    fireEvent.click(screen.getByRole('button', { name: /Send/i }));

    expect(await screen.findByText(/AI provider is not configured/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({
        method: 'POST'
      })
    );
  });
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: async () => body
  } as Response;
}
