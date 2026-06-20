import { CalendarCheck, Dumbbell, Flame, NotebookText, Utensils } from 'lucide-react';
import { useEffect, useState } from 'react';

import { fetchDashboard, type DashboardState } from './api';

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
        <MetricCard icon={Flame} label="רצף" value={`${dashboard.current_streak} ימים`} detail="ימים פעילים" />
        <MetricCard
          icon={Dumbbell}
          label="תזונה"
          value={nutritionRange}
          detail={dashboard.missed_workouts > 0 ? `${dashboard.missed_workouts} אימונים שפוספסו` : 'לא תועדו פספוסים'}
        />
      </div>

      <div className="next-action">
        <NotebookText size={18} aria-hidden="true" />
        <div>
          <strong>פעולה הבאה</strong>
          <p>{dashboard.next_recommended_action}</p>
        </div>
      </div>

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
