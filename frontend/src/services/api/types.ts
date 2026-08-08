export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: unknown;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
}
