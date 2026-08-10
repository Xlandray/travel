import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: 1,
  // Claude ajanının logları analiz edebilmesi için JSON çıktısı zorunludur
  reporter: [
    ['list'],
    ['json', { outputFile: 'agent-report/test-results.json' }]
  ], 
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000', // Armonitex Vitrini
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
