import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AnalysisHistoryPage } from '../src/pages/AnalysisHistoryPage';

const mockAnalysesList = {
  items: [
    {
      analysis_id: 'ana-test-11111111',
      submission_document_id: 'sub-test-doc',
      submission_filename: 'thesis_candidate.pdf',
      mode: 'direct',
      lexical_coverage: 42.5,
      semantic_coverage: 0.0,
      net_score: 42.5,
      matched_source_count: 1,
      total_findings_count: 3,
      status: 'completed',
      created_at: '2026-10-14T11:30:00Z',
    },
    {
      analysis_id: 'ana-test-22222222',
      submission_document_id: 'sub-test-doc-2',
      submission_filename: 'essay_candidate.docx',
      mode: 'corpus',
      lexical_coverage: 0.0,
      semantic_coverage: 0.0,
      net_score: 0.0,
      matched_source_count: 0,
      total_findings_count: 0,
      status: 'completed',
      created_at: '2026-10-14T11:45:00Z',
    },
  ],
  pagination: {
    total: 2,
    limit: 50,
    offset: 0,
  },
};

describe('AnalysisHistoryPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/analyses')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockAnalysesList,
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ items: [] }),
      });
    });
  });

  it('renders list of similarity analyses with scores and badges', async () => {
    const onSelect = vi.fn();
    const onNavigateIngestion = vi.fn();

    render(
      <AnalysisHistoryPage
        onSelectAnalysis={onSelect}
        onNavigateToIngestion={onNavigateIngestion}
      />
    );

    expect(screen.getByRole('heading', { name: 'Analysis History' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('thesis_candidate.pdf')).toBeInTheDocument();
      expect(screen.getByText('essay_candidate.docx')).toBeInTheDocument();
      expect(screen.getAllByText(/42\.5%/).length).toBeGreaterThan(0);
      expect(screen.getByText('3 matches')).toBeInTheDocument();
    });
  });

  it('triggers onSelectAnalysis when View Results button is clicked', async () => {
    const onSelect = vi.fn();
    const onNavigateIngestion = vi.fn();

    render(
      <AnalysisHistoryPage
        onSelectAnalysis={onSelect}
        onNavigateToIngestion={onNavigateIngestion}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByText('View Results').length).toBeGreaterThan(0);
    });

    const viewButtons = screen.getAllByText('View Results');
    fireEvent.click(viewButtons[0]);

    expect(onSelect).toHaveBeenCalledWith('ana-test-11111111');
  });

  it('toggles quick run analysis drawer when button is clicked', async () => {
    render(
      <AnalysisHistoryPage
        onSelectAnalysis={vi.fn()}
        onNavigateToIngestion={vi.fn()}
      />
    );

    const runBtn = screen.getByRole('button', { name: /Run Analysis/i });
    fireEvent.click(runBtn);

    expect(screen.getByText('Execute Similarity Analysis')).toBeInTheDocument();
    expect(screen.getByText(/Submission Document \*/i)).toBeInTheDocument();
    expect(screen.getByText(/Reference Document \*/i)).toBeInTheDocument();
  });
});
