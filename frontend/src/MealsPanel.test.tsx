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
            message: 'Meal image analysis is unavailable until an AI provider is configured.'
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

    fireEvent.click(screen.getByRole('button', { name: /Meals/i }));
    fireEvent.change(screen.getByLabelText(/Meal note/i), { target: { value: 'Lunch' } });
    fireEvent.change(screen.getByLabelText(/Meal image/i), {
      target: { files: [new File(['fake'], 'lunch.jpg', { type: 'image/jpeg' })] }
    });
    fireEvent.click(screen.getByRole('button', { name: /Upload meal/i }));

    expect(await screen.findByText(/not_analyzed/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Analyze image/i }));
    expect(await screen.findByText(/analysis is unavailable/i)).toBeInTheDocument();
  });

  it('logs a manual meal with approximate ranges', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Meals/i }));
    fireEvent.change(screen.getByLabelText(/Manual meal/i), { target: { value: 'Log protein shake 25g protein' } });
    fireEvent.click(screen.getByRole('button', { name: /Save meal log/i }));

    expect(await screen.findByText(/120-220 calories/i)).toBeInTheDocument();
    expect(screen.getByText(/25-35g protein/i)).toBeInTheDocument();
  });
});

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response;
}
