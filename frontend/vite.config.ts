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
        port: 3001,
        open: false,
        proxy: {
            '/pokeguesser/api/v1': {
                target: 'http://localhost:8085',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/pokeguesser\/api\/v1/, '/api/v1'),
            },
        },
    },
});
