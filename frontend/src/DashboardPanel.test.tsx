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
        if (url.endsWith('/api/summaries/weekly/current')) {
          return jsonResponse({
            summary: 'סיכום שבועי: הושלמו 2 אימונים, אימון אחד פוספס, תועדו 4 ארוחות.',
            metrics: {
              workouts_completed: 2,
              missed_workouts: 1,
              consistency_percentage: 67,
              meals_logged: 4
            },
            next_action: 'לבצע את האימון הבא בגרסה שמרנית ולתעד ארוחה אחת עם חלבון.',
            week_start: '2026-06-15',
            week_end: '2026-06-21',
            persisted: false
          });
        }
        if (url.endsWith('/api/dashboard')) {
          return jsonResponse({
            current_goal: 'build_muscle',
            current_workout_plan: { name: '3-Day Build Muscle Plan' },
            next_workout: {
              id: 101,
              name: 'יום 2 גוף מלא',
              plan_id: 1,
              plan_name: '3-Day Build Muscle Plan',
              load_signal: 'adherence_risk',
              next_adjustment: 'לבצע גרסת מינימום במקום להשלים הכל.'
            },
            completed_workouts_this_week: 2,
            meals_logged_this_week: 4,
            meals_logged_today: 1,
            estimated_nutrition_range: [1200, 1800],
            estimated_protein_range_today: [35, 55],
            nutrition_action: 'יש ארוחה מתועדת היום. לשמור על תיעוד פשוט.',
            recent_coach_notes: ['User prefers short workouts'],
            current_streak: 1,
            missed_workouts: 1,
            next_recommended_action: 'לבצע את האימון המתוכנן הבא.'
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
    expect(screen.getByText('יום אחד')).toBeInTheDocument();
    expect(screen.getByText('טווח שבועי משוער')).toBeInTheDocument();
    expect(screen.getByText('פספוסים')).toBeInTheDocument();
    expect(screen.getByText('אימון אחד שפוספס')).toBeInTheDocument();
    expect(screen.queryByText(/1 ימים/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/1 אימונים/i)).not.toBeInTheDocument();
    expect(screen.getByText(/לבצע את האימון המתוכנן הבא/i)).toBeInTheDocument();
    expect(screen.getByText(/פעולה הבאה/i)).toBeInTheDocument();
    expect(screen.getByText(/יום 2 גוף מלא/i)).toBeInTheDocument();
    expect(screen.getByText(/התאמה שמרנית/i)).toBeInTheDocument();
    expect(screen.getByText(/תזונה היום/i)).toBeInTheDocument();
    expect(screen.getByText(/35-55 גרם חלבון/i)).toBeInTheDocument();
    expect(screen.getByText(/יש ארוחה מתועדת היום/i)).toBeInTheDocument();
    expect(screen.queryByText(/adherence_risk/i)).not.toBeInTheDocument();
    expect(await screen.findByText(/סקירה שבועית/i)).toBeInTheDocument();
    expect(screen.getByText(/סיכום שבועי: הושלמו 2 אימונים/i)).toBeInTheDocument();
    expect(screen.getByText(/67% עקביות/i)).toBeInTheDocument();
    expect(screen.getByText(/לבצע את האימון הבא בגרסה שמרנית/i)).toBeInTheDocument();
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
            next_workout: null,
            completed_workouts_this_week: 0,
            meals_logged_this_week: 0,
            meals_logged_today: 0,
            estimated_nutrition_range: [null, null],
            estimated_protein_range_today: null,
            nutrition_action: 'לתעד ארוחה אחת היום עם טווח משוער.',
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
            next_workout: null,
            completed_workouts_this_week: 0,
            meals_logged_this_week: 0,
            meals_logged_today: 0,
            estimated_nutrition_range: null,
            estimated_protein_range_today: null,
            nutrition_action: 'לתעד ארוחה אחת היום עם טווח משוער.',
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
