import { Dumbbell } from 'lucide-react';
import { useState } from 'react';

import { generateWorkoutPlan, saveWorkoutLog, type WorkoutLog, type WorkoutPlan } from './api';

export function WorkoutsPanel() {
  const [prompt, setPrompt] = useState('Build me a 3-day gym plan for muscle');
  const [logText, setLogText] = useState('I did 3 sets of bench press 10, 8, 7 with 50kg');
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [lastLog, setLastLog] = useState<WorkoutLog | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [logStatus, setLogStatus] = useState<'idle' | 'saving' | 'error'>('idle');

  async function handleGenerate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus('loading');
    try {
      const nextPlan = await generateWorkoutPlan(prompt);
      setPlan(nextPlan);
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  async function handleLog(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLogStatus('saving');
    try {
      const saved = await saveWorkoutLog(logText);
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
        <h3>Workout plan</h3>
        <p>Generate a structured plan that can be inspected and edited later.</p>
      </div>

      <form className="composer" onSubmit={handleGenerate}>
        <label htmlFor="plan-request">Plan request</label>
        <div className="composer-row">
          <textarea id="plan-request" value={prompt} onChange={(event) => setPrompt(event.target.value)} />
          <button className="primary-button icon-button" type="submit" disabled={status === 'loading'}>
            <Dumbbell size={17} aria-hidden="true" />
            Generate plan
          </button>
        </div>
      </form>

      {status === 'error' && <p className="error-text">Could not generate plan.</p>}

      {plan && (
        <div className="plan-view">
          <div className="plan-summary">
            <h4>{plan.name}</h4>
            <span>{plan.days_per_week} days/week</span>
            <span>{plan.equipment_needed.join(', ') || 'bodyweight'}</span>
          </div>
          {plan.days.map((day) => (
            <article className="plan-day" key={day.name}>
              <h5>{day.name}</h5>
              <p>{day.warmup.join(' / ')}</p>
              <div className="exercise-grid">
                {day.exercises.map((exercise) => (
                  <div className="exercise-row" key={exercise.name}>
                    <strong>{exercise.name}</strong>
                    <span>{exercise.sets} sets</span>
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
        <h4>Workout log</h4>
        <form className="composer" onSubmit={handleLog}>
          <label htmlFor="workout-log">Workout log</label>
          <div className="composer-row">
            <textarea id="workout-log" value={logText} onChange={(event) => setLogText(event.target.value)} />
            <button className="primary-button icon-button" type="submit" disabled={logStatus === 'saving'}>
              Save workout log
            </button>
          </div>
        </form>
        {logStatus === 'error' && <p className="error-text">Could not save workout log.</p>}
        {lastLog && (
          <div className="log-result">
            <strong>{lastLog.status}</strong>
            <span>Confidence: {lastLog.parse_confidence}</span>
            {lastLog.pain_flag && <span className="error-text">Pain flag saved</span>}
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
