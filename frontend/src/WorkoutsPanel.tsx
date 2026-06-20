import { Dumbbell } from 'lucide-react';
import { useEffect, useState } from 'react';

import { fetchCurrentWorkoutPlan, generateWorkoutPlan, saveWorkoutLog, type WorkoutLog, type WorkoutPlan } from './api';

export function WorkoutsPanel() {
  const [prompt, setPrompt] = useState('');
  const [logText, setLogText] = useState('');
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [lastLog, setLastLog] = useState<WorkoutLog | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [logStatus, setLogStatus] = useState<'idle' | 'saving' | 'error'>('idle');

  useEffect(() => {
    let active = true;
    fetchCurrentWorkoutPlan()
      .then((currentPlan) => {
        if (!active || !currentPlan) return;
        setPlan(currentPlan);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  async function handleGenerate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) return;
    setStatus('loading');
    try {
      const nextPlan = await generateWorkoutPlan(trimmed);
      setPlan(nextPlan);
      setStatus('idle');
    } catch {
      setStatus('error');
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
      setLogText('');
      setLogStatus('idle');
    } catch {
      setLogStatus('error');
    }
  }

  return (
    <section className="panel workouts-panel">
      <div className="panel-heading">
        <h3>תוכנית אימון</h3>
        <p>צור תוכנית מובנית שאפשר לבדוק, לעדכן ולתעד מולה בהמשך.</p>
      </div>

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

      {plan && (
        <div className="plan-view">
          <div className="plan-summary">
            <h4>{plan.name}</h4>
            <span>{plan.days_per_week} ימים בשבוע</span>
            <span>{formatEquipment(plan.equipment_needed)}</span>
          </div>
          {plan.days.map((day) => (
            <article className="plan-day" key={day.name}>
              <h5>{day.name}</h5>
              <p>{day.warmup.join(' / ')}</p>
              <div className="exercise-grid">
                {day.exercises.map((exercise) => (
                  <div className="exercise-row" key={exercise.name}>
                    <strong>{exercise.name}</strong>
                    <span>{exercise.sets} סטים</span>
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
        <h4>תיעוד אימון</h4>
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
            {lastLog.pain_flag && <span className="error-text">סימון כאב נשמר</span>}
            {lastLog.exercise_results.map((result) => (
              <span key={`${result.exercise}-${result.weight ?? ''}`}>
                {result.exercise} {result.reps?.join(', ')} {result.weight ?? ''}
              </span>
            ))}
          </div>
        )}
      </section>
    </section>
  );
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
