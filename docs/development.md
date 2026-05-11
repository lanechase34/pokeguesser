# Development Guide

This document covers developer workflows including dependency updates, formatting, and testing for both frontend and backend services.

## Updates

### NPM Updates

1. Check for updates

    ```bash
    ncu
    ```

2. Update `package.json` file

    ```bash
    ncu -u
    ```

3. Install new packages

    ```bash
    npm install
    ```

4. (Optional) Run audit on prod dependencies

    ```bash
    audit:prod
    ```

### PIP Updates

1. Check for updates

    ```bash
    pur -r requirements.txt -d
    ```
2. Update `requirements.txt` and `requirements-dev.txt` file(s)

    ```bash
    pur -r requirements.txt
    pur -r requirements-dev.txt
    ```

3. Install new dependencies

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

## Code Formatting

### Frontend

1. Format `.ts`, `.tsx` files using Prettier by running

    ```bash
    npm run format

    OR

    Ctrl+Shift+P -> Run Task -> Format Frontend
    ```

### Backend

1. Format `.py` files using Ruff by running

    ```bash
    ruff format .

    OR

    Ctrl+Shift+P -> Run Task -> Format Backend
    ```

## Code Linting

### Frontend

1. Make sure vscode can resolve `eslint.config.ts`

2. Lint `.ts`, `.tsx` files by running

    ```bash
    npm run lint

    OR

    Ctrl+Shift+P -> Run Task -> Lint Frontend
    ```

### Backend

1. Lint `.py` files using Ruff by running

    ```bash
    ruff check . --fix

    OR

    Ctrl+Shift+P -> Run Task -> Lint Backend
    ```

## Type Checking

### Frontend

1. Typecheck `.ts`, `.tsx` files by running

    ```bash
    npm run typecheck

    OR

    Ctrl+Shift+P -> Run Task -> Typecheck Frontend
    ```

### Backend

1. Typecheck `.py` files by running

    ```bash
    Ctrl+Shift+P -> Run Task -> Typecheck Backend
    ```

## Testing

### Frontend

1. Run Jest Suite using vscode extension or running

    ```bash
    npm run test
    ```

2. Check test coverage by running

    ```bash
    npm run testcoverage
    ```

### Backend

Tests should be organized in a tests/ directory with each test being named `${name}\_test.py`

Tests will be ran locally and connect to the docker containers

The test database will automatically be created as `test_pokeguesser`

1. Prerequisites

    Set up `.env.test` file

    ```bash
    cp docker/.env.test.example backend/.env.test
    ```

2. Run PyTest suite using vscode extension


## GitHooks

Formatting, linting, and typechecking occurs for both Frontend and Backend on every commit

Test pre-commit GitHook by running from the root

```bash
lefthook run pre-commit
```