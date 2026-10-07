import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	server: {
		host: true,
		port: 5173,
		strictPort: true,
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8000',
				changeOrigin: true,
			},
		},
	},
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true,
			},
			adapter: adapter({
				fallback: 'index.html',
			}),
		}),
	],
});
