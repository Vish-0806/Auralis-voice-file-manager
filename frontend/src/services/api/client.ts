import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { AuralisApiError } from './errors';
import { authService } from '../auth/authService';

export class ApiClient {
  private instance: AxiosInstance;

  constructor(config?: AxiosRequestConfig) {
    const defaultBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    
    this.instance = axios.create({
      baseURL: defaultBaseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
      ...config,
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request Interceptor: Attach bearer token if user is authenticated
    this.instance.interceptors.request.use(
      (config) => {
        const token = authService.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response Interceptor: Translate failures into normalized AuralisApiError
    this.instance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  private normalizeError(error: AxiosError): AuralisApiError {
    const path = error.config?.url;
    
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as Record<string, unknown> | undefined;
      const message = (data?.detail as string) || (data?.message as string) || error.message || 'Server error';
      const code = (data?.code as string) || `HTTP_${status}`;
      return new AuralisApiError(message, status, code, data?.details || data, path);
    }
    
    if (error.request) {
      return new AuralisApiError(
        'No response received from the backend server. Verify your connection.',
        undefined,
        'NETWORK_ERROR',
        undefined,
        path
      );
    }
    
    return new AuralisApiError(
      error.message || 'Request configuration failure',
      undefined,
      'REQUEST_SETUP_ERROR',
      undefined,
      path
    );
  }

  public async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  public async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  public async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  public async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
