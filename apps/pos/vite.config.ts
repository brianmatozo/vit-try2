import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import { defineConfig } from 'vite';

export default defineConfig({
	server: {
		host: true,
		port: 5174,
		strictPort: true,
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8000',
				changeOrigin: true,
				secure: false,
			},
		},
	},
	plugins: [
		basicSsl(),
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true,
			},
			adapter: adapter({
				fallback: 'index.html',
			}),
		}),
	],
});
