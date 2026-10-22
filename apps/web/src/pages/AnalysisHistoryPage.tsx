import React, { useEffect, useState, useCallback } from 'react';
import {
  History,
  RefreshCw,
  Search,
  Play,
  Trash2,
  Filter,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import {
  AnalysisSummary,
  DocumentMetadata,
} from '../types/generated/api';
import { analysesApi } from '../lib/api/analyses';
import { documentsApi } from '../lib/api/documents';

interface AnalysisHistoryPageProps {
  onSelectAnalysis: (analysisId: string) => void;
  onNavigateToIngestion: () => void;
}

export const AnalysisHistoryPage: React.FC<AnalysisHistoryPageProps> = ({
  onSelectAnalysis,
  onNavigateToIngestion,
}) => {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Quick Run Drawer
  const [showQuickRun, setShowQuickRun] = useState<boolean>(false);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [submissionId, setSubmissionId] = useState<string>('');
  const [referenceId, setReferenceId] = useState<string>('');
  const [quickDetectionMode, setQuickDetectionMode] = useState<'hybrid' | 'lexical' | 'semantic'>('hybrid');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runProgressMsg, setRunProgressMsg] = useState<string>('');

  const loadAnalyses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await analysesApi.listAnalyses(50, 0);
      setAnalyses(res.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch analysis history.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadDocs = useCallback(async () => {
    try {
      const docsRes = await documentsApi.listDocuments(100, 0);
      setDocuments(docsRes.items || []);
    } catch (err) {
      console.error('Failed to load documents for quick analysis', err);
    }
  }, []);

  useEffect(() => {
    loadAnalyses();
  }, [loadAnalyses]);

  useEffect(() => {
    if (showQuickRun) {
      loadDocs();
    }
  }, [showQuickRun, loadDocs]);

  const handleDelete = async (analysisId: string) => {
    if (!window.confirm('Are you sure you want to delete this analysis report?')) {
      return;
    }
    try {
      await analysesApi.deleteAnalysis(analysisId);
      setAnalyses((prev) => prev.filter((a) => a.analysis_id !== analysisId));
    } catch (err: any) {
      alert(`Failed to delete analysis: ${err.message}`);
    }
  };

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!referenceId) {
      alert('Please select a reference document.');
      return;
    }

    const payload: any = {
      submission_document_id: submissionId,
      detection_mode: quickDetectionMode,
      mode: 'direct',
      reference_document_id: referenceId,
    };

    setIsRunning(true);
    setRunProgressMsg('Submitting analysis...');

    try {
      const res = await analysesApi.createAnalysis(payload);
      setRunProgressMsg('Processing similarity...');
      const completed = await analysesApi.pollAnalysisUntilComplete(
        res.analysis_id,
        (status) => {
          if (status.current_step) setRunProgressMsg(status.current_step.replace('_', ' '));
        },
        1000,
        120
      );

      setIsRunning(false);
      setShowQuickRun(false);
      onSelectAnalysis(completed.analysis_id);
    } catch (err: any) {
      setIsRunning(false);
      alert(`Analysis failed: ${err.message}`);
    }
  };

  const filteredAnalyses = analyses.filter((a) => {
    const matchesStatus = statusFilter === 'all' || a.status === statusFilter;
    const q = searchQuery.toLowerCase();
    const docName = a.submission_filename || a.submission_document_id || '';
    const matchesSearch =
      docName.toLowerCase().includes(q) ||
      a.analysis_id.toLowerCase().includes(q) ||
      (a.detection_mode && a.detection_mode.toLowerCase().includes(q));
    return matchesStatus && matchesSearch;
  });

  const getModeLabel = (mode?: string) => {
    switch (mode) {
      case 'lexical':
        return 'Exact Text';
      case 'semantic':
        return 'Meaning-Based';
      default:
        return 'Hybrid AI';
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Analysis History</h1>
          <p className="text-xs text-slate-500 mt-1">
            Review previous similarity reports, inspect matching evidence, and export audit documents.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => setShowQuickRun(!showQuickRun)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center space-x-1.5"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run Analysis</span>
          </button>
          <button
            onClick={loadAnalyses}
            disabled={isLoading}
            className="p-2 text-slate-500 hover:text-slate-800 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition"
            title="Refresh History"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Quick Run Drawer */}
      {showQuickRun && (
        <div className="p-6 bg-white border border-indigo-200 rounded-2xl shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2 text-indigo-600">
              <Play className="w-4 h-4 fill-current" />
              <h3 className="text-sm font-bold text-slate-900">Execute Similarity Analysis</h3>
            </div>
            <button
              onClick={() => setShowQuickRun(false)}
              className="text-slate-400 hover:text-slate-600 text-sm px-2 py-1"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleStartAnalysis} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Submission Document *
                </label>
                <select
                  value={submissionId}
                  onChange={(e) => setSubmissionId(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">-- Choose document --</option>
                  {documents.map((d) => (
                    <option key={d.document_id} value={d.document_id}>
                      {d.filename}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Reference Document *
                </label>
                <select
                  value={referenceId}
                  onChange={(e) => setReferenceId(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">-- Choose reference --</option>
                  {documents
                    .filter((d) => d.document_id !== submissionId)
                    .map((d) => (
                      <option key={d.document_id} value={d.document_id}>
                        {d.filename}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Detection Mode
              </label>
              <div className="flex gap-2">
                {(['hybrid', 'lexical', 'semantic'] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setQuickDetectionMode(m)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                      quickDetectionMode === m
                        ? 'bg-indigo-50 text-indigo-700 border border-indigo-300'
                        : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {getModeLabel(m)}
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-100">
              <span className="text-xs text-slate-500">{runProgressMsg}</span>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setShowQuickRun(false)}
                  disabled={isRunning}
                  className="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRunning}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5"
                >
                  {isRunning ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <span>Start Analysis</span>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-xs">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-1" />
          <span className="text-xs text-slate-500 font-medium">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by document name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Analyses Table */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600" />
          <p className="text-xs">Loading analysis history...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs">
          {error}
        </div>
      ) : filteredAnalyses.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-slate-200 rounded-2xl bg-white shadow-xs space-y-3">
          <History className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No analyses found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {analyses.length === 0
              ? 'No similarity analyses have been run yet. Click "Run Analysis" or check a document on the Home screen.'
              : 'No analyses matched your filter criteria.'}
          </p>
          {analyses.length === 0 && (
            <div className="pt-2">
              <button
                onClick={onNavigateToIngestion}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg inline-flex items-center space-x-1.5 shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Start First Analysis</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200/90 overflow-hidden shadow-xs">
          <div className="divide-y divide-slate-100">
            {filteredAnalyses.map((a) => {
              const score = a.net_score ?? a.lexical_coverage ?? 0;
              const dateStr = a.created_at
                ? new Date(a.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'Recent';

              const docName = a.submission_filename || `Document ${a.submission_document_id.substring(0, 8)}`;

              return (
                <div
                  key={a.analysis_id}
                  className="p-4 sm:px-6 hover:bg-slate-50/70 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-900 truncate max-w-md">
                        {docName}
                      </h3>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {getModeLabel(a.detection_mode)}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          a.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : a.status === 'processing'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {a.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      <span>{dateStr}</span>
                      <span>•</span>
                      <span>{a.total_findings_count ?? 0} matches</span>
                      <span>•</span>
                      <span>
                        Evidence:{' '}
                        <strong className="text-slate-700 font-mono">
                          {score.toFixed(1)}%
                        </strong>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 flex-shrink-0 self-end sm:self-center">
                    <button
                      type="button"
                      onClick={() => onSelectAnalysis(a.analysis_id)}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
                    >
                      <span>View Results</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDelete(a.analysis_id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                      title="Delete Analysis"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisHistoryPage;
