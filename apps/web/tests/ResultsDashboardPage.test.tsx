import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ResultsDashboardPage } from '../src/pages/ResultsDashboardPage';

const mockAnalysisResult = {
  analysis_id: 'analysis-12345678',
  submission_document_id: 'sub-doc-1',
  submission_filename: 'submission.txt',
  mode: 'direct',
  status: 'completed',
  overall_lexical_coverage_percent: 75.4,
  overall_semantic_coverage_percent: 0.0,
  net_adjusted_score_percent: 75.4,
  matched_source_count: 1,
  total_findings_count: 2,
  created_at: '2026-10-14T12:00:00Z',
  completed_at: '2026-10-14T12:00:05Z',
  sources: [
    {
      reference_document_id: 'ref-doc-1',
      source_title: 'source_article.txt',
      matched_passage_count: 2,
      lexical_coverage_percent: 75.4,
      semantic_coverage_percent: 0.0,
    },
  ],
  findings: [
    {
      finding_id: 'find-1',
      category: 'exact_copy',
      confidence: 'high',
      submission_start_offset: 0,
      submission_end_offset: 108,
      submission_excerpt: 'Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn.',
      reference_document_id: 'ref-doc-1',
      reference_source_title: 'source_article.txt',
      reference_start_offset: 0,
      reference_end_offset: 108,
      reference_excerpt: 'Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn.',
      lexical_similarity: 1.0,
      semantic_similarity: 0.0,
      is_quoted: false,
      is_excluded: false,
    },
    {
      finding_id: 'find-2',
      category: 'near_exact_rewrite',
      confidence: 'high',
      submission_start_offset: 109,
      submission_end_offset: 198,
      submission_excerpt: 'Deep learning models use multiple layers to extract higher level features from raw input.',
      reference_document_id: 'ref-doc-1',
      reference_source_title: 'source_article.txt',
      reference_start_offset: 109,
      reference_end_offset: 207,
      reference_excerpt: 'Deep learning architectures use multiple layers to extract higher-level features from the raw input.',
      lexical_similarity: 0.88,
      semantic_similarity: 0.0,
      is_quoted: false,
      is_excluded: false,
    },
  ],
};

describe('ResultsDashboardPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/analyses/analysis-12345678/report')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockAnalysisResult,
        });
      }
      if (url.includes('/api/v1/analyses/analysis-12345678')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockAnalysisResult,
        });
      }
      if (url.includes('/api/v1/documents/sub-doc-1/text')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            document_id: 'sub-doc-1',
            filename: 'submission.txt',
            raw_text:
              'Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn. Deep learning models use multiple layers to extract higher level features from raw input.',
            char_count: 200,
            word_count: 32,
            detected_language: 'en',
          }),
        });
      }
      if (url.includes('/api/v1/documents/ref-doc-1/text')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            document_id: 'ref-doc-1',
            filename: 'source_article.txt',
            raw_text:
              'Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn. Deep learning architectures use multiple layers to extract higher-level features from the raw input.',
            char_count: 209,
            word_count: 31,
            detected_language: 'en',
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });
    });
  });

  it('renders overall similarity score and finding breakdown cards', async () => {
    const onBack = vi.fn();
    const onOpenHistory = vi.fn();

    render(
      <ResultsDashboardPage
        analysisId="analysis-12345678"
        onBackToIngestion={onBack}
        onOpenHistory={onOpenHistory}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Similarity Results')).toBeInTheDocument();
      expect(screen.getAllByText(/75\.4%/).length).toBeGreaterThan(0);
      expect(screen.getByText('Overall Evidence Coverage')).toBeInTheDocument();
      expect(screen.getAllByText(/source_article\.txt/).length).toBeGreaterThan(0);
    });
  });

  it('renders side-by-side submission and reference text panels', async () => {
    render(
      <ResultsDashboardPage
        analysisId="analysis-12345678"
        onBackToIngestion={vi.fn()}
        onOpenHistory={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Submission Text')).toBeInTheDocument();
      expect(screen.getByText(/Reference Source Text/)).toBeInTheDocument();
    });

    // Verify findings are listed
    expect(screen.getAllByText(/exact copy/i).length).toBeGreaterThan(0);
  });

  it('renders reviewer decision actions and report download options', async () => {
    render(
      <ResultsDashboardPage
        analysisId="analysis-12345678"
        onBackToIngestion={vi.fn()}
        onOpenHistory={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Keep \(Confirmed\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Exclude \(False Positive\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Quoted \/ Cited/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Needs Review/i).length).toBeGreaterThan(0);
      expect(screen.getByText('Download Report')).toBeInTheDocument();
    });

    // Toggle download report menu
    const downloadBtn = screen.getByText('Download Report');
    fireEvent.click(downloadBtn);

    expect(screen.getByText(/PDF Report \(Recommended\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Printable HTML/i)).toBeInTheDocument();
    expect(screen.getByText(/Export JSON/i)).toBeInTheDocument();
  });

  it('handles history button click', async () => {
    const onOpenHistory = vi.fn();

    render(
      <ResultsDashboardPage
        analysisId="analysis-12345678"
        onBackToIngestion={vi.fn()}
        onOpenHistory={onOpenHistory}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'History' })).toBeInTheDocument();
    });

    const historyBtn = screen.getByRole('button', { name: 'History' });
    fireEvent.click(historyBtn);
    expect(onOpenHistory).toHaveBeenCalled();
  });
});
