import { defineConfig } from '@playwright/test'
const python = process.env.DOMI_PYTHON || 'python'
export default defineConfig({
  testDir: './tests/e2e', fullyParallel: false, workers: 1, timeout: 30000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:5173', browserName: 'chromium', viewport: { width: 1365, height: 900 },
    launchOptions: process.env.DOMI_CHROMIUM ? { executablePath: process.env.DOMI_CHROMIUM } : {},
    screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: [
    { command: `"${python}" ../backend/orders/tests/e2e_server.py`, url: 'http://127.0.0.1:8000/api/categories/', reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev -- --host 127.0.0.1', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 60000 },
  ],
})
