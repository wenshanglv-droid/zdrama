import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [
    { command: `${process.env.E2E_PYTHON || '../.venv/bin/python'} ../scripts/e2e_server.py`, url: 'http://127.0.0.1:8000/api/session/', reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 60000 }
  ]
})
