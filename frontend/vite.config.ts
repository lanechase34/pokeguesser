import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
    build: {
        outDir: 'build',
    },
    base: '/pokeguesser',
    plugins: [react(), tsconfigPaths(), visualizer({ open: true })],
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
});
