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
