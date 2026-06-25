import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
            current_streak: 0,
            missed_workouts: 0,
            next_recommended_action: 'להשלים אונבורדינג.'
          });
        }
        if (url.endsWith('/api/settings')) {
          return jsonResponse(settingsPayload());
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
    const { container } = render(<App />);
    openSettings(container);

    await waitForSettings();
    expect(screen.queryByText(/not_configured/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sk-/i)).not.toBeInTheDocument();
    expect(screen.getByText('אימות Supabase')).toBeInTheDocument();
    expect(screen.getByText('מצב מקומי')).toBeInTheDocument();
    expect(screen.queryByText(/local fallback/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/General wellness only/i)).not.toBeInTheDocument();
    expect(screen.getByText(/49,984/i)).toBeInTheDocument();

    const [exportButton, resetButton] = settingsActionButtons(container);
    fireEvent.click(exportButton);
    expect(await screen.findByDisplayValue(/"profile": null/i)).toBeInTheDocument();

    fireEvent.click(resetButton);
    fireEvent.click(resetButton);
    await waitFor(() => expect(screen.queryByDisplayValue(/"profile": null/i)).not.toBeInTheDocument());
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
          return jsonResponse(settingsPayload());
        }
        if (url.endsWith('/api/usage')) {
          return { ok: false, status: 500, json: async () => ({}) } as Response;
        }
        return jsonResponse({});
      })
    );

    const { container } = render(<App />);
    openSettings(container);

    await waitForSettings();
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
          return jsonResponse(settingsPayload());
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

    const { container } = render(<App />);
    openSettings(container);
    await waitForSettings();

    const [exportButton] = settingsActionButtons(container);
    fireEvent.click(exportButton);

    await waitFor(() => expect(exportButton).not.toBeDisabled());
  });
});

function settingsPayload() {
  return {
    ai_provider: 'not_configured',
    model: 'claude-haiku-4-5',
    chat_model: 'claude-haiku-4-5',
    database: 'configured',
    api_key_present: false,
    supabase: 'not_configured',
    supabase_storage: 'local',
    disclaimer: 'מידע כללי לאורח חיים בריא בלבד.'
  };
}

function openSettings(container: HTMLElement) {
  const navButtons = container.querySelectorAll<HTMLButtonElement>('.nav-button');
  fireEvent.click(navButtons[navButtons.length - 1]);
}

function settingsActionButtons(container: HTMLElement): HTMLButtonElement[] {
  return Array.from(container.querySelectorAll<HTMLButtonElement>('.settings-actions button'));
}

async function waitForSettings() {
  expect((await screen.findAllByText(/claude-haiku-4-5/i)).length).toBeGreaterThan(0);
}

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
