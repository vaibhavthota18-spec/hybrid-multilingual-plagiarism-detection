import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowPage } from '../src/pages/WorkflowPage';

describe('WorkflowPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string, options?: any) => {
      if (url.includes('/api/v1/documents') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 201,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            document_id: 'doc-uploaded-1',
            filename: 'test_essay.pdf',
            mime_type: 'application/pdf',
            sha256_hash: 'hash123',
            file_size_bytes: 15000,
            page_count: 3,
            char_count: 2400,
            word_count: 380,
            detected_language: 'en',
            status: 'completed',
            created_at: '2026-10-14T12:00:00Z',
          }),
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

  it('renders clean upload homepage and supported formats', () => {
    render(
      <WorkflowPage
        onSelectAnalysis={vi.fn()}
        onNavigateToLibrary={vi.fn()}
        onNavigateToHistory={vi.fn()}
      />
    );

    expect(screen.getByText('Check Document Similarity')).toBeInTheDocument();
    expect(screen.getByText(/Upload a document, compare it with your references, and review matching passages./i)).toBeInTheDocument();
    expect(screen.getByText('Select Document')).toBeInTheDocument();
    expect(screen.getByText(/Drop your document here/i)).toBeInTheDocument();
    expect(screen.getByText(/English • Hindi • Telugu/i)).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('DOCX')).toBeInTheDocument();
    expect(screen.getByText('TXT')).toBeInTheDocument();
    expect(screen.getByText(/Up to 32 MB/i)).toBeInTheDocument();
    expect(screen.getByText('My Documents')).toBeInTheDocument();
    expect(screen.getByText('View History')).toBeInTheDocument();
  });
});
