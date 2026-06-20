import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import App from './App';

describe('App shell', () => {
  it('renders the local coach workspace and primary navigation', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /CALO Coach/i })).toBeInTheDocument();
    expect(screen.getByRole('main')).toHaveAttribute('dir', 'rtl');
    expect(screen.getByRole('main')).toHaveAttribute('lang', 'he');
    expect(screen.getByRole('button', { name: /לוח בקרה/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /צ'אט/i })).toBeInTheDocument();
    expect(screen.getByText(/מאמן כושר מקומי/i)).toBeInTheDocument();
  });
});
