import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Stub matchesMedia for JSDOM
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Globally mock API services to avoid network requests in unit/integration tests
vi.mock('../src/services/api/assistantService', () => {
  return {
    assistantService: {
      getHealth: vi.fn().mockResolvedValue({
        status: 'ok',
        version: '2.0.0',
        timestamp: '2026-08-09T10:00:00Z'
      }),
      getStatus: vi.fn().mockResolvedValue({
        platform: {
          system: 'Windows',
          release: '11',
          version: '10.0.22000',
          machine: 'AMD64',
          python_version: '3.11.2'
        },
        loaded_capabilities: ['files', 'listener', 'voice'],
        assistant_status: 'ready'
      }),
      sendMessage: vi.fn(),
      sendTextCommand: vi.fn()
    }
  };
});

vi.mock('../src/services/api/filesService', () => {
  return {
    filesService: {
      searchFiles: vi.fn().mockResolvedValue([
        { name: 'document.txt', path: 'C:/Users/Vishal/Documents/document.txt', size: 1024, modified: '2026-08-09T10:00:00Z' },
        { name: 'photo.jpg', path: 'C:/Users/Vishal/Desktop/photo.jpg', size: 204800, modified: '2026-08-09T10:00:00Z' }
      ])
    }
  };
});
