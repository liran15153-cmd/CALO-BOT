import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Settings UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/dashboard')) {
          return jsonResponse({
            current_goal: null,
            current_workout_plan: null,
            completed_workouts_this_week: 0,
            meals_logged_this_week: 0,
            estimated_nutrition_range: null,
            recent_coach_notes: [],
            current_streak: 0,
            missed_workouts: 0,
            next_recommended_action: 'סיים אונבורדינג.'
          });
        }
        if (url.endsWith('/api/settings')) {
          return jsonResponse({
            ai_provider: 'not_configured',
            model: 'claude-haiku-4-5',
            database: 'configured',
            api_key_present: false,
            disclaimer: 'זו אינה עצה רפואית.'
          });
        }
        if (url.endsWith('/api/usage')) {
          return jsonResponse({
            usage_date: '2026-06-15',
            chat_requests_count: 1,
            image_analysis_count: 0,
            summary_requests_count: 1,
            estimated_tokens_in: 12,
            estimated_tokens_out: 4,
            estimated_tokens_total: 16,
            daily_ai_token_limit: 50000,
            tokens_remaining: 49984
          });
        }
        if (url.endsWith('/api/settings/export')) {
          return jsonResponse({ profile: null, meals: [] });
        }
        if (url.endsWith('/api/settings/reset') && init?.method === 'POST') {
          return jsonResponse({ deleted_records: 1, message: 'הנתונים המקומיים אופסו.' });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it('shows provider status without exposing an API key and supports export/reset actions', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /הגדרות/i }));

    expect((await screen.findAllByText(/לא מוגדר/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/not_configured/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sk-/i)).not.toBeInTheDocument();
    expect(screen.getByText(/אינה עצה רפואית/i)).toBeInTheDocument();
    expect(await screen.findByText(/בקשות צ'אט/i)).toBeInTheDocument();
    expect(screen.getByText(/סיכומים/i)).toBeInTheDocument();
    expect(screen.getByText(/תקציב שנותר/i)).toBeInTheDocument();
    expect(screen.getByText(/49,984/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /ייצוא/i }));
    expect(await screen.findByText(/הייצוא מוכן/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /איפוס נתונים מקומיים/i }));
    expect(await screen.findByText(/לאישור מחיקה/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /אישור איפוס/i }));
    expect(await screen.findByText(/רשומה אחת נמחקה/i)).toBeInTheDocument();
    expect(screen.queryByText(/1 רשומות נמחקו/i)).not.toBeInTheDocument();
  });

  it('shows settings even when usage metrics fail to load', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/settings')) {
          return jsonResponse({
            ai_provider: 'not_configured',
            model: 'claude-haiku-4-5',
            database: 'configured',
            api_key_present: false,
            disclaimer: 'זו אינה עצה רפואית.'
          });
        }
        if (url.endsWith('/api/usage')) {
          return { ok: false, status: 500, json: async () => ({}) } as Response;
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /הגדרות/i }));

    expect(await screen.findByText(/claude-haiku-4-5/i)).toBeInTheDocument();
    expect(screen.queryByText(/ההגדרות לא זמינות/i)).not.toBeInTheDocument();
  });

  it('shows an export failure without leaving the settings action busy', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/settings')) {
          return jsonResponse({
            ai_provider: 'not_configured',
            model: 'claude-haiku-4-5',
            database: 'configured',
            api_key_present: false,
            disclaimer: 'זו אינה עצה רפואית.'
          });
        }
        if (url.endsWith('/api/usage')) {
          return jsonResponse({
            usage_date: '2026-06-15',
            chat_requests_count: 0,
            image_analysis_count: 0,
            summary_requests_count: 0,
            estimated_tokens_in: 0,
            estimated_tokens_out: 0,
            estimated_tokens_total: 0,
            daily_ai_token_limit: 50000,
            tokens_remaining: 50000
          });
        }
        if (url.endsWith('/api/settings/export')) {
          return { ok: false, status: 500, json: async () => ({}) } as Response;
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /הגדרות/i }));
    fireEvent.click(await screen.findByRole('button', { name: /ייצוא/i }));

    expect(await screen.findByText(/הייצוא נכשל/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ייצוא/i })).not.toBeDisabled();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
