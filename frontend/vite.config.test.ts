import { describe, expect, it } from 'vitest';

import config from './vite.config';

describe('vite env config', () => {
  it('loads VITE variables from the root env files only', () => {
    expect(config).toMatchObject({ envDir: '..' });
  });
});
