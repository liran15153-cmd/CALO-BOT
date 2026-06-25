import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Onboarding UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/onboarding') && !init?.method) {
          return jsonResponse({ completed: false, profile: null });
        }
        if (url.endsWith('/api/onboarding') && init?.method === 'POST') {
          return jsonResponse({
            completed: true,
            profile: { name: 'Lior', main_goal: 'build_muscle' }
          });
        }
        throw new Error(`unexpected fetch ${url}`);
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('saves the required onboarding profile fields', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /פרופיל/i }));
    expect(screen.getByRole('option', { name: /שיפור מוביליטי/i })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/שם/i), { target: { value: 'Lior' } });
    fireEvent.change(screen.getByLabelText(/מטרה מרכזית/i), { target: { value: 'build_muscle' } });
    fireEvent.change(screen.getByLabelText(/רמת ניסיון/i), { target: { value: 'beginner' } });
    fireEvent.change(screen.getByLabelText(/מיקום אימון/i), { target: { value: 'gym' } });
    fireEvent.change(screen.getByLabelText(/ימי אימון בשבוע/i), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText(/משך אימון/i), { target: { value: '45' } });
    fireEvent.click(screen.getByLabelText(/הכוונת כושר ותזונה כללית/i));
    fireEvent.click(screen.getByRole('button', { name: /שמירת פרופיל/i }));

    await waitFor(() => {
      expect(screen.getByText(/הפרופיל מוכן/i)).toBeInTheDocument();
    });

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/onboarding',
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
