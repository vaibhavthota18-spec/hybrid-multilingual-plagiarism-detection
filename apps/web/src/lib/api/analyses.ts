/**
 * Analysis API Client
 * Typed client for Phase 3 Lexical Plagiarism Detection endpoints
 */

import { apiFetch } from './client';
import {
  CreateAnalysisRequest,
  AnalysisJobStatus,
  AnalysisResult,
  SimilarityFinding,
  PaginatedAnalyses,
  ModelInfo,
} from '../../types/generated/api';

export const analysesApi = {
  /**
   * Retrieve active dense semantic embedding model info
   */
  getModelInfo: async (): Promise<ModelInfo> => {
    return apiFetch<ModelInfo>('/api/v1/analyses/models/info');
  },

  /**
   * Create and enqueue similarity analysis
   */
  createAnalysis: async (req: CreateAnalysisRequest, syncProcessing: boolean = false): Promise<AnalysisJobStatus> => {
    return apiFetch<AnalysisJobStatus>(`/api/v1/analyses?sync_processing=${syncProcessing}`, {
      method: 'POST',
      body: JSON.stringify(req),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },

  /**
   * Poll analysis job progress and status
   */
  getAnalysisStatus: async (analysisId: string): Promise<AnalysisJobStatus> => {
    return apiFetch<AnalysisJobStatus>(`/api/v1/analyses/${analysisId}/status`);
  },

  /**
   * Retrieve full analysis results and findings
   */
  getAnalysisResult: async (analysisId: string): Promise<AnalysisResult> => {
    return apiFetch<AnalysisResult>(`/api/v1/analyses/${analysisId}`);
  },

  /**
   * Retrieve exportable analysis report
   */
  getAnalysisReport: async (analysisId: string): Promise<AnalysisResult> => {
    return apiFetch<AnalysisResult>(`/api/v1/analyses/${analysisId}/report`);
  },

  /**
   * Submit human reviewer decision and notes on a finding
   */
  reviewFinding: async (
    analysisId: string,
    findingId: string,
    decision: 'keep' | 'exclude' | 'quoted_cited' | 'needs_review' | 'unreviewed',
    notes?: string
  ): Promise<import('../../types/generated/api').ReviewFindingResponse> => {
    return apiFetch<import('../../types/generated/api').ReviewFindingResponse>(
      `/api/v1/analyses/${analysisId}/findings/${findingId}/review`,
      {
        method: 'PATCH',
        body: JSON.stringify({ decision, notes }),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  },

  /**
   * Download report helper URL
   */
  downloadReportUrl: (analysisId: string, format: 'pdf' | 'html' | 'json' = 'pdf'): string => {
    return `/api/v1/analyses/${analysisId}/report?format=${format}`;
  },

  /**
   * List user analyses history
   */
  listAnalyses: async (limit: number = 50, offset: number = 0): Promise<PaginatedAnalyses> => {
    return apiFetch<PaginatedAnalyses>(`/api/v1/analyses?limit=${limit}&offset=${offset}`);
  },

  /**
   * Retrieve findings for an analysis
   */
  getAnalysisFindings: async (analysisId: string): Promise<SimilarityFinding[]> => {
    return apiFetch<SimilarityFinding[]>(`/api/v1/analyses/${analysisId}/findings`);
  },

  /**
   * Cancel an in-progress analysis job
   */
  cancelAnalysis: async (analysisId: string): Promise<AnalysisJobStatus> => {
    return apiFetch<AnalysisJobStatus>(`/api/v1/analyses/${analysisId}/cancel`, {
      method: 'POST',
    });
  },

  /**
   * Delete an analysis record and associated findings
   */
  deleteAnalysis: async (analysisId: string): Promise<void> => {
    return apiFetch<void>(`/api/v1/analyses/${analysisId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Helper to poll an analysis job until it reaches completed or failed
   */
  pollAnalysisUntilComplete: async (
    analysisId: string,
    onProgress?: (status: AnalysisJobStatus) => void,
    intervalMs: number = 1000,
    maxAttempts: number = 60
  ): Promise<AnalysisResult> => {
    let attempts = 0;
    while (attempts < maxAttempts) {
      const status = await analysesApi.getAnalysisStatus(analysisId);
      if (onProgress) {
        onProgress(status);
      }
      if (status.status === 'completed') {
        return await analysesApi.getAnalysisResult(analysisId);
      }
      if (status.status === 'failed' || status.status === 'cancelled') {
        throw new Error(status.error_message || `Analysis ${status.status}`);
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
      attempts++;
    }
    throw new Error('Analysis timed out waiting for completion.');
  },
};
