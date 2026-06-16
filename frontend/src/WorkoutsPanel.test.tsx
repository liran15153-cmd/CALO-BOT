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
        if (url.endsWith('/api/workout-plans') && init?.method === 'POST') {
          return jsonResponse({
            id: 1,
            is_current: true,
            name: '3-Day Build Muscle Plan',
            goal: 'build_muscle',
            days_per_week: 3,
            equipment_needed: ['dumbbells'],
            days: [
              {
                name: 'Day 1 Full Body',
                warmup: ['5 minutes easy cardio'],
                difficulty: 'moderate',
                exercises: [{ name: 'Goblet squat', sets: '3', reps_or_duration: '8-12 reps', rest: '90 sec' }]
              }
            ],
            progression_rule: 'Increase reps first.',
            recovery_note: 'Rest if sore.'
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

    fireEvent.click(screen.getByRole('button', { name: /Workouts/i }));
    fireEvent.change(screen.getByLabelText(/Plan request/i), { target: { value: 'Build me a 3-day plan' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate plan/i }));

    expect(await screen.findByText(/3-Day Build Muscle Plan/i)).toBeInTheDocument();
    expect(screen.getByText(/Goblet squat/i)).toBeInTheDocument();
  });

  it('logs a workout from natural language text', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Workouts/i }));
    fireEvent.change(screen.getByLabelText(/Workout log/i), {
      target: { value: 'I did 3 sets of bench press 10, 8, 7 with 50kg' }
    });
    fireEvent.click(screen.getByRole('button', { name: /Save workout log/i }));

    expect(await screen.findByText(/completed/i)).toBeInTheDocument();
    expect(screen.getByText(/bench press/i)).toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
