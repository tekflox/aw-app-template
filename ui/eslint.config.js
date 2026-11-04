// Flat config (ESLint 10) — @eslint/js recommended rules only, per
// docs/standards/pipeline-testing.md §6a. No Prettier (see that section's
// "Rejected: Prettier"). ui/dist is committed build output, not source —
// never linted.
import js from '@eslint/js';
import globals from 'globals';

export default [
  { ignores: ['dist/**'] },
  js.configs.recommended,
  {
    files: ['src/**/*.js'],
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    files: ['vite.config.js'],
    languageOptions: {
      globals: globals.node,
    },
  },
];
