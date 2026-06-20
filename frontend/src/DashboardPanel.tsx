import { CalendarCheck, Dumbbell, Flame, NotebookText, TrendingUp, Utensils } from 'lucide-react';
import { useEffect, useState } from 'react';

import { fetchCurrentWeeklySummary, fetchDashboard, type DashboardState, type SummaryResponse } from './api';

export function DashboardPanel() {
  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [weeklySummary, setWeeklySummary] = useState<SummaryResponse | null>(null);
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
    fetchCurrentWeeklySummary()
      .then((data) => {
        if (!active) return;
        setWeeklySummary(data.summary?.trim() ? data : null);
      })
      .catch(() => {
        if (!active) return;
        setWeeklySummary(null);
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
  const weeklyRangeLabel = formatWeekRange(weeklySummary?.week_start, weeklySummary?.week_end);
  const weeklyConsistency = formatConsistency(weeklySummary?.metrics);
  const weeklyMetricItems = formatWeeklyMetricItems(weeklySummary?.metrics);

  return (
    <section className="panel dashboard-panel">
      <div className="panel-heading">
        <h3>{formatGoal(dashboard.current_goal)}</h3>
        <p>{dashboard.current_workout_plan?.name ?? 'השלם פרופיל כדי ליצור את התוכנית הראשונה שלך.'}</p>
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

      {weeklySummary?.summary ? (
        <section className="weekly-review" aria-label="סקירה שבועית">
          <div className="weekly-review-header">
            <div className="weekly-review-title">
              <strong>סקירה שבועית</strong>
              {weeklyRangeLabel ? <span>{weeklyRangeLabel}</span> : null}
            </div>
            {weeklyConsistency ? <span className="next-action-signal">{weeklyConsistency}</span> : null}
          </div>
          <p>{weeklySummary.summary}</p>
          {weeklyMetricItems.length > 0 ? (
            <div className="weekly-review-metrics">
              {weeklyMetricItems.map((item) => (
                <span className="weekly-review-metric" key={item.label}>
                  {item.label}: {item.value}
                </span>
              ))}
            </div>
          ) : null}
          {weeklySummary.next_action ? (
            <p className="weekly-review-action">
              <TrendingUp size={16} aria-hidden="true" />
              <span>{weeklySummary.next_action}</span>
            </p>
          ) : null}
        </section>
      ) : null}

      {dashboard.recent_coach_notes.length > 0 ? (
        <div className="coach-notes">
          <h4>זיכרון מאמן אחרון</h4>
          <ul>
            {dashboard.recent_coach_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}
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

function formatMealCountToday(value: number): string {
  return value === 1 ? 'ארוחה אחת היום' : `${value} ארוחות היום`;
}

function formatWeekRange(start?: string | null, end?: string | null): string | null {
  if (!start || !end) return null;
  const startLabel = formatShortDate(start);
  const endLabel = formatShortDate(end);
  if (!startLabel || !endLabel) return null;
  return `${startLabel} - ${endLabel}`;
}

function formatShortDate(value: string): string | null {
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toLocaleDateString('he-IL', { day: 'numeric', month: 'numeric' });
}

function formatConsistency(metrics?: SummaryResponse['metrics']): string | null {
  const value = numberMetric(metrics, 'consistency_percentage');
  return value == null ? null : `${value}% עקביות`;
}

function formatWeeklyMetricItems(metrics?: SummaryResponse['metrics']): Array<{ label: string; value: string }> {
  const completed = numberMetric(metrics, 'workouts_completed');
  const missed = numberMetric(metrics, 'missed_workouts');
  const meals = numberMetric(metrics, 'meals_logged');
  return [
    completed == null ? null : { label: 'הושלמו', value: formatWorkoutCount(completed) },
    missed == null ? null : { label: 'פוספסו', value: formatWorkoutCount(missed) },
    meals == null ? null : { label: 'ארוחות', value: formatMealCount(meals) }
  ].filter((item): item is { label: string; value: string } => item !== null);
}

function numberMetric(metrics: SummaryResponse['metrics'] | undefined, key: string): number | null {
  const value = metrics?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function formatWorkoutCount(value: number): string {
  if (value === 1) return 'אימון אחד';
  return `${value} אימונים`;
}

function formatMealCount(value: number): string {
  if (value === 1) return 'ארוחה אחת';
  return `${value} ארוחות`;
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
      improve_endurance: 'שיפור סבולת'
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
