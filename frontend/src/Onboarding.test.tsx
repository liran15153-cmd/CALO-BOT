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

    fireEvent.click(screen.getByRole('button', { name: /Onboarding/i }));
    fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'Lior' } });
    fireEvent.change(screen.getByLabelText(/Main goal/i), { target: { value: 'build_muscle' } });
    fireEvent.change(screen.getByLabelText(/Experience/i), { target: { value: 'beginner' } });
    fireEvent.change(screen.getByLabelText(/Training location/i), { target: { value: 'gym' } });
    fireEvent.change(screen.getByLabelText(/Workout days per week/i), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText(/Session length/i), { target: { value: '45' } });
    fireEvent.click(screen.getByLabelText(/general fitness and nutrition guidance/i));
    fireEvent.click(screen.getByRole('button', { name: /Save profile/i }));

    await waitFor(() => {
      expect(screen.getByText(/Profile saved/i)).toBeInTheDocument();
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
