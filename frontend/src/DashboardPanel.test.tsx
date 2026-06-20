import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Dashboard UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/dashboard')) {
          return jsonResponse({
            current_goal: 'build_muscle',
            current_workout_plan: { name: '3-Day Build Muscle Plan' },
            completed_workouts_this_week: 2,
            meals_logged_this_week: 4,
            estimated_nutrition_range: [1200, 1800],
            recent_coach_notes: ['User prefers short workouts'],
            current_streak: 2,
            missed_workouts: 1,
            next_recommended_action: 'בצע את האימון המתוכנן הבא.'
          });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it('renders live dashboard metrics from the API', async () => {
    render(<App />);

    expect(await screen.findByText(/בניית שריר/i)).toBeInTheDocument();
    expect(screen.getByText(/3-Day Build Muscle Plan/i)).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText(/בצע את האימון המתוכנן הבא/i)).toBeInTheDocument();
    expect(screen.getByText(/פעולה הבאה/i)).toBeInTheDocument();
  });

  it('does not render a fake nutrition range when the API has no estimate', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
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
            estimated_nutrition_range: [null, null],
            recent_coach_notes: [],
            current_streak: 0,
            missed_workouts: 0,
            next_recommended_action: 'סיים אונבורדינג.'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    expect(await screen.findByText(/אין עדיין הערכות ארוחה/i)).toBeInTheDocument();
    expect(screen.queryByText(/null-null/i)).not.toBeInTheDocument();
  });

  it('does not leak unknown internal goal identifiers to the dashboard', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/dashboard')) {
          return jsonResponse({
            current_goal: 'custom_goal_code',
            current_workout_plan: null,
            completed_workouts_this_week: 0,
            meals_logged_this_week: 0,
            estimated_nutrition_range: null,
            recent_coach_notes: [],
            current_streak: 0,
            missed_workouts: 0,
            next_recommended_action: 'סיים אונבורדינג.'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    expect(await screen.findByText(/מטרה לא מוכרת/i)).toBeInTheDocument();
    expect(screen.queryByText(/custom_goal_code/i)).not.toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
