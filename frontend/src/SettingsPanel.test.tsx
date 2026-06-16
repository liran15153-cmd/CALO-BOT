import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Settings UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/dashboard')) {
          return jsonResponse({
            current_goal: null,
            current_workout_plan: null,
            completed_workouts_this_week: 0,
            meals_logged_this_week: 0,
            estimated_nutrition_range: null,
            recent_coach_notes: [],
            current_streak: 0,
            missed_workouts: 0,
            next_recommended_action: 'Complete onboarding.'
          });
        }
        if (url.endsWith('/api/settings')) {
          return jsonResponse({
            ai_provider: 'not_configured',
            model: 'claude-haiku-4-5',
            database: 'configured',
            api_key_present: false,
            disclaimer: 'This is not medical advice.'
          });
        }
        if (url.endsWith('/api/usage')) {
          return jsonResponse({
            usage_date: '2026-06-15',
            chat_requests_count: 1,
            image_analysis_count: 0,
            summary_requests_count: 1,
            estimated_tokens_in: 12,
            estimated_tokens_out: 4
          });
        }
        if (url.endsWith('/api/settings/export')) {
          return jsonResponse({ profile: null, meals: [] });
        }
        if (url.endsWith('/api/settings/reset') && init?.method === 'POST') {
          return jsonResponse({ deleted_records: 3, message: 'Local coaching data reset.' });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it('shows provider status without exposing an API key and supports export/reset actions', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Settings/i }));

    expect((await screen.findAllByText(/not_configured/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/sk-/i)).not.toBeInTheDocument();
    expect(screen.getByText(/not medical advice/i)).toBeInTheDocument();
    expect(await screen.findByText(/Chat requests/i)).toBeInTheDocument();
    expect(screen.getByText(/Summaries/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Export/i }));
    expect(await screen.findByText(/Export ready/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Reset local data/i }));
    expect(await screen.findByText(/3 records deleted/i)).toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
