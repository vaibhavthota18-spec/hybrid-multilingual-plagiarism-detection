import { ErrorEnvelope } from '../../types/generated/api';

export class ApiClientError extends Error {
  public status: number;
  public code: string;
  public requestId?: string;
  public details?: any[];

  constructor(status: number, code: string, message: string, requestId?: string, details?: any[]) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '';

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Inject correlation request ID if not provided
  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', `web-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`);
  }

  // Inject Bearer token if user is authenticated
  const token = localStorage.getItem('auth_token');
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  if (!response.ok) {
    if (isJson) {
      try {
        const errorData = (await response.json()) as ErrorEnvelope;
        if (errorData.error) {
          throw new ApiClientError(
            errorData.error.status || response.status,
            errorData.error.code || 'API_ERROR',
            errorData.error.message || 'An unexpected API error occurred',
            errorData.error.request_id,
            errorData.error.details
          );
        }
      } catch (err) {
        if (err instanceof ApiClientError) throw err;
      }
    }
    throw new ApiClientError(
      response.status,
      'HTTP_ERROR',
      `HTTP request failed with status ${response.status}: ${response.statusText}`
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}
