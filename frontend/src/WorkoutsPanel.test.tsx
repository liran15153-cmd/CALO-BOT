import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
        if (url.endsWith('/api/workouts/next')) {
          return jsonResponse({}, 404);
        }
        if (url.endsWith('/api/workout-logs/recent')) {
          return jsonResponse([
            {
              id: 22,
              workout_id: 101,
              logged_on: '2026-06-20',
              status: 'partial',
              exercise_results: [
                {
                  exercise_id: 201,
                  exercise_name: 'Goblet squat',
                  status: 'completed',
                  sets: [{ set_index: 1, reps: 10, weight: '20kg', completed: true }]
                }
              ],
              rpe: 9,
              notes: 'קוצר בזמן',
              pain_flag: false,
              parse_confidence: 'high'
            }
          ]);
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

  it('still displays the current plan when the next workout request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse(currentPlanFixture());
        }
        if (url.endsWith('/api/workouts/next')) {
          return jsonResponse({}, 500);
        }
        if (url.endsWith('/api/workout-logs/recent')) {
          return jsonResponse([]);
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));

    expect(await screen.findByText(/Current strength plan/i)).toBeInTheDocument();
    expect(screen.getByText(/Goblet squat/i)).toBeInTheDocument();
  });

  it('uses natural Hebrew singular wording for one workout day and one set', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse({
            id: 11,
            is_current: true,
            name: 'אימון קצר שמור',
            goal: 'maintain_consistency',
            plan_type: 'single_session',
            days_per_week: 1,
            session_length_minutes: 30,
            equipment_needed: ['bodyweight'],
            days: [
              {
                name: 'אימון קצר',
                estimated_duration_minutes: 30,
                warmup: ['5 דקות הליכה קלה'],
                difficulty: 'easy',
                exercises: [{ name: 'סקוואט למשקל גוף', sets: '1', reps_or_duration: '8-10 חזרות', rest: '60 שניות' }]
              }
            ],
            progression_rule: 'להוסיף חזרות רק כשזה מרגיש יציב.',
            recovery_note: 'לעצור אם מופיע כאב חד.'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));

    expect(await screen.findByText(/אימון קצר שמור/i)).toBeInTheDocument();
    expect(screen.getByText('אימון יחיד')).toBeInTheDocument();
    expect(screen.getByText('30 דקות')).toBeInTheDocument();
    expect(screen.getByText('יום אחד בשבוע')).toBeInTheDocument();
    expect(screen.getByText('סט אחד')).toBeInTheDocument();
    expect(screen.queryByText(/1 ימים/)).not.toBeInTheDocument();
    expect(screen.queryByText(/1 סטים/)).not.toBeInTheDocument();
  });

  it('logs a workout from natural language text', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));
    fireEvent.change(screen.getByLabelText(/תיעוד אימון/i), {
      target: { value: 'I did 3 sets of bench press 10, 8, 7 with 50kg' }
    });
    fireEvent.click(screen.getByRole('button', { name: /שמירת תיעוד אימון/i }));

    expect(await screen.findAllByText(/הושלם/i)).not.toHaveLength(0);
    expect(screen.getAllByText(/bench press/i)).not.toHaveLength(0);
  });

  it('loads persisted recent workout logs', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));

    expect(await screen.findByText(/תיעודים אחרונים/i)).toBeInTheDocument();
    expect(screen.getByText(/חלקי/i)).toBeInTheDocument();
    expect(screen.getByText(/RPE 9/i)).toBeInTheDocument();
    expect(screen.getByText(/קוצר בזמן/i)).toBeInTheDocument();
    expect(screen.getByText(/Goblet squat 10 20kg/i)).toBeInTheDocument();
  });

  it('submits a structured workout log from the next workout form', async () => {
    const logPayloads: unknown[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse(currentPlanFixture());
        }
        if (url.endsWith('/api/workouts/next')) {
          return jsonResponse(nextWorkoutFixture());
        }
        if (url.endsWith('/api/workout-logs') && init?.method === 'POST') {
          logPayloads.push(JSON.parse(String(init.body)));
          return jsonResponse({
            id: 12,
            workout_id: 101,
            logged_on: '2026-06-20',
            status: 'partial',
            exercise_results: [
              {
                exercise_id: 201,
                exercise_name: 'Goblet squat',
                status: 'completed',
                sets: [
                  { set_index: 1, reps: 12, weight: '20kg', completed: true },
                  { set_index: 2, reps: 10, weight: '20kg', completed: true }
                ],
                rpe: 8,
                rir: 2
              }
            ],
            rpe: 8,
            pain_flag: false,
            parse_confidence: 'high',
            adaptation: {
              load_signal: 'adherence_risk',
              next_adjustment: 'לבצע גרסת מינימום באימון הבא.',
              exercise_adjustments: []
            }
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));
    expect(await screen.findAllByText(/Next workout A/i)).not.toHaveLength(0);

    fireEvent.click(screen.getByLabelText(/חלקי/));
    fireEvent.change(screen.getByLabelText(/חזרות לפי סט.*Goblet squat/i), { target: { value: '12,10' } });
    fireEvent.change(screen.getByLabelText(/משקל.*Goblet squat/i), { target: { value: '20kg' } });
    fireEvent.change(screen.getByLabelText(/RPE כללי/i), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText(/RIR כללי/i), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText(/הערות כלליות/i), { target: { value: 'קיצרתי בגלל זמן' } });
    fireEvent.click(screen.getByRole('button', { name: /שמירת ביצוע מובנה/i }));

    await waitFor(() => expect(logPayloads).toHaveLength(1));
    expect(logPayloads[0]).toMatchObject({
      workout_id: 101,
      status: 'partial',
      rpe: 8,
      rir: 2,
      pain_flag: false,
      notes: 'קיצרתי בגלל זמן',
      exercises: [
        {
          exercise_id: 201,
          exercise_name: 'Goblet squat',
          status: 'completed',
          sets: [
            { set_index: 1, reps: 12, weight: '20kg', completed: true },
            { set_index: 2, reps: 10, weight: '20kg', completed: true }
          ],
          rpe: 8,
          rir: 2
        }
      ]
    });
    expect(await screen.findByText(/גרסת מינימום/i)).toBeInTheDocument();
  });

  it('renders the adapted execution plan and logs against source exercise ids', async () => {
    const logPayloads: unknown[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse(currentPlanFixture());
        }
        if (url.endsWith('/api/workouts/next')) {
          return jsonResponse(adaptedNextWorkoutFixture());
        }
        if (url.endsWith('/api/workout-logs') && init?.method === 'POST') {
          logPayloads.push(JSON.parse(String(init.body)));
          return jsonResponse({
            id: 14,
            workout_id: 101,
            logged_on: '2026-06-20',
            status: 'completed',
            exercise_results: [],
            pain_flag: false,
            parse_confidence: 'high'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));

    expect(await screen.findByText(/גרסת ביצוע להיום/i)).toBeInTheDocument();
    expect(screen.getByText(/2 סטים/i)).toBeInTheDocument();
    expect(screen.getByText(/לבצע גרסת מינימום נקייה/i)).toBeInTheDocument();
    expect(screen.queryByText(/adherence_risk/i)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/חזרות לפי סט.*Goblet squat/i), { target: { value: '10,8' } });
    fireEvent.click(screen.getByRole('button', { name: /שמירת ביצוע מובנה/i }));

    await waitFor(() => expect(logPayloads).toHaveLength(1));
    expect(logPayloads[0]).toMatchObject({
      workout_id: 101,
      exercises: [
        {
          exercise_id: 201,
          exercise_name: 'Goblet squat'
        }
      ]
    });
  });

  it('validates structured workout numbers before sending payload', async () => {
    const logPayloads: unknown[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/workout-plans/current')) {
          return jsonResponse(currentPlanFixture());
        }
        if (url.endsWith('/api/workouts/next')) {
          return jsonResponse(nextWorkoutFixture());
        }
        if (url.endsWith('/api/workout-logs') && init?.method === 'POST') {
          logPayloads.push(JSON.parse(String(init.body)));
          return jsonResponse({});
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /אימונים/i }));
    expect(await screen.findAllByText(/Next workout A/i)).not.toHaveLength(0);

    fireEvent.change(screen.getByLabelText(/חזרות לפי סט.*Goblet squat/i), { target: { value: '12 reps,10' } });
    fireEvent.change(screen.getByLabelText(/RPE כללי/i), { target: { value: '11' } });
    fireEvent.click(screen.getByRole('button', { name: /שמירת ביצוע מובנה/i }));

    expect(await screen.findByText(/RPE כללי חייב להיות בין 1 ל-10/i)).toBeInTheDocument();
    expect(logPayloads).toHaveLength(0);
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

    expect(await screen.findAllByText(/סטטוס לא מוכר/i)).not.toHaveLength(0);
    expect(screen.getAllByText(/רמת ביטחון: לא ידועה|לא ידועה/i)).not.toHaveLength(0);
    expect(screen.queryByText(/internal_status_code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/internal_confidence_code/i)).not.toBeInTheDocument();
  });
});

