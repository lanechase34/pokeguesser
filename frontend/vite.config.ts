import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => ({
    build: {
        outDir: 'build',
        chunkSizeWarningLimit: 1000,
    },
    resolve: {
        tsconfigPaths: true,
    },
    base: '/pokeguesser',
    plugins: [
        react(),
        tsconfigPaths(),
        visualizer({ open: true }),
        {
            name: 'html-inject-env',
            transformIndexHtml(html) {
                const base = 'PokeGuesser';
                const title = mode === 'production' ? base : `[DEV] ${base}`;
                return html.replace('%APP_TITLE%', title);
            },
        },
    ],
    server: {
        host: '0.0.0.0',
        port: 3001,
        open: false,
        watch: {
            usePolling: true,
            interval: 1000,
        },
        proxy: {
            '/pokeguesser/api/v1': {
                target: process.env.VITE_API_TARGET || 'http://localhost:8085',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/pokeguesser\/api\/v1/, '/api/v1'),
            },
        },
    },
}));
