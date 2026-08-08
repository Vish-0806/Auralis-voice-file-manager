import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { ApiClient } from '../../src/services/api/client';
import { AuralisApiError } from '../../src/services/api/errors';
import { authService } from '../../src/services/auth/authService';

vi.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() }
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    }
  };
});

describe('ApiClient', () => {
  let client: ApiClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockAxiosInstance = axios.create();
    client = new ApiClient();
  });

  it('should initialize with correct default base URL', () => {
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: 'http://localhost:8000',
        timeout: 10000,
      })
    );
  });

  it('should format request configuration correctly', async () => {
    mockAxiosInstance.get.mockResolvedValue({ data: { status: 'ok' } });
    const res = await client.get('/health');
    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/health', undefined);
    expect(res).toEqual({ status: 'ok' });
  });

  it('should attach session authorization tokens', () => {
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    authService.loginPlaceholder('user@auralis.app', 'Tester');
    const mockConfig = { headers: {} as Record<string, string> };
    const resultConfig = requestInterceptor(mockConfig);
    expect(resultConfig.headers.Authorization).toBe('Bearer mock-session-token-phase-16-6');
    authService.logout();
  });

  it('should format API response errors to AuralisApiError objects', async () => {
    const responseInterceptorError = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
    const mockAxiosError = {
      config: { url: '/status' },
      response: {
        status: 400,
        data: { detail: 'Bad Request Parameter' }
      }
    };
    
    try {
      await responseInterceptorError(mockAxiosError);
      throw new Error('Should have failed');
    } catch (err: any) {
      expect(err).toBeInstanceOf(AuralisApiError);
      expect(err.status).toBe(400);
      expect(err.message).toBe('Bad Request Parameter');
      expect(err.path).toBe('/status');
    }
  });
});
