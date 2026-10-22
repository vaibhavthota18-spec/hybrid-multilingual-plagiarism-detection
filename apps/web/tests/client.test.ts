import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiFetch, ApiClientError } from '../src/lib/api/client';

describe('ApiClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('injects X-Request-ID and Accept headers automatically', async () => {
    const mockResponse = { status: 'healthy', timestamp: '2026-10-14T10:00:00Z' };
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse,
    });
    global.fetch = fetchSpy;

    const result = await apiFetch('/api/v1/health');

    expect(result).toEqual(mockResponse);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const calledHeaders = fetchSpy.mock.calls[0][1].headers as Headers;
    expect(calledHeaders.get('Accept')).toBe('application/json');
    expect(calledHeaders.get('X-Request-ID')).toMatch(/^web-\d+-[a-z0-9]+$/);
  });

  it('injects Bearer token when present in localStorage', async () => {
    localStorage.setItem('auth_token', 'jwt-test-token-value');
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ status: 'authenticated' }),
    });
    global.fetch = fetchSpy;

    await apiFetch('/api/v1/auth/me');

    const calledHeaders = fetchSpy.mock.calls[0][1].headers as Headers;
    expect(calledHeaders.get('Authorization')).toBe('Bearer jwt-test-token-value');
  });

  it('parses RFC 7807 ErrorEnvelope into ApiClientError on failure', async () => {
    const errorPayload = {
      error: {
        code: 'NOT_FOUND',
        message: 'The requested document does not exist',
        status: 404,
        request_id: 'req-err-999',
      },
    };
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => errorPayload,
    });
    global.fetch = fetchSpy;

    await expect(apiFetch('/api/v1/documents/missing-uuid')).rejects.toThrow(ApiClientError);

    try {
      await apiFetch('/api/v1/documents/missing-uuid');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiClientError);
      expect(err.code).toBe('NOT_FOUND');
      expect(err.status).toBe(404);
      expect(err.message).toBe('The requested document does not exist');
      expect(err.requestId).toBe('req-err-999');
    }
  });
});
