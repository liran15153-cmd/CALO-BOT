import { CalendarCheck, Dumbbell, Flame, NotebookText, Utensils } from 'lucide-react';
import { useEffect, useState } from 'react';

import { fetchDashboard, type DashboardState } from './api';
import { formatPlanSessionLength, formatPlanType, formatPlanWeeks } from './planFormatters';

export function DashboardPanel() {
  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => {
    let active = true;
    fetchDashboard()
      .then((data) => {
        if (!active) return;
        setDashboard(data);
        setStatus('ready');
      })
      .catch(() => {
        if (!active) return;
        setStatus('error');
      });
    return () => {
      active = false;
    };
  }, []);

  if (status === 'loading') {
    return (
      <section className="panel dashboard-panel">
        <p>טוען לוח בקרה...</p>
      </section>
    );
  }

  if (status === 'error' || !dashboard) {
    return (
      <section className="panel dashboard-panel">
        <h3>לוח הבקרה לא זמין</h3>
        <p className="error-text">הבקאנד לא החזיר נתוני אימון שמורים.</p>
      </section>
    );
  }

  const nutritionRange = formatNutritionRange(dashboard.estimated_nutrition_range);
  const currentPlanSummary = formatCurrentPlanSummary(dashboard.current_workout_plan);

  return (
    <section className="panel dashboard-panel">
      <div className="panel-heading">
        <h3>{formatGoal(dashboard.current_goal)}</h3>
        <p>{currentPlanSummary ?? 'השלם פרופיל כדי ליצור את התוכנית הראשונה שלך.'}</p>
      </div>

      <div className="metric-grid" aria-label="מדדים שבועיים">
        <MetricCard
          icon={CalendarCheck}
          label="אימונים"
          value={String(dashboard.completed_workouts_this_week)}
          detail="הושלמו השבוע"
        />
        <MetricCard
          icon={Utensils}
          label="ארוחות"
          value={String(dashboard.meals_logged_this_week)}
          detail="תועדו השבוע"
        />
        <MetricCard icon={Flame} label="רצף" value={formatDayCount(dashboard.current_streak)} detail="ימים פעילים" />
        <MetricCard
          label="תזונה"
          icon={Utensils}
          value={nutritionRange}
          detail="טווח שבועי משוער"
        />
        <MetricCard
          icon={Dumbbell}
          label="פספוסים"
          value={formatMissedWorkoutCount(dashboard.missed_workouts)}
          detail={dashboard.missed_workouts > 0 ? 'דורש התאמה עדינה' : 'לא תועדו פספוסים'}
        />
      </div>

      <div className="next-action">
        <NotebookText size={18} aria-hidden="true" />
        <div>
          <strong>פעולה הבאה</strong>
          {dashboard.next_workout ? (
            <div className="next-action-workout">
              <span>{dashboard.next_workout.name ?? 'האימון הבא'}</span>
              <span className="next-action-signal">{formatLoadSignal(dashboard.next_workout.load_signal)}</span>
            </div>
          ) : null}
          {dashboard.next_workout?.first_exercise ? <p>{formatFirstExercise(dashboard.next_workout.first_exercise)}</p> : null}
          <p>{dashboard.next_recommended_action}</p>
        </div>
      </div>

      <div className="next-action nutrition-action">
        <Utensils size={18} aria-hidden="true" />
        <div>
          <strong>תזונה היום</strong>
          {formatProteinRange(dashboard.estimated_protein_range_today) ? (
            <div className="next-action-workout">
              <span>{formatProteinRange(dashboard.estimated_protein_range_today)}</span>
              <span className="next-action-signal">{formatMealCountToday(dashboard.meals_logged_today)}</span>
            </div>
          ) : null}
          <p>{dashboard.nutrition_action}</p>
        </div>
      </div>
    </section>
  );
}

function formatNutritionRange(range: DashboardState['estimated_nutrition_range']): string {
  if (!range || range[0] == null || range[1] == null) {
    return 'אין עדיין הערכות ארוחה';
  }
  return `${range[0]}-${range[1]} קלוריות`;
}

function formatProteinRange(range: DashboardState['estimated_protein_range_today']): string | null {
  if (!range || range[0] == null || range[1] == null) {
    return null;
  }
  return `${range[0]}-${range[1]} גרם חלבון`;
}

function formatCurrentPlanSummary(plan: DashboardState['current_workout_plan']): string | null {
  if (!plan) return null;
  const details = [
    formatPlanType(plan.plan_type),
    formatPlanWeeks(plan.plan_type, plan.duration_weeks),
    formatPlanSessionLength(plan.plan_type, plan.session_length_minutes)
  ].filter(Boolean);
  return details.length ? `${plan.name} | ${details.join(' | ')}` : plan.name;
}

function formatMealCountToday(value: number): string {
  return value === 1 ? 'ארוחה אחת היום' : `${value} ארוחות היום`;
}

function formatLoadSignal(signal?: string | null): string {
  return (
    {
      adherence_risk: 'התאמה שמרנית',
      pain_caution: 'זהירות מכאב',
      recovery_needed: 'התאוששות קודם',
      progress_candidate: 'אפשר להתקדם מעט',
      maintain: 'שמירה'
    }[signal ?? ''] ?? 'התאמה'
  );
}

function formatFirstExercise(exercise: NonNullable<NonNullable<DashboardState['next_workout']>['first_exercise']>): string {
  const prescription = [exercise.sets, exercise.reps_or_duration, exercise.rest ? `מנוחה ${exercise.rest}` : null].filter(Boolean);
  return prescription.length
    ? `פותחים: ${exercise.name ?? 'התרגיל הראשון'} | ${prescription.join(' | ')}`
    : `פותחים: ${exercise.name ?? 'התרגיל הראשון'}`;
}

function formatGoal(goal: string | null): string {
  if (!goal) return 'לא הוגדרה מטרה';
  return (
    {
      build_muscle: 'בניית שריר',
      lose_fat: 'ירידה בשומן',
      improve_fitness: 'שיפור כושר',
      maintain_health: 'שמירה על בריאות',
      improve_consistency: 'שיפור עקביות',
      improve_strength: 'שיפור כוח',
      improve_endurance: 'שיפור סבולת',
      improve_mobility: 'שיפור מוביליטי'
    }[goal] ?? 'מטרה לא מוכרת'
  );
}

function formatDayCount(value: number): string {
  return value === 1 ? 'יום אחד' : `${value} ימים`;
}

function formatMissedWorkoutCount(value: number): string {
  return value === 1 ? 'אימון אחד שפוספס' : `${value} אימונים שפוספסו`;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail
}: {
  icon: typeof CalendarCheck;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="metric-card">
      <div className="metric-icon">
        <Icon size={18} aria-hidden="true" />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
