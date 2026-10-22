import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import IngestionPage from '../src/pages/IngestionPage';

describe('IngestionPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string, options?: any) => {
      const isGet = !options?.method || options.method === 'GET';
      if (url.includes('/api/v1/documents') && isGet) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            items: [
              {
                document_id: 'doc-mock-1',
                filename: 'sample_thesis.pdf',
                mime_type: 'application/pdf',
                sha256_hash: 'hash123',
                file_size_bytes: 20480,
                page_count: 5,
                char_count: 4500,
                word_count: 750,
                detected_language: 'en',
                status: 'completed',
                created_at: '2026-10-14T10:00:00Z',
              },
              {
                document_id: 'doc-mock-2',
                filename: 'hindi_paper.txt',
                mime_type: 'text/plain',
                sha256_hash: 'hash456',
                file_size_bytes: 1024,
                page_count: 1,
                char_count: 600,
                word_count: 120,
                detected_language: 'hi',
                status: 'completed',
                created_at: '2026-10-14T10:05:00Z',
              },
            ],
            pagination: { total_items: 2, limit: 100, offset: 0, has_more: false },
          }),
        });
      }
      if (url.includes('/api/v1/collections') && isGet) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            items: [
              {
                collection_id: 'col-mock-1',
                name: 'Standard NLP Benchmarks',
                description: 'Corpus collection',
                document_count: 2,
                is_public_within_tenant: false,
                created_at: '2026-10-14T09:00:00Z',
              },
            ],
            pagination: { total_items: 1, limit: 100, offset: 0, has_more: false },
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

  it('renders page header and format guidance', async () => {
    render(<IngestionPage />);

    expect(screen.getByText('Document Ingestion & Reference Corpus')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop source documents here/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, DOCX, and TXT/i)).toBeInTheDocument();
  });

  it('switches to Document Library and renders mock documents', async () => {
    render(<IngestionPage />);

    const libraryTab = screen.getByText(/Document Library/i);
    fireEvent.click(libraryTab);

    await waitFor(() => {
      expect(screen.getByText('sample_thesis.pdf')).toBeInTheDocument();
      expect(screen.getByText('hindi_paper.txt')).toBeInTheDocument();
      expect(screen.getByText('EN')).toBeInTheDocument();
      expect(screen.getByText('HI')).toBeInTheDocument();
    });
  });

  it('switches to Reference Collections and displays collection card', async () => {
    render(<IngestionPage />);

    const collectionsTab = screen.getByText(/Reference Collections/i);
    fireEvent.click(collectionsTab);

    await waitFor(() => {
      expect(screen.getByText('Standard NLP Benchmarks')).toBeInTheDocument();
      expect(screen.getByText('2 doc(s)')).toBeInTheDocument();
    });
  });

  it('switches to Comparison Setup and validates comparison inputs', async () => {
    render(<IngestionPage />);

    const compTab = screen.getByText('Comparison Setup');
    fireEvent.click(compTab);

    expect(screen.getByText(/Comparison Input Validation & Analysis Preparation/i)).toBeInTheDocument();
    expect(screen.getByText('1. Direct Comparison (1:1)')).toBeInTheDocument();
    expect(screen.getByText('2. One-to-Many (1:N)')).toBeInTheDocument();
    expect(screen.getByText('3. Corpus Search (1:Collection)')).toBeInTheDocument();
  });
});
