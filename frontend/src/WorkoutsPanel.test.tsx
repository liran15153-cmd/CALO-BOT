import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Workout plan UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse({}, 404);
        }
        if (url.endsWith('/api/workout-plans') && init?.method === 'POST') {
          return jsonResponse({
            id: 1,
            is_current: true,
            name: 'תוכנית 3 ימים לבניית שריר',
            goal: 'build_muscle',
            days_per_week: 3,
            equipment_needed: ['dumbbells'],
            days: [
              {
                name: 'יום 1 גוף מלא',
                warmup: ['5 דקות אירובי קל'],
                difficulty: 'moderate',
                exercises: [{ name: 'סקוואט גביע', sets: '3', reps_or_duration: '8-12 חזרות', rest: '90 שניות' }]
              }
            ],
            progression_rule: 'הוסף חזרות קודם.',
            recovery_note: 'נוח אם הכאב השרירי גבוה.'
          });
        }
        if (url.endsWith('/api/workout-logs') && init?.method === 'POST') {
          return jsonResponse({
            id: 2,
            logged_on: '2026-06-15',
            status: 'completed',
            exercise_results: [{ exercise: 'bench press', sets: 3, reps: [10, 8, 7], weight: '50kg' }],
            pain_flag: false,
            parse_confidence: 'medium'
          });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it('generates and displays a structured workout plan', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));
    fireEvent.change(screen.getByLabelText(/בקשת תוכנית/i), { target: { value: 'Build me a 3-day plan' } });
    fireEvent.click(screen.getByRole('button', { name: /יצירת תוכנית/i }));

    expect(await screen.findByText(/תוכנית 3 ימים לבניית שריר/i)).toBeInTheDocument();
    expect(screen.getByText(/סקוואט גביע/i)).toBeInTheDocument();
    expect(screen.getByText(/ימים בשבוע/i)).toBeInTheDocument();
  });

  it('loads and displays the current persisted workout plan', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse({
            id: 9,
            is_current: true,
            name: 'תוכנית כוח שמורה',
            goal: 'improve_strength',
            days_per_week: 2,
            equipment_needed: ['resistance bands'],
            days: [
              {
                name: 'יום שלישי גוף מלא',
                warmup: ['5 דקות אירובי קל'],
                difficulty: 'moderate',
                exercises: [{ name: 'חתירה עם גומייה', sets: '3', reps_or_duration: '10-12 חזרות', rest: '75 שניות' }]
              }
            ],
            progression_rule: 'הוסף חזרות קודם.',
            recovery_note: 'כבד את המגבלה שתועדה בפרופיל.'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));

    expect(await screen.findByText(/תוכנית כוח שמורה/i)).toBeInTheDocument();
    expect(screen.getByText(/חתירה עם גומייה/i)).toBeInTheDocument();
  });

  it('logs a workout from natural language text', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));
    fireEvent.change(screen.getByLabelText(/תיעוד אימון/i), {
      target: { value: 'I did 3 sets of bench press 10, 8, 7 with 50kg' }
    });
    fireEvent.click(screen.getByRole('button', { name: /שמירת תיעוד אימון/i }));

    expect(await screen.findByText(/הושלם/i)).toBeInTheDocument();
    expect(screen.getByText(/bench press/i)).toBeInTheDocument();
  });

  it('does not leak unknown internal workout status identifiers', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse({}, 404);
        }
        if (url.endsWith('/api/workout-logs') && init?.method === 'POST') {
          return jsonResponse({
            id: 2,
            logged_on: '2026-06-15',
            status: 'internal_status_code',
            exercise_results: [],
            pain_flag: false,
            parse_confidence: 'internal_confidence_code'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));
    fireEvent.change(screen.getByLabelText(/תיעוד אימון/i), { target: { value: 'תיעדתי אימון קצר' } });
    fireEvent.click(screen.getByRole('button', { name: /שמירת תיעוד אימון/i }));

    expect(await screen.findByText(/סטטוס לא מוכר/i)).toBeInTheDocument();
    expect(screen.getByText(/רמת ביטחון: לא ידועה/i)).toBeInTheDocument();
    expect(screen.queryByText(/internal_status_code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/internal_confidence_code/i)).not.toBeInTheDocument();
  });
});

function jsonResponse(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}
