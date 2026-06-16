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
        <h3>Onboarding</h3>
        <p>Set the minimum profile data the coach needs before personalization.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input
            required
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
        </label>

        <label>
          <span>Main goal</span>
          <select value={form.main_goal} onChange={(event) => setForm({ ...form, main_goal: event.target.value })}>
            <option value="build_muscle">Build muscle</option>
            <option value="lose_fat">Lose fat</option>
            <option value="improve_fitness">Improve fitness</option>
            <option value="maintain_health">Maintain health</option>
            <option value="improve_consistency">Improve consistency</option>
            <option value="improve_strength">Improve strength</option>
            <option value="improve_endurance">Improve endurance</option>
          </select>
        </label>

        <label>
          <span>Experience</span>
          <select
            value={form.experience_level}
            onChange={(event) => setForm({ ...form, experience_level: event.target.value })}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </label>

        <label>
          <span>Training location</span>
          <select
            value={form.training_location}
            onChange={(event) => setForm({ ...form, training_location: event.target.value })}
          >
            <option value="home">Home</option>
            <option value="gym">Gym</option>
            <option value="outdoors">Outdoors</option>
            <option value="mixed">Mixed</option>
          </select>
        </label>

        <label>
          <span>Workout days per week</span>
          <input
            min={1}
            max={7}
            type="number"
            value={form.weekly_availability}
            onChange={(event) => setForm({ ...form, weekly_availability: Number(event.target.value) })}
          />
        </label>

        <label>
          <span>Session length</span>
          <select
            value={form.session_length_minutes}
            onChange={(event) => setForm({ ...form, session_length_minutes: Number(event.target.value) })}
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={45}>45 minutes</option>
            <option value={60}>60 minutes</option>
            <option value={75}>75+ minutes</option>
          </select>
        </label>

        <label>
          <span>Equipment</span>
          <input
            placeholder="dumbbells, resistance bands"
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
          <span>Coaching style</span>
          <select
            value={form.coaching_style}
            onChange={(event) => setForm({ ...form, coaching_style: event.target.value })}
          >
            <option value="direct">Direct</option>
            <option value="supportive">Supportive</option>
            <option value="strict">Strict</option>
            <option value="minimal">Minimal</option>
            <option value="detailed">Detailed</option>
          </select>
        </label>

        <label className="wide">
          <span>Injuries or limitations</span>
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
          <span>The app gives general fitness and nutrition guidance, not medical advice.</span>
        </label>

        <div className="form-actions wide">
          <button type="submit" className="primary-button" disabled={status === 'saving'}>
            Save profile
          </button>
          {status === 'saved' && <span className="success-text">Profile saved</span>}
          {status === 'error' && <span className="error-text">Could not save profile</span>}
        </div>
      </form>
    </section>
  );
}

