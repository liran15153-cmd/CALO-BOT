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
        <p>Loading dashboard...</p>
      </section>
    );
  }

  if (status === 'error' || !dashboard) {
    return (
      <section className="panel dashboard-panel">
        <h3>Dashboard unavailable</h3>
        <p className="error-text">The backend did not return persisted coaching data.</p>
      </section>
    );
  }

  const nutritionRange = dashboard.estimated_nutrition_range
    ? `${dashboard.estimated_nutrition_range[0]}-${dashboard.estimated_nutrition_range[1]} kcal`
    : 'No meal estimates yet';

  return (
    <section className="panel dashboard-panel">
      <div className="panel-heading">
        <h3>{dashboard.current_goal ?? 'No goal set'}</h3>
        <p>{dashboard.current_workout_plan?.name ?? 'Complete onboarding to create your first plan.'}</p>
      </div>

      <div className="metric-grid" aria-label="Weekly metrics">
        <MetricCard
          icon={CalendarCheck}
          label="Workouts"
          value={String(dashboard.completed_workouts_this_week)}
          detail="completed this week"
        />
        <MetricCard
          icon={Utensils}
          label="Meals"
          value={String(dashboard.meals_logged_this_week)}
          detail="logged this week"
        />
        <MetricCard icon={Flame} label="Streak" value={`${dashboard.current_streak} days`} detail="active days" />
        <MetricCard
          icon={Dumbbell}
          label="Nutrition"
          value={nutritionRange}
          detail={dashboard.missed_workouts > 0 ? `${dashboard.missed_workouts} missed workout` : 'no misses tracked'}
        />
      </div>

      <div className="next-action">
        <NotebookText size={18} aria-hidden="true" />
        <div>
          <strong>Next action</strong>
          <p>{dashboard.next_recommended_action}</p>
        </div>
      </div>

      {dashboard.recent_coach_notes.length > 0 ? (
        <div className="coach-notes">
          <h4>Recent coach memory</h4>
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
