import { Dumbbell } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import {
  fetchCurrentPendingAction,
  fetchCurrentWorkoutPlan,
  fetchNextWorkout,
  fetchRecentWorkoutLogs,
  generateWorkoutPlan,
  resolvePendingAction,
  saveWorkoutLog,
  type ExecutionPlanExercise,
  type NextWorkout,
  type PendingAction,
  type WorkoutLog,
  type WorkoutLogInput,
  type WorkoutPlan
} from './api';
import { formatAdjustmentExplanation } from './formatters';

type WorkoutStatus = 'completed' | 'partial' | 'skipped' | 'modified';

type ExerciseFormState = {
  setsInput: string;
  weight: string;
  completed: boolean;
  rpe: string;
  rir: string;
  notes: string;
};

const STATUS_OPTIONS: Array<{ value: WorkoutStatus; label: string }> = [
  { value: 'completed', label: 'הושלם' },
  { value: 'partial', label: 'חלקי' },
  { value: 'skipped', label: 'פוספס' },
  { value: 'modified', label: 'שונה' }
];

export function WorkoutsPanel() {
  const [prompt, setPrompt] = useState('');
  const [logText, setLogText] = useState('');
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [pendingPlan, setPendingPlan] = useState<WorkoutPlan | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [nextWorkout, setNextWorkout] = useState<NextWorkout | null>(null);
  const [lastLog, setLastLog] = useState<WorkoutLog | null>(null);
  const [recentLogs, setRecentLogs] = useState<WorkoutLog[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [replacementStatus, setReplacementStatus] = useState<'idle' | 'saving' | 'error'>('idle');
  const [logStatus, setLogStatus] = useState<'idle' | 'saving' | 'error'>('idle');
  const [structuredLogStatus, setStructuredLogStatus] = useState<'idle' | 'saving' | 'error'>('idle');
  const [structuredLogError, setStructuredLogError] = useState<string | null>(null);
  const [nextWorkoutStatus, setNextWorkoutStatus] = useState<'idle' | 'loading' | 'error'>('loading');
  const [workoutStatus, setWorkoutStatus] = useState<WorkoutStatus>('completed');
  const [exerciseInputs, setExerciseInputs] = useState<Record<number, ExerciseFormState>>({});
  const [overallRpe, setOverallRpe] = useState('');
  const [overallRir, setOverallRir] = useState('');
  const [painFlag, setPainFlag] = useState(false);
  const [generalNotes, setGeneralNotes] = useState('');

  const applyNextWorkout = useCallback((value: NextWorkout | null) => {
    const normalized = normalizeNextWorkout(value);
    setNextWorkout(normalized);
    setExerciseInputs(normalized ? makeExerciseInputs(normalized) : {});
  }, []);

  const loadNextWorkout = useCallback(async () => {
    setNextWorkoutStatus('loading');
    try {
      applyNextWorkout(await fetchNextWorkout());
      setNextWorkoutStatus('idle');
    } catch {
      applyNextWorkout(null);
      setNextWorkoutStatus('error');
    }
  }, [applyNextWorkout]);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetchCurrentWorkoutPlan().catch(() => null),
      fetchCurrentPendingAction().catch(() => null)
    ])
      .then(([currentPlan, currentPendingAction]) => {
        if (!active) return;
        const candidatePlan = validCandidatePlan(currentPendingAction);
        if (candidatePlan) {
          setPlan((current) => current ?? candidatePlan);
          setPendingPlan((current) => current ?? candidatePlan);
          setPendingAction((current) => current ?? currentPendingAction);
        } else {
          setPlan((current) => current ?? currentPlan);
          setPendingPlan((current) => current ?? null);
          setPendingAction((current) => current ?? null);
        }
      });
    fetchNextWorkout()
      .then((next) => {
        if (!active) return;
        applyNextWorkout(next);
        setNextWorkoutStatus('idle');
      })
      .catch(() => {
        if (!active) return;
        applyNextWorkout(null);
        setNextWorkoutStatus('error');
      });
    fetchRecentWorkoutLogs()
      .then((logs) => {
        if (!active) return;
        setRecentLogs(Array.isArray(logs) ? logs : []);
      })
      .catch(() => {
        if (!active) return;
        setRecentLogs([]);
      });
    return () => {
      active = false;
    };
  }, [applyNextWorkout]);

  async function handleGenerate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) return;
    setStatus('loading');
    setReplacementStatus('idle');
    try {
      const nextPlan = await generateWorkoutPlan(trimmed);
      setPlan(nextPlan);
      setPendingPlan(nextPlan.pending_action && !nextPlan.is_current ? nextPlan : null);
      setPendingAction(nextPlan.pending_action && !nextPlan.is_current ? nextPlan.pending_action : null);
      if (nextPlan.is_current) {
        await loadNextWorkout();
      }
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  async function handleActivatePendingPlan() {
    if (!pendingAction) return;
    setReplacementStatus('saving');
    try {
      const result = await resolvePendingAction(pendingAction.id, 'confirm');
      setPlan(result.workout_plan);
      setPendingPlan(null);
      setPendingAction(null);
      await loadNextWorkout();
      setReplacementStatus('idle');
    } catch {
      setReplacementStatus('error');
    }
  }

  async function handleDiscardPendingPlan() {
    if (!pendingAction) return;
    setReplacementStatus('saving');
    try {
      const result = await resolvePendingAction(pendingAction.id, 'decline');
      setPlan(result.workout_plan ?? (await fetchCurrentWorkoutPlan()));
      setPendingPlan(null);
      setPendingAction(null);
      setReplacementStatus('idle');
    } catch {
      setReplacementStatus('error');
    }
  }

  async function handleStructuredLog(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!nextWorkout) return;
    setStructuredLogError(null);
    const validationError = validateStructuredLog(workoutStatus, exerciseInputs, overallRpe, overallRir, painFlag, generalNotes);
    if (validationError) {
      setStructuredLogError(validationError);
      return;
    }
    setStructuredLogStatus('saving');
    const payload: WorkoutLogInput = {
      workout_id: nextWorkout.id,
      status: workoutStatus,
      exercises:
        workoutStatus === 'skipped'
          ? []
          : executionExercisesFor(nextWorkout).flatMap((exercise) => {
              const exerciseId = executionExerciseId(exercise);
              if (exerciseId === null) return [];
              const input = exerciseInputs[exerciseId] ?? emptyExerciseInput();
              if (!hasExerciseInput(input)) return [];
              const exerciseRpe = integerOrNull(input.rpe) ?? integerOrNull(overallRpe);
              const exerciseRir = integerOrNull(input.rir) ?? integerOrNull(overallRir);
              return [{
                exercise_id: exerciseId,
                exercise_name: exercise.name,
                status: exerciseStatus(workoutStatus, input),
                sets: parseSetLogs(input.setsInput, input.weight, input.completed),
                rpe: exerciseRpe,
                rir: exerciseRir,
                notes: input.notes.trim() || null
              }];
            }),
      rpe: integerOrNull(overallRpe),
      rir: integerOrNull(overallRir),
      pain_flag: painFlag,
      notes: generalNotes.trim() || null
    };
    try {
      const saved = await saveWorkoutLog(payload);
      setLastLog(saved);
      setRecentLogs((current) => [saved, ...current.filter((log) => log.id !== saved.id)].slice(0, 10));
      setWorkoutStatus('completed');
      setOverallRpe('');
      setOverallRir('');
      setPainFlag(false);
      setGeneralNotes('');
      await loadNextWorkout();
      setStructuredLogStatus('idle');
    } catch {
      setStructuredLogStatus('error');
    }
  }

  async function handleLog(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = logText.trim();
    if (!trimmed) return;
    setLogStatus('saving');
    try {
      const saved = await saveWorkoutLog(trimmed);
      setLastLog(saved);
      setRecentLogs((current) => [saved, ...current.filter((log) => log.id !== saved.id)].slice(0, 10));
      setLogText('');
      setLogStatus('idle');
      await loadNextWorkout();
    } catch {
      setLogStatus('error');
    }
  }

  function updateExerciseInput(exerciseId: number, patch: Partial<ExerciseFormState>) {
    setExerciseInputs((current) => ({
      ...current,
      [exerciseId]: {
        ...(current[exerciseId] ?? emptyExerciseInput()),
        ...patch
      }
    }));
  }

  return (
    <section className="panel workouts-panel">
      <div className="panel-heading">
        <h3>תוכנית אימון</h3>
        <p>צור תוכנית מובנית שאפשר לבדוק, לעדכן ולתעד מולה בהמשך.</p>
      </div>

      <section className="next-workout-section">
        <h4>האימון הבא</h4>
        {nextWorkout ? (
          <div className="next-workout-layout">
            <div className="plan-day next-workout-card">
              <div className="plan-summary">
                <h4>{nextWorkout.name}</h4>
                {nextWorkout.difficulty && <span>{formatDifficulty(nextWorkout.difficulty)}</span>}
              </div>
              {nextWorkout.warmup.length > 0 && <p>{nextWorkout.warmup.join(' / ')}</p>}
              {nextWorkout.execution_plan && (
                <div className="execution-plan-summary">
                  <strong>גרסת ביצוע להיום</strong>
                  <span>{nextWorkout.execution_plan.summary}</span>
                </div>
              )}
              <div className="exercise-grid">
                {executionExercisesFor(nextWorkout).map((exercise) => {
                  const explanation = formatAdjustmentExplanation(exercise.reason, exercise.name);
                  return (
                    <div className="exercise-row" key={executionExerciseId(exercise) ?? exercise.name}>
                      <strong>{exercise.name}</strong>
                      <span>{formatSetCount(exercise.sets)}</span>
                      <span>{exercise.reps_or_duration}</span>
                      <span>{exercise.rest}</span>
                      {exercise.execution_note && <small>{exercise.execution_note}</small>}
                      {explanation && <small className="adjustment-explanation">{explanation}</small>}
                    </div>
                  );
                })}
              </div>
              <p className="plan-note">{nextWorkout.execution_plan?.summary ?? nextWorkout.adaptation.next_adjustment}</p>
            </div>

            <form className="structured-log-form" onSubmit={handleStructuredLog}>
              <div className="status-options" role="radiogroup" aria-label="סטטוס ביצוע">
                {STATUS_OPTIONS.map((option) => (
                  <label key={option.value}>
                    <input
                      type="radio"
                      name="workout-status"
                      value={option.value}
                      checked={workoutStatus === option.value}
                      onChange={() => setWorkoutStatus(option.value)}
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>

              {workoutStatus !== 'skipped' &&
                executionExercisesFor(nextWorkout).map((exercise) => {
                  const exerciseId = executionExerciseId(exercise);
                  if (exerciseId === null) return null;
                  const input = exerciseInputs[exerciseId] ?? emptyExerciseInput();
                  return (
                    <fieldset className="exercise-log-fields" key={exerciseId}>
                      <legend>{exercise.name}</legend>
                      <label>
                        חזרות לפי סט - {exercise.name}
                        <input
                          value={input.setsInput}
                          onChange={(event) => updateExerciseInput(exerciseId, { setsInput: event.target.value })}
                          placeholder="12,10,8"
                        />
                      </label>
                      <label>
                        משקל - {exercise.name}
                        <input
                          value={input.weight}
                          onChange={(event) => updateExerciseInput(exerciseId, { weight: event.target.value })}
                          placeholder='20kg או 20 ק"ג'
                        />
                      </label>
                      <label>
                        RPE - {exercise.name}
                        <input
                          inputMode="numeric"
                          value={input.rpe}
                          onChange={(event) => updateExerciseInput(exerciseId, { rpe: event.target.value })}
                          placeholder="8"
                        />
                      </label>
                      <label>
                        RIR - {exercise.name}
                        <input
                          inputMode="numeric"
                          value={input.rir}
                          onChange={(event) => updateExerciseInput(exerciseId, { rir: event.target.value })}
                          placeholder="2"
                        />
                      </label>
                      <label className="checkbox-row">
                        <input
                          type="checkbox"
                          checked={input.completed}
                          onChange={(event) => updateExerciseInput(exerciseId, { completed: event.target.checked })}
                        />
                        בוצע
                      </label>
                      <label className="notes-field">
                        הערה לתרגיל - {exercise.name}
                        <textarea
                          value={input.notes}
                          onChange={(event) => updateExerciseInput(exerciseId, { notes: event.target.value })}
                        />
                      </label>
                    </fieldset>
                  );
                })}

              <div className="structured-log-footer">
                <label>
                  RPE כללי
                  <input inputMode="numeric" value={overallRpe} onChange={(event) => setOverallRpe(event.target.value)} placeholder="8" />
                </label>
                <label>
                  RIR כללי
                  <input inputMode="numeric" value={overallRir} onChange={(event) => setOverallRir(event.target.value)} placeholder="2" />
                </label>
                <label className="checkbox-row">
                  <input type="checkbox" checked={painFlag} onChange={(event) => setPainFlag(event.target.checked)} />
                  היה כאב
                </label>
                <label className="notes-field">
                  הערות כלליות
                  <textarea value={generalNotes} onChange={(event) => setGeneralNotes(event.target.value)} />
                </label>
              </div>

              <button className="primary-button icon-button" type="submit" disabled={structuredLogStatus === 'saving'}>
                שמירת ביצוע מובנה
              </button>
              {structuredLogError && <p className="error-text">{structuredLogError}</p>}
              {structuredLogStatus === 'error' && <p className="error-text">לא הצלחתי לשמור את הביצוע המובנה.</p>}
            </form>
          </div>
        ) : (
          <p className={nextWorkoutStatus === 'error' ? 'error-text' : 'plan-note'}>
            {nextWorkoutStatus === 'loading'
              ? 'טוען את האימון הבא...'
              : nextWorkoutStatus === 'error'
                ? 'לא הצלחתי לטעון את האימון הבא. התיעוד יכול להישמר, אבל צריך לרענן לפני פעולה הבאה.'
                : 'אין עדיין אימון הבא. צור תוכנית אימון פעילה כדי להתחיל לתעד ביצוע מול תוכנית.'}
          </p>
        )}
      </section>

      <form className="composer" onSubmit={handleGenerate}>
        <label htmlFor="plan-request">בקשת תוכנית</label>
        <div className="composer-row">
          <textarea
            id="plan-request"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="צור תוכנית ל-3 ימים לפי הפרופיל והציוד הזמין שלי."
          />
          <button className="primary-button icon-button" type="submit" disabled={status === 'loading' || !prompt.trim()}>
            <Dumbbell size={17} aria-hidden="true" />
            יצירת תוכנית
          </button>
        </div>
      </form>

      {status === 'error' && <p className="error-text">לא הצלחתי ליצור תוכנית.</p>}

      {pendingPlan && (
        <div className="plan-replacement-panel" role="status">
          <div>
            <strong>זו תוכנית חדשה שלא פעילה עדיין.</strong>
            <p>התוכנית הקיימת נשארת פעילה עד שתבחר להחליף אותה. האימון הבא עדיין מגיע מהתוכנית הפעילה.</p>
          </div>
          <div className="plan-replacement-actions">
            <button className="primary-button icon-button" type="button" onClick={handleActivatePendingPlan} disabled={replacementStatus === 'saving'}>
              החלף לתוכנית החדשה
            </button>
            <button className="ghost-button" type="button" onClick={handleDiscardPendingPlan} disabled={replacementStatus === 'saving'}>
              השאר את הקיימת
            </button>
          </div>
          {replacementStatus === 'error' && <p className="error-text">לא הצלחתי לעדכן את בחירת התוכנית.</p>}
        </div>
      )}

      {plan && (
        <div className="plan-view">
          <div className="plan-summary">
            <h4>{plan.name}</h4>
            {formatPlanType(plan.plan_type) && <span>{formatPlanType(plan.plan_type)}</span>}
            {formatPlanDuration(plan) && <span>{formatPlanDuration(plan)}</span>}
            <span>{formatDaysPerWeek(plan.days_per_week)}</span>
            <span>{formatEquipment(plan.equipment_needed)}</span>
          </div>
          {plan.days.map((day) => (
            <article className="plan-day" key={day.name}>
              <h5>{day.name}</h5>
              <p>{day.warmup.join(' / ')}</p>
              <div className="exercise-grid">
                {day.exercises.map((exercise) => (
                  <div className="exercise-row" key={`${day.workout_id ?? day.name}-${exercise.exercise_id ?? exercise.name}`}>
                    <strong>{exercise.name}</strong>
                    <span>{formatSetCount(exercise.sets)}</span>
                    <span>{exercise.reps_or_duration}</span>
                    <span>{exercise.rest}</span>
                  </div>
                ))}
              </div>
            </article>
          ))}
          <p className="plan-note">{plan.progression_rule}</p>
        </div>
      )}

      <section className="inline-section">
        <h4>תיעוד חופשי</h4>
        <form className="composer" onSubmit={handleLog}>
          <label htmlFor="workout-log">תיעוד אימון</label>
          <div className="composer-row">
            <textarea
              id="workout-log"
              value={logText}
              onChange={(event) => setLogText(event.target.value)}
              placeholder='עשיתי 3 סטים של לחיצת חזה 10, 8, 7 חזרות עם 50 ק"ג.'
            />
            <button className="primary-button icon-button" type="submit" disabled={logStatus === 'saving' || !logText.trim()}>
              שמירת תיעוד אימון
            </button>
          </div>
        </form>
        {logStatus === 'error' && <p className="error-text">לא הצלחתי לשמור את תיעוד האימון.</p>}
        {lastLog && (
          <div className="log-result">
            <strong>{formatWorkoutStatus(lastLog.status)}</strong>
            <span>רמת ביטחון: {formatConfidence(lastLog.parse_confidence)}</span>
            {lastLog.adaptation?.next_adjustment && <span>{lastLog.adaptation.next_adjustment}</span>}
            {lastLog.pain_flag && <span className="error-text">דווח כאב</span>}
            {lastLog.exercise_results.map((result, index) => (
              <span key={`${formatLoggedExercise(result)}-${index}`}>{formatLoggedExercise(result)}</span>
            ))}
          </div>
        )}
        {recentLogs.length > 0 && (
          <div className="workout-log-history">
            <h4>תיעודים אחרונים</h4>
            <div className="workout-log-list">
              {recentLogs.map((log) => (
                <article className="workout-log-item" key={log.id}>
                  <div className="workout-log-heading">
                    <strong>{formatWorkoutStatus(log.status)}</strong>
                    <span>{formatLogDate(log.logged_on)}</span>
                  </div>
                  <div className="workout-log-meta">
                    {log.rpe ? <span>RPE {log.rpe}</span> : null}
                    {log.pain_flag ? <span className="error-text">דווח כאב</span> : null}
                    <span>{formatConfidence(log.parse_confidence)}</span>
                  </div>
                  {log.notes ? <p>{log.notes}</p> : null}
                  {log.exercise_results.length > 0 ? (
                    <div className="workout-log-exercises">
                      {log.exercise_results.slice(0, 3).map((result, index) => (
                        <span key={`${log.id}-${formatLoggedExercise(result)}-${index}`}>{formatLoggedExercise(result)}</span>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          </div>
        )}
      </section>
    </section>
  );
}

function emptyExerciseInput(): ExerciseFormState {
  return { setsInput: '', weight: '', completed: true, rpe: '', rir: '', notes: '' };
}

function makeExerciseInputs(workout: NextWorkout): Record<number, ExerciseFormState> {
  return Object.fromEntries(
    executionExercisesFor(workout).flatMap((exercise) => {
      const exerciseId = executionExerciseId(exercise);
      if (exerciseId === null) return [];
      return [
        [
          exerciseId,
          {
            setsInput: '',
            weight: '',
            completed: true,
            rpe: '',
            rir: '',
            notes: ''
          }
        ]
      ];
    })
  );
}

function normalizeNextWorkout(value: NextWorkout | null): NextWorkout | null {
  if (!value || typeof value.id !== 'number' || !Array.isArray(value.exercises)) {
    return null;
  }
  return {
    ...value,
    warmup: Array.isArray(value.warmup) ? value.warmup : [],
    execution_plan:
      value.execution_plan && Array.isArray(value.execution_plan.adjusted_exercises)
        ? {
            ...value.execution_plan,
            adjusted_exercises: value.execution_plan.adjusted_exercises
          }
        : null,
    adaptation: value.adaptation ?? {
      load_signal: 'maintain',
      next_adjustment: 'שמור על התוכנית הנוכחית.',
      exercise_adjustments: []
    }
  };
}

function validCandidatePlan(action: PendingAction | null): WorkoutPlan | null {
  if (!action || action.status !== 'pending' || !action.candidate_plan || action.candidate_plan.is_current) {
    return null;
  }
  return action.candidate_plan;
}

function executionExercisesFor(workout: NextWorkout): ExecutionPlanExercise[] {
  if (workout.execution_plan?.adjusted_exercises?.length) {
    return workout.execution_plan.adjusted_exercises;
  }
  return workout.exercises.map((exercise) => ({
    ...exercise,
    source_exercise_id: exercise.exercise_id
  }));
}

function executionExerciseId(exercise: ExecutionPlanExercise): number | null {
  if (typeof exercise.source_exercise_id === 'number') return exercise.source_exercise_id;
  if (typeof exercise.exercise_id === 'number') return exercise.exercise_id;
  return null;
}

function parseSetLogs(input: string, weight: string, completed: boolean) {
  return input
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value, index) => ({
      set_index: index + 1,
      reps: integerOrNull(value),
      weight: weight.trim() || null,
      completed
    }));
}

function integerOrNull(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (!/^\d+$/.test(trimmed)) return null;
  return Number(trimmed);
}

function hasExerciseInput(input: ExerciseFormState): boolean {
  return Boolean(
    input.setsInput.trim() ||
      input.weight.trim() ||
      input.rpe.trim() ||
      input.rir.trim() ||
      input.notes.trim() ||
      !input.completed
  );
}

function exerciseStatus(workoutStatus: WorkoutStatus, input: ExerciseFormState): WorkoutStatus {
  if (!input.completed && workoutStatus === 'completed') return 'partial';
  if (workoutStatus === 'partial' && input.completed) return 'completed';
  return workoutStatus;
}

function validateStructuredLog(
  workoutStatus: WorkoutStatus,
  exerciseInputs: Record<number, ExerciseFormState>,
  overallRpe: string,
  overallRir: string,
  painFlag: boolean,
  generalNotes: string
): string | null {
  const inputs = Object.values(exerciseInputs);
  const painNotes = inputs.some((input) => input.notes.trim()) || Boolean(generalNotes.trim());
  if (painFlag && !painNotes) {
    return 'כשמסמנים כאב, צריך לכתוב איפה ומה הורגש כדי להתאים את האימון הבא בזהירות.';
  }
  if (rangeError(overallRpe, 1, 10, 'RPE כללי')) return rangeError(overallRpe, 1, 10, 'RPE כללי');
  if (rangeError(overallRir, 0, 10, 'RIR כללי')) return rangeError(overallRir, 0, 10, 'RIR כללי');
  for (const input of inputs) {
    if (!hasExerciseInput(input)) continue;
    const invalidSet = input.setsInput
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)
      .find((value) => !/^\d+$/.test(value));
    if (invalidSet) return 'חזרות לפי סט צריכות להיות מספרים שלמים מופרדים בפסיקים, למשל 12,10,8.';
    const rpeError = rangeError(input.rpe, 1, 10, 'RPE לתרגיל');
    if (rpeError) return rpeError;
    const rirError = rangeError(input.rir, 0, 10, 'RIR לתרגיל');
    if (rirError) return rirError;
  }
  if (workoutStatus !== 'skipped' && inputs.length > 0 && !inputs.some(hasExerciseInput) && !overallRpe.trim() && !overallRir.trim() && !generalNotes.trim()) {
    return 'כדי לשמור ביצוע מובנה, מלא לפחות חזרות לתרגיל אחד, RPE/RIR כללי או הערה קצרה.';
  }
  return null;
}

function rangeError(value: string, min: number, max: number, label: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (!/^\d+$/.test(trimmed)) return `${label} חייב להיות מספר שלם.`;
  const parsed = Number(trimmed);
  if (parsed < min || parsed > max) return `${label} חייב להיות בין ${min} ל-${max}.`;
  return null;
}

function formatDaysPerWeek(days: number): string {
  return days === 1 ? 'יום אחד בשבוע' : `${days} ימים בשבוע`;
}

function formatPlanType(planType?: string | null): string | null {
  if (planType === 'single_session') return 'אימון יחיד';
  if (planType === 'multi_week') return 'תוכנית רב-שבועית';
  return null;
}

function formatPlanDuration(plan: WorkoutPlan): string | null {
  const duration = plan.session_length_minutes ?? plan.days[0]?.estimated_duration_minutes;
  return duration ? `${duration} דקות` : null;
}

function formatSetCount(sets: string): string {
  const normalized = sets.trim();
  return normalized === '1' ? 'סט אחד' : `${sets} סטים`;
}

function formatEquipment(equipment: string[]): string {
  if (equipment.length === 0) return 'משקל גוף';
  return equipment
    .map((item) => ({ dumbbells: 'משקולות יד', 'resistance bands': 'גומיות התנגדות', bodyweight: 'משקל גוף' })[item] ?? item)
    .join(', ');
}

function formatWorkoutStatus(status: string): string {
  return { completed: 'הושלם', skipped: 'פוספס', partial: 'חלקי', modified: 'שונה' }[status] ?? 'סטטוס לא מוכר';
}

function formatConfidence(confidence: string): string {
  return { low: 'נמוכה', medium: 'בינונית', high: 'גבוהה' }[confidence] ?? 'לא ידועה';
}

function formatDifficulty(difficulty: string): string {
  return { easy: 'קל', moderate: 'בינוני', hard: 'קשה' }[difficulty] ?? difficulty;
}

function formatLogDate(value: string): string {
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString('he-IL', { day: 'numeric', month: 'numeric' });
}

function formatLoggedExercise(result: WorkoutLog['exercise_results'][number]): string {
  const name = result.exercise_name ?? result.exercise ?? 'תרגיל';
  const setEntries = Array.isArray(result.sets) ? result.sets : [];
  const reps = result.reps?.join(', ') || setEntries.map((set) => set.reps).filter((value) => value != null).join(', ');
  const weight = result.weight ?? setEntries.find((set) => set.weight)?.weight ?? '';
  return [name, reps, weight].filter(Boolean).join(' ');
}
