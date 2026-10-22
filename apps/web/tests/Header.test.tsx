import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../src/components/Header';

describe('Header Component', () => {
  it('renders application branding without engineering badges', () => {
    render(<Header />);

    expect(screen.getByText('Plagiarism Engine')).toBeInTheDocument();
    expect(
      screen.getByText(/Multilingual Similarity Detection \(English • Hindi • Telugu\)/i)
    ).toBeInTheDocument();

    // Verify engineering badges are removed from normal user header
    expect(screen.queryByText(/Phase 1 Foundation/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Backend Healthy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/OpenAPI Docs/i)).not.toBeInTheDocument();
  });

  it('calls onNavigateHome when clicking branding', () => {
    const onNavigateHome = vi.fn();
    render(<Header onNavigateHome={onNavigateHome} />);

    const brand = screen.getByText('Plagiarism Engine');
    fireEvent.click(brand);

    expect(onNavigateHome).toHaveBeenCalledTimes(1);
  });
});
