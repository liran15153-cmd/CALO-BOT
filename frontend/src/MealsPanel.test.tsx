import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('Meals UI', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/meals/recent')) {
          return jsonResponse([
            {
              id: 4,
              eaten_on: '2026-06-20',
              meal_type: 'snack',
              note: 'Greek yogurt and protein shake',
              image_path: null,
              calories_min: 210,
              calories_max: 380,
              protein_min: 35,
              protein_max: 55,
              confidence: 'legacy_score',
              items: [
                { id: 10, name: 'יוגורט יווני', quantity: 'מנה משוערת' },
                { id: 11, name: 'שייק חלבון', quantity: 'מנה משוערת' }
              ]
            }
          ]);
        }
        if (url.endsWith('/api/meals/upload') && init?.method === 'POST') {
          return jsonResponse({ id: 1, note: 'Lunch', image_path: 'data/uploads/meals/1/lunch.jpg', confidence: 'not_analyzed' });
        }
        if (url.endsWith('/api/meals/1/analyze') && init?.method === 'POST') {
          return jsonResponse({
            id: 1,
            meal_id: 1,
            provider_status: 'not_configured',
            detected_items: [],
            message: 'ניתוח תמונת ארוחה לא זמין עד שמוגדר ספק בינה מלאכותית.'
          });
        }
        if (url.endsWith('/api/meals/manual') && init?.method === 'POST') {
          return jsonResponse({
            id: 2,
            note: 'Log protein shake 25g protein',
            image_path: null,
            calories_min: 120,
            calories_max: 220,
            protein_min: 25,
            protein_max: 35,
            confidence: 'medium'
          });
        }
        return jsonResponse({});
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it('uploads a meal image and shows no-provider analysis state', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /תזונה/i }));
    fireEvent.change(screen.getByLabelText(/הערת ארוחה/i), { target: { value: 'Lunch' } });
    fireEvent.change(screen.getByLabelText(/תמונת ארוחה/i), {
      target: { files: [new File(['fake'], 'lunch.jpg', { type: 'image/jpeg' })] }
    });
    fireEvent.click(screen.getByRole('button', { name: /העלאת ארוחה/i }));

    expect(await screen.findByText(/טרם נותח/i)).toBeInTheDocument();
    expect(screen.getByText(/הארוחה מוכנה לניתוח/i)).toBeInTheDocument();
    expect(screen.getByText(/הערה: Lunch/i)).toBeInTheDocument();
    expect(screen.queryByText(/Lunch נשמרה/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /ניתוח תמונה/i }));
    expect(await screen.findByText(/לא זמין/i)).toBeInTheDocument();
    expect(screen.queryByText(/not_configured/i)).not.toBeInTheDocument();
  });

  it('logs a manual meal with approximate ranges', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /תזונה/i }));
    fireEvent.change(screen.getByLabelText(/ארוחה ידנית/i), { target: { value: 'Log protein shake 25g protein' } });
    fireEvent.click(screen.getByRole('button', { name: /שמירת ארוחה/i }));

    expect(await screen.findByText(/120-220 קלוריות/i)).toBeInTheDocument();
    expect(screen.getByText(/25-35 גרם חלבון/i)).toBeInTheDocument();
  });

  it('renders recent meal history with ranges and items', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /תזונה/i }));

    expect(await screen.findByText(/ארוחות אחרונות/i)).toBeInTheDocument();
    expect(screen.getByText(/210-380 קלוריות/i)).toBeInTheDocument();
    expect(screen.getByText(/35-55 גרם חלבון/i)).toBeInTheDocument();
    expect(screen.getByText(/לא ידוע/i)).toBeInTheDocument();
    expect(screen.queryByText(/legacy_score/i)).not.toBeInTheDocument();
    expect(screen.getByText(/יוגורט יווני/i)).toBeInTheDocument();
    expect(screen.getByText(/שייק חלבון/i)).toBeInTheDocument();
  });

  it('shows a load error instead of an empty history when recent meals fail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/meals/recent')) {
          return { ok: false, status: 500, json: async () => ({}) } as Response;
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /תזונה/i }));

    expect(await screen.findByText(/לא הצלחתי לטעון את הארוחות האחרונות/i)).toBeInTheDocument();
    expect(screen.queryByText(/אין עדיין ארוחות שמורות להצגה/i)).not.toBeInTheDocument();
  });

  it('does not render null nutrition ranges for manual meals without estimates', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'not_configured' });
        }
        if (url.endsWith('/api/meals/recent')) {
          return jsonResponse([]);
        }
        if (url.endsWith('/api/meals/manual') && init?.method === 'POST') {
          return jsonResponse({
            id: 3,
            note: 'Coffee',
            image_path: null,
            calories_min: null,
            calories_max: null,
            protein_min: null,
            protein_max: null,
            confidence: 'low'
          });
        }
        return jsonResponse({});
      })
    );

    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /תזונה/i }));
    fireEvent.change(screen.getByLabelText(/ארוחה ידנית/i), { target: { value: 'Coffee' } });
    fireEvent.click(screen.getByRole('button', { name: /שמירת ארוחה/i }));

    expect(await screen.findByText(/ביטחון נמוך/i)).toBeInTheDocument();
    expect(screen.queryByText(/null-null/i)).not.toBeInTheDocument();
  });

  it('shows configured image analysis ranges, detected items, and follow-up questions', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith('/api/health')) {
          return jsonResponse({ status: 'ok', service: 'calo-coach', database: 'configured', ai_provider: 'configured' });
        }
        if (url.endsWith('/api/meals/upload') && init?.method === 'POST') {
          return jsonResponse({ id: 1, note: 'Lunch', image_path: 'data/uploads/meals/1/lunch.jpg', confidence: 'not_analyzed' });
        }
        if (url.endsWith('/api/meals/1/analyze') && init?.method === 'POST') {
          return jsonResponse({
            id: 1,
            meal_id: 1,
            provider_status: 'configured',
            detected_items: [{ name: 'קערת עוף ואורז', quantity: 'קערה אחת' }],
            follow_up_questions: ['כמה אורז היה בקערה?'],
            message: '',
            analysis: {
              calorie_range: [520, 760],
              macro_ranges: { protein: [35, 52] },
              confidence: 'medium'
            }
          });
        }
        return jsonResponse({});
      })
    );
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /תזונה/i }));
    fireEvent.change(screen.getByLabelText(/הערת ארוחה/i), { target: { value: 'Lunch' } });
    fireEvent.change(screen.getByLabelText(/תמונת ארוחה/i), {
      target: { files: [new File(['fake'], 'lunch.jpg', { type: 'image/jpeg' })] }
    });
    fireEvent.click(screen.getByRole('button', { name: /העלאת ארוחה/i }));
    await screen.findByText(/טרם נותח/i);
    fireEvent.click(screen.getByRole('button', { name: /ניתוח תמונה/i }));

    expect(await screen.findByText(/520-760 קלוריות/i)).toBeInTheDocument();
    expect(screen.getByText(/35-52 גרם חלבון/i)).toBeInTheDocument();
    expect(screen.getByText(/קערת עוף ואורז/i)).toBeInTheDocument();
    expect(screen.getByText(/כמה אורז/i)).toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
