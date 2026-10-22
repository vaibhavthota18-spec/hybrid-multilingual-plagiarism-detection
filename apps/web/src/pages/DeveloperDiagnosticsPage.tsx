import React, { useState } from 'react';
import { StatusIndicator } from '../components/StatusIndicator';
import { HealthStatus } from '../types/generated/api';
import { 
  Database, 
  Cpu, 
  ShieldCheck, 
  CheckCircle2, 
  Clock, 
  ArrowLeft,
  FileText
} from 'lucide-react';

interface DeveloperDiagnosticsPageProps {
  health: HealthStatus | null;
  loading: boolean;
  onRefresh?: () => void;
  onBackToApp: () => void;
}

export const DeveloperDiagnosticsPage: React.FC<DeveloperDiagnosticsPageProps> = ({
  health,
  loading,
  onRefresh,
  onBackToApp,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);

  return (
    <div className="space-y-6 pb-12">
      {/* Return Action */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBackToApp}
          className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs transition"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
          Back to Main Application
        </button>

        <div className="flex items-center gap-2">
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-xs font-medium text-slate-700 hover:text-indigo-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 transition shadow-xs"
          >
            <FileText className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
            FastAPI OpenAPI Docs
          </a>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              className="text-xs font-medium text-slate-700 bg-white border border-slate-200 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition"
            >
              {loading ? 'Refreshing...' : 'Refresh Health'}
            </button>
          )}
        </div>
      </div>

      {/* Hero */}
      <section className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-8 shadow-xs">
        <div className="max-w-4xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-indigo-50 border border-indigo-200/70 rounded-full text-xs font-semibold text-indigo-700 mb-3">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
            <span>Developer Diagnostics & Infrastructure Health</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            System Infrastructure & Health Console
          </h2>
          <p className="mt-2 text-xs text-slate-600 leading-relaxed">
            Internal service status, SQLite development adapter, local worker concurrency, and local multilingual AI model parameters.
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center">
              <Clock className="w-3.5 h-3.5 mr-1 text-slate-400" />
              Last Checked:{' '}
              {health?.timestamp
                ? new Date(health.timestamp).toLocaleTimeString()
                : 'Awaiting connection'}
            </span>
            <span>•</span>
            <span className="font-mono text-slate-700">FastAPI 0.115+</span>
            <span>•</span>
            <span className="font-mono text-slate-700">SQLite (WAL Mode)</span>
            <span>•</span>
            <span className="font-mono text-slate-700">LocalProcessingExecutor (Workers: 2)</span>
            <span>•</span>
            <span className="font-mono text-slate-700">intfloat/multilingual-e5-small (384d)</span>
          </div>
        </div>
      </section>

      {/* Infrastructure Status Cards */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Live Subsystem Health
          </h3>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium transition"
          >
            {showRawJson ? 'Hide Raw JSON' : 'View Raw JSON'}
          </button>
        </div>

        <StatusIndicator health={health} loading={loading} />

        {showRawJson && health && (
          <div className="mt-3 p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono text-xs text-emerald-400 overflow-x-auto">
            <pre>{JSON.stringify(health, null, 2)}</pre>
          </div>
        )}
      </section>

      {/* Architectural Configuration Cards */}
      <section className="space-y-3">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Runtime System Components
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-xs">
            <div className="flex items-center space-x-2 text-indigo-600 mb-2">
              <Database className="w-4 h-4" />
              <h4 className="text-xs font-bold text-slate-900">Database & Storage</h4>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Active Tier 1: Local SQLite with WAL mode & immediate transactions. Private filesystem storage with UUID-keyed file isolation.
            </p>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-xs">
            <div className="flex items-center space-x-2 text-amber-600 mb-2">
              <Cpu className="w-4 h-4" />
              <h4 className="text-xs font-bold text-slate-900">Processing Engine</h4>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Winnowing fingerprinting (k=25, w=16), BM25 candidate retrieval, Smith-Waterman alignment, and local Multilingual E5 dense vectors.
            </p>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-xs">
            <div className="flex items-center space-x-2 text-emerald-600 mb-2">
              <ShieldCheck className="w-4 h-4" />
              <h4 className="text-xs font-bold text-slate-900">Security & Isolation</h4>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Development principal isolation, path-traversal prevention, zero pickle serialization, safe XML entity escaping in PDF/HTML reports.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default DeveloperDiagnosticsPage;
