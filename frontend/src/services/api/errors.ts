export class AuralisApiError extends Error {
  public readonly status?: number;
  public readonly code?: string;
  public readonly details?: unknown;
  public readonly path?: string;

  constructor(message: string, status?: number, code?: string, details?: unknown, path?: string) {
    super(message);
    this.name = 'AuralisApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.path = path;
  }
}

export const isAuralisApiError = (error: unknown): error is AuralisApiError => {
  return error instanceof AuralisApiError;
};
