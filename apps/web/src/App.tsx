import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';
import { WorkflowPage } from './pages/WorkflowPage';
import { MyDocumentsPage } from './pages/MyDocumentsPage';
import { AnalysisHistoryPage } from './pages/AnalysisHistoryPage';
import { ResultsDashboardPage } from './pages/ResultsDashboardPage';
import { DeveloperDiagnosticsPage } from './pages/DeveloperDiagnosticsPage';
import { HealthStatus, DocumentMetadata } from './types/generated/api';
import { fetchHealthStatus } from './lib/api/health';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<string>('home');
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [activeSubmissionDoc, setActiveSubmissionDoc] = useState<DocumentMetadata | null>(null);

  const loadHealth = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchHealthStatus();
      setHealth(data);
    } catch {
      setHealth({
        status: 'degraded',
        timestamp: new Date().toISOString(),
        database: 'disconnected',
        redis: 'disconnected',
        worker_pool: 'degraded',
        version: '1.0.0',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  // Handle URL hash or query params for direct tab navigation
  useEffect(() => {
    const hash = window.location.hash;
    if (hash === '#diagnostics' || window.location.search.includes('dev=true')) {
      setActiveTab('diagnostics');
    } else if (hash === '#documents') {
      setActiveTab('documents');
    } else if (hash === '#history') {
      setActiveTab('history');
    }
  }, []);

  const handleSelectAnalysis = (id: string) => {
    setSelectedAnalysisId(id);
    setActiveTab('results');
  };

  const handleUseDocumentInComparison = (doc: DocumentMetadata) => {
    setActiveSubmissionDoc(doc);
    setSelectedAnalysisId(null);
    setActiveTab('home');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <Header
        health={health}
        loading={loading}
        onRefresh={loadHealth}
        onNavigateHome={() => {
          setSelectedAnalysisId(null);
          setActiveSubmissionDoc(null);
          setActiveTab('home');
        }}
      />

      {activeTab !== 'diagnostics' && (
        <Navigation
          activeTab={activeTab === 'results' ? 'history' : activeTab}
          setActiveTab={(tab) => {
            if (tab === 'home') {
              setActiveSubmissionDoc(null);
              setSelectedAnalysisId(null);
            }
            setActiveTab(tab);
          }}
        />
      )}

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {activeTab === 'home' && (
          <WorkflowPage
            onSelectAnalysis={handleSelectAnalysis}
            onNavigateToLibrary={() => setActiveTab('documents')}
            onNavigateToHistory={() => setActiveTab('history')}
            initialSubmissionDoc={activeSubmissionDoc}
          />
        )}

        {activeTab === 'documents' && (
          <MyDocumentsPage
            onUseDocumentInComparison={handleUseDocumentInComparison}
          />
        )}

        {activeTab === 'history' && (
          <AnalysisHistoryPage
            onSelectAnalysis={handleSelectAnalysis}
            onNavigateToIngestion={() => {
              setActiveSubmissionDoc(null);
              setSelectedAnalysisId(null);
              setActiveTab('home');
            }}
          />
        )}

        {activeTab === 'results' && selectedAnalysisId && (
          <ResultsDashboardPage
            analysisId={selectedAnalysisId}
            onBackToIngestion={() => {
              setActiveSubmissionDoc(null);
              setSelectedAnalysisId(null);
              setActiveTab('home');
            }}
            onOpenHistory={() => {
              setSelectedAnalysisId(null);
              setActiveTab('history');
            }}
          />
        )}

        {activeTab === 'diagnostics' && (
          <DeveloperDiagnosticsPage
            health={health}
            loading={loading}
            onRefresh={loadHealth}
            onBackToApp={() => setActiveTab('home')}
          />
        )}
      </main>

      <Footer
        onOpenDiagnostics={() => setActiveTab('diagnostics')}
      />
    </div>
  );
};

export default App;
