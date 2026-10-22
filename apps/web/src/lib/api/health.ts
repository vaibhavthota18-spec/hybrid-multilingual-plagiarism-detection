import { apiFetch } from './client';
import { HealthStatus } from '../../types/generated/api';

/**
 * Fetches the current operational and readiness status of the backend API
 * and underlying infrastructure (PostgreSQL, Redis, Worker Pool).
 */
export async function fetchHealthStatus(): Promise<HealthStatus> {
  return await apiFetch<HealthStatus>('/api/v1/health');
}
