import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('App shell', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              status: 'ok',
              service: 'calo-coach',
              database: 'configured',
              ai_provider: 'not_configured',
              no_api_key_mode: true
            })
          } as Response;
        }
        if (url.endsWith('/api/dashboard')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              current_goal: 'improve_fitness',
              current_workout_plan: { name: 'Base plan' },
              next_workout: {
                id: 1,
                name: 'Upper',
                load_signal: 'maintain',
                scheduled_day: 'יום ראשון',
                warmup: [],
                exercises: []
              },
              completed_workouts_this_week: 0,
              meals_logged_this_week: 0,
              meals_logged_today: 0,
              estimated_nutrition_range: [null, null],
              estimated_protein_range_today: [null, null],
              current_streak: 0,
              missed_workouts: 0,
              next_recommended_action: 'Start with one short workout.',
              nutrition_action: 'Add one balanced meal first.',
              recent_coach_notes: []
            })
          } as Response;
        }
        if (url.endsWith('/api/summaries/weekly/current')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              summary: null,
              metrics: {},
              next_action: null,
              week_start: null,
              week_end: null,
              persisted: false
            })
          } as Response;
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({})
        } as Response;
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the local coach workspace and primary navigation', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /CALO Coach/i })).toBeInTheDocument();
    expect(screen.getByRole('main')).toHaveAttribute('dir', 'rtl');
    expect(screen.getByRole('main')).toHaveAttribute('lang', 'he');
    expect(screen.getAllByRole('button')).toHaveLength(6);
  });

  it('shows local-only provider mode when API key is missing', async () => {
    render(<App />);

    expect(await screen.findByText(/AI provider is not configured/i)).toBeInTheDocument();
    expect(await screen.findByText(/local-only mode/i)).toBeInTheDocument();
  });
});
