import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../../scripts/openapi.json',
  output: {
    path: 'src/generated',
  },
  plugins: [
    '@hey-api/client-fetch',
    '@hey-api/typescript',
    '@hey-api/sdk',
    'zod',
    {
      name: '@tanstack/svelte-query',
      infiniteQueryOptions: false,
    },
  ],
});
