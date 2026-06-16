import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import App from './App';

describe('App shell', () => {
  it('renders the local coach workspace and primary navigation', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /CALO Coach/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chat/i })).toBeInTheDocument();
    expect(screen.getByText(/Local-first fitness coach/i)).toBeInTheDocument();
  });
});

