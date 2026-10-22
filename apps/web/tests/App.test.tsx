import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import App from '../src/App';

describe('App Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/health')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            status: 'healthy',
            timestamp: '2026-10-15T10:00:00Z',
            database: 'connected',
            redis: 'connected',
            worker_pool: 'operational',
            version: '1.0.0',
          }),
        });
      }
      if (url.includes('/api/v1/documents')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            items: [],
            pagination: { total_items: 0, limit: 50, offset: 0, total_pages: 0, current_page: 1 },
          }),
        });
      }
      if (url.includes('/api/v1/analyses')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            items: [],
            pagination: { total_items: 0, limit: 50, offset: 0, total_pages: 0, current_page: 1 },
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

  it('renders clean upload-first homepage and 3-tab navigation', async () => {
    render(<App />);

    // Brand and subtitle
    expect(screen.getAllByText('Plagiarism Engine').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Multilingual Similarity Detection \(English • Hindi • Telugu\)/i).length).toBeGreaterThan(0);

    // 3 clean navigation tabs
    const nav = screen.getByRole('navigation');
    expect(within(nav).getByText('Home')).toBeInTheDocument();
    expect(within(nav).getByText('My Documents')).toBeInTheDocument();
    expect(within(nav).getByText('History')).toBeInTheDocument();

    // Verification: Homepage is default view
    expect(screen.getByText('Check Document Similarity')).toBeInTheDocument();
    expect(screen.getByText('Select Document')).toBeInTheDocument();

    // Verification: Engineering badges and old phase roadmap removed from consumer view
    expect(screen.queryByText('Phase 1 Foundation')).not.toBeInTheDocument();
    expect(screen.queryByText('Backend Healthy')).not.toBeInTheDocument();
    expect(screen.queryByText('Infrastructure & Health')).not.toBeInTheDocument();
    expect(screen.queryByText('Corpus Search')).not.toBeInTheDocument();
    expect(screen.queryByText('Eight-Phase Development Roadmap Status')).not.toBeInTheDocument();
  });

  it('switches between Home, My Documents, and History tabs smoothly', async () => {
    render(<App />);

    const nav = screen.getByRole('navigation');

    // Click My Documents tab
    const myDocsTab = within(nav).getByText('My Documents');
    fireEvent.click(myDocsTab);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'My Documents' })).toBeInTheDocument();
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });

    // Click History tab
    const historyTab = within(nav).getByText('History');
    fireEvent.click(historyTab);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Analysis History' })).toBeInTheDocument();
    });

    // Click Home tab
    const homeTab = within(nav).getByText('Home');
    fireEvent.click(homeTab);

    await waitFor(() => {
      expect(screen.getByText('Check Document Similarity')).toBeInTheDocument();
    });
  });

  it('allows accessing developer diagnostics via footer without polluting user navigation', async () => {
    render(<App />);

    const diagButton = screen.getByRole('button', { name: /System Diagnostics/i });
    expect(diagButton).toBeInTheDocument();

    fireEvent.click(diagButton);

    await waitFor(() => {
      expect(screen.getByText(/System Infrastructure & Health Console/i)).toBeInTheDocument();
      expect(screen.getByText(/Back to Main Application/i)).toBeInTheDocument();
    });

    // Return to main app
    const backButton = screen.getByText(/Back to Main Application/i);
    fireEvent.click(backButton);

    await waitFor(() => {
      expect(screen.getByText('Check Document Similarity')).toBeInTheDocument();
    });
  });
});