function jsonResponse(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

function currentPlanFixture() {
  return {
    id: 1,
    is_current: true,
    name: 'Current strength plan',
    goal: 'build_muscle',
    days_per_week: 2,
    equipment_needed: ['dumbbells'],
    days: [
      {
        workout_id: 101,
        name: 'Next workout A',
        warmup: ['5 minutes easy cardio'],
        difficulty: 'moderate',
        exercises: [
          {
            exercise_id: 201,
            name: 'Goblet squat',
            sets: '3',
            reps_or_duration: '8-12 reps',
            rest: '90 sec'
          }
        ]
      }
    ],
    progression_rule: 'Add one rep first.',
    recovery_note: 'Keep one easy day between sessions.'
  };
}

function nextWorkoutFixture() {
  return {
    id: 101,
    plan_id: 1,
    name: 'Next workout A',
    scheduled_day: 'Day 1',
    difficulty: 'moderate',
    warmup: ['5 minutes easy cardio'],
    exercises: [
      {
        exercise_id: 201,
        name: 'Goblet squat',
        sets: '3',
        reps_or_duration: '8-12 reps',
        rest: '90 sec',
        notes: 'Controlled tempo'
      },
      {
        exercise_id: 202,
        name: 'Dumbbell row',
        sets: '3',
        reps_or_duration: '10-12 reps',
        rest: '75 sec',
        notes: 'Pause at the top'
      }
    ],
    adaptation: {
      load_signal: 'maintain',
      next_adjustment: 'לשמור על התוכנית הנוכחית.',
      exercise_adjustments: []
    }
  };
}

function adaptedNextWorkoutFixture() {
  return {
    ...nextWorkoutFixture(),
    adaptation: {
      load_signal: 'adherence_risk',
      next_adjustment: 'לבצע גרסת מינימום במקום להשלים הכל.',
      exercise_adjustments: []
    },
    execution_plan: {
      source: 'derived_from_base_workout',
      base_workout_id: 101,
      workout_name: 'Next workout A',
      load_signal: 'adherence_risk',
      summary: 'לבצע גרסת מינימום: פחות תרגילים, פחות סטים, ולסיים נקי.',
      adjusted_exercises: [
        {
          exercise_id: 201,
          source_exercise_id: 201,
          name: 'Goblet squat',
          sets: '2',
          reps_or_duration: '8-12 reps',
          rest: '90 sec',
          notes: 'Controlled tempo',
          alternatives: ['Box squat'],
          adjustment: 'minimum_version',
          reason: 'missed_or_partial',
          execution_note: 'לבצע גרסת מינימום נקייה.'
        }
      ]
    }
  };
}
