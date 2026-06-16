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
            next_recommended_action: 'Complete the next planned workout.'
          });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it('renders live dashboard metrics from the API', async () => {
    render(<App />);

    expect(await screen.findByText(/build_muscle/i)).toBeInTheDocument();
    expect(screen.getByText(/3-Day Build Muscle Plan/i)).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText(/Complete the next planned workout/i)).toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}

