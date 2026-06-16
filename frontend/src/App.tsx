import { Activity, Dumbbell, LayoutDashboard, MessageSquare, Settings, UserRound, Utensils } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { fetchHealth, type HealthStatus } from './api';
import { ChatPanel } from './ChatPanel';
import { DashboardPanel } from './DashboardPanel';
import { MealsPanel } from './MealsPanel';
import { OnboardingPanel } from './OnboardingPanel';
import { SettingsPanel } from './SettingsPanel';
import { WorkoutsPanel } from './WorkoutsPanel';
import './styles.css';

type View = 'dashboard' | 'onboarding' | 'chat' | 'workouts' | 'meals' | 'settings';

const navItems: Array<{ id: View; label: string; icon: typeof LayoutDashboard }> = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'onboarding', label: 'Onboarding', icon: UserRound },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'workouts', label: 'Workouts', icon: Dumbbell },
  { id: 'meals', label: 'Meals', icon: Utensils },
  { id: 'settings', label: 'Settings', icon: Settings }
];

function App() {
  const [view, setView] = useState<View>('dashboard');
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() =>
        setHealth({
          status: 'offline',
          service: 'calo-coach',
          database: 'unknown',
          ai_provider: 'unknown'
        })
      );
  }, []);

  const title = useMemo(() => navItems.find((item) => item.id === view)?.label ?? 'Dashboard', [view]);

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-block">
          <div className="brand-mark">C</div>
          <div>
            <h1>CALO Coach</h1>
            <p>Local-first fitness coach</p>
          </div>
        </div>

        <nav className="nav-stack">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={view === item.id ? 'nav-button active' : 'nav-button'}
                type="button"
                onClick={() => setView(item.id)}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="status-panel">
          <span className={health?.status === 'ok' ? 'status-dot online' : 'status-dot'} />
          <div>
            <strong>{health?.status === 'ok' ? 'Backend online' : 'Backend unavailable'}</strong>
            <p>AI: {health?.ai_provider ?? 'checking'}</p>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div>
            <span className="eyebrow">Personal coaching workspace</span>
            <h2>{title}</h2>
          </div>
          <div className="health-pill">
            <Activity size={16} aria-hidden="true" />
            <span>{health?.database === 'configured' ? 'SQLite ready' : 'Storage pending'}</span>
          </div>
        </header>

        {view === 'dashboard' ? (
          <DashboardPanel />
        ) : view === 'onboarding' ? (
          <OnboardingPanel />
        ) : view === 'chat' ? (
          <ChatPanel />
        ) : view === 'workouts' ? (
          <WorkoutsPanel />
        ) : view === 'meals' ? (
          <MealsPanel />
        ) : view === 'settings' ? (
          <SettingsPanel />
        ) : (
          <section className="panel">
            <h3>{title}</h3>
            <p>
              This local product shell is ready for onboarding, coach chat, workout planning, meal logging,
              structured memory, summaries, and settings.
            </p>
          </section>
        )}
      </section>
    </main>
  );
}

export default App;
