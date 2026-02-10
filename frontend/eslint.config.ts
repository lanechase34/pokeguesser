import eslint from '@eslint/js';
import eslintReact from '@eslint-react/eslint-plugin';
import reactHooks from 'eslint-plugin-react-hooks';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';
import importPlugin from 'eslint-plugin-import';
import jsxA11y from 'eslint-plugin-jsx-a11y';

export default defineConfig([
    {
        // Global ignores
        ignores: [
            '**/node_modules/**',
            '**/build/**',
            '**/dist/**',
            '**/coverage/**',
            '**/.vite/**',
            'eslint.config.ts',
            'jest.config.cjs',
            'vite.config.ts',
            'vite.config.js',
        ],
    },

    // Base configurations
    eslint.configs.recommended,
    ...tseslint.configs.recommendedTypeChecked,
    ...tseslint.configs.stylisticTypeChecked,
    jsxA11y.flatConfigs.recommended,

    // React configurations
    eslintReact.configs['recommended-typescript'],
    reactHooks.configs.flat.recommended,

    // Import/Export organization
    importPlugin.flatConfigs.recommended,
    importPlugin.flatConfigs.typescript,

    // Project-specific configurations
    {
        files: ['**/*.ts', '**/*.tsx'],
        languageOptions: {
            parser: tseslint.parser,
            parserOptions: {
                project: './tsconfig.json',
                tsconfigRootDir: import.meta.dirname,
                ecmaVersion: 'latest',
                sourceType: 'module',
            },
        },
        settings: {
            'import/resolver': {
                typescript: {
                    alwaysTryTypes: true,
                    project: './tsconfig.json',
                },
            },
            react: {
                version: 'detect',
            },
        },
        rules: {
            '@typescript-eslint/no-unused-vars': [
                'error',
                {
                    argsIgnorePattern: '^_',
                    varsIgnorePattern: '^_',
                    caughtErrorsIgnorePattern: '^_',
                },
            ],
            '@eslint-react/no-use-context': 'off',
            '@eslint-react/hooks-extra/no-direct-set-state-in-use-effect': 'off',
        },
    },
]);
