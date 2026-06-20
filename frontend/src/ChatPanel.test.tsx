import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

    fireEvent.click(screen.getByRole('button', { name: /צ'אט/i }));

    expect(screen.getByLabelText(/הודעה למאמן/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /שליחה/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /צ'אט חדש/i })).toBeInTheDocument();
  });

  it('does not create an empty chat session just by opening chat', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/health')) {
        return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
      }
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /צ'אט/i }));

    await waitFor(() => expect(screen.getByLabelText(/הודעה למאמן/i)).toBeInTheDocument());
    const urls = fetchMock.mock.calls.map(([input]) => String(input));
    expect(urls.some((url) => url.endsWith('/api/chat/sessions'))).toBe(false);
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
          response: 'ספק הבינה המלאכותית לא מוגדר.',
          safety_flagged: false,
          provider_status: 'not_configured'
        });
      }
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /צ'אט/i }));
    fireEvent.change(screen.getByLabelText(/הודעה למאמן/i), { target: { value: 'Build me a plan' } });
    fireEvent.click(screen.getByRole('button', { name: /שליחה/i }));

    expect(await screen.findByText(/ספק הבינה המלאכותית לא מוגדר/i)).toBeInTheDocument();
    expect(screen.queryByText(/not_configured/i)).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({
        method: 'POST'
      })
    );
  });

  it('shows a Hebrew-only network error when the coach request fails', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/health')) {
        return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
      }
      if (url.endsWith('/api/chat') && init?.method === 'POST') {
        return { ok: false, status: 500, json: async () => ({}) } as Response;
      }
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /צ'אט/i }));
    fireEvent.change(screen.getByLabelText(/הודעה למאמן/i), { target: { value: 'שלום' } });
    fireEvent.click(screen.getByRole('button', { name: /שליחה/i }));

    expect(await screen.findByText(/לא הצלחתי להגיע לשרת המאמן/i)).toBeInTheDocument();
    expect(screen.queryByText(/API/i)).not.toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: async () => body
  } as Response;
}
