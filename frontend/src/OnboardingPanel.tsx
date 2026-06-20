import { useEffect, useState } from 'react';

import { fetchOnboarding, saveOnboarding, type OnboardingPayload } from './api';

const defaultPayload: OnboardingPayload = {
  name: '',
  age_range: '',
  gender: 'prefer_not_to_say',
  height_cm: null,
  weight_kg: null,
  main_goal: 'build_muscle',
  experience_level: 'beginner',
  training_location: 'gym',
  available_equipment: [],
  weekly_availability: 3,
  session_length_minutes: 45,
  preferred_workout_days: [],
  injuries_limitations: '',
  nutrition_preference: 'high_protein',
  foods_disliked: '',
  allergies: '',
  typical_schedule: '',
  coaching_style: 'direct',
  consent_disclaimer: false
};

export function OnboardingPanel() {
  const [form, setForm] = useState<OnboardingPayload>(defaultPayload);
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  useEffect(() => {
    fetchOnboarding()
      .then((state) => {
        if (state.profile) {
          setForm({
            ...defaultPayload,
            ...state.profile,
            available_equipment: state.profile.available_equipment ?? [],
            preferred_workout_days: state.profile.preferred_workout_days ?? []
          });
        }
      })
      .catch(() => undefined);
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus('saving');
    try {
      await saveOnboarding(form);
      setStatus('saved');
    } catch {
      setStatus('error');
    }
  }

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <h3>פרופיל ראשוני</h3>
        <p>הגדר את נתוני המינימום שהמאמן צריך לפני התאמה אישית.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          <span>שם</span>
          <input
            required
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
        </label>

        <label>
          <span>מטרה מרכזית</span>
          <select value={form.main_goal} onChange={(event) => setForm({ ...form, main_goal: event.target.value })}>
            <option value="build_muscle">בניית שריר</option>
            <option value="lose_fat">ירידה בשומן</option>
            <option value="improve_fitness">שיפור כושר</option>
            <option value="maintain_health">שמירה על בריאות</option>
            <option value="improve_consistency">שיפור עקביות</option>
            <option value="improve_strength">שיפור כוח</option>
            <option value="improve_endurance">שיפור סבולת</option>
          </select>
        </label>

        <label>
          <span>רמת ניסיון</span>
          <select
            value={form.experience_level}
            onChange={(event) => setForm({ ...form, experience_level: event.target.value })}
          >
            <option value="beginner">מתחיל</option>
            <option value="intermediate">בינוני</option>
            <option value="advanced">מתקדם</option>
          </select>
        </label>

        <label>
          <span>מיקום אימון</span>
          <select
            value={form.training_location}
            onChange={(event) => setForm({ ...form, training_location: event.target.value })}
          >
            <option value="home">בית</option>
            <option value="gym">חדר כושר</option>
            <option value="outdoors">בחוץ</option>
            <option value="mixed">מעורב</option>
          </select>
        </label>

        <label>
          <span>ימי אימון בשבוע</span>
          <input
            min={1}
            max={7}
            type="number"
            value={form.weekly_availability}
            onChange={(event) => setForm({ ...form, weekly_availability: Number(event.target.value) })}
          />
        </label>

        <label>
          <span>משך אימון</span>
          <select
            value={form.session_length_minutes}
            onChange={(event) => setForm({ ...form, session_length_minutes: Number(event.target.value) })}
          >
            <option value={15}>15 דקות</option>
            <option value={30}>30 דקות</option>
            <option value={45}>45 דקות</option>
            <option value={60}>60 דקות</option>
            <option value={75}>75+ דקות</option>
          </select>
        </label>

        <label>
          <span>ציוד</span>
          <input
            placeholder="משקולות יד, גומיות התנגדות"
            value={form.available_equipment.join(', ')}
            onChange={(event) =>
              setForm({
                ...form,
                available_equipment: event.target.value.split(',').map((item) => item.trim()).filter(Boolean)
              })
            }
          />
        </label>

        <label>
          <span>סגנון אימון</span>
          <select
            value={form.coaching_style}
            onChange={(event) => setForm({ ...form, coaching_style: event.target.value })}
          >
            <option value="direct">ישיר</option>
            <option value="supportive">תומך</option>
            <option value="strict">נוקשה</option>
            <option value="minimal">מינימלי</option>
            <option value="detailed">מפורט</option>
          </select>
        </label>

        <label className="wide">
          <span>פציעות או מגבלות</span>
          <textarea
            value={form.injuries_limitations ?? ''}
            onChange={(event) => setForm({ ...form, injuries_limitations: event.target.value })}
          />
        </label>

        <label className="checkbox-row wide">
          <input
            type="checkbox"
            checked={form.consent_disclaimer}
            onChange={(event) => setForm({ ...form, consent_disclaimer: event.target.checked })}
          />
          <span>האפליקציה נותנת הכוונת כושר ותזונה כללית, לא עצה רפואית.</span>
        </label>

        <div className="form-actions wide">
          <button type="submit" className="primary-button" disabled={status === 'saving'}>
            שמירת פרופיל
          </button>
          {status === 'saved' && <span className="success-text">הפרופיל נשמר</span>}
          {status === 'error' && <span className="error-text">לא הצלחתי לשמור את הפרופיל</span>}
        </div>
      </form>
    </section>
  );
}
