import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

export class ApiClient {
  private instance: AxiosInstance;

  constructor(config?: AxiosRequestConfig) {
    const defaultBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
    
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
    this.instance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  private normalizeError(error: AxiosError): ApiError {
    if (error.response) {
      // The server responded with a status code outside the 2xx range
      const data = error.response.data as Record<string, unknown> | undefined;
      return {
        message: (data?.message as string) || error.message || 'An error occurred during communication',
        status: error.response.status,
        code: (data?.code as string) || 'SERVER_ERROR',
        details: data?.details || data,
      };
    } else if (error.request) {
      // The request was made but no response was received
      return {
        message: 'No response received from the backend server. Verify your connection.',
        code: 'NETWORK_ERROR',
      };
    } else {
      // Something happened in setting up the request that triggered an Error
      return {
        message: error.message || 'Request setup failure occurred',
        code: 'REQUEST_SETUP_ERROR',
      };
    }
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
