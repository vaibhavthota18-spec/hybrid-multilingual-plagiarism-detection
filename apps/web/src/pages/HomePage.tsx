import React, { useState } from 'react';
import { StatusIndicator } from '../components/StatusIndicator';
import { HealthStatus } from '../types/generated/api';
import { 
  Database, 
  Cpu, 
  ShieldCheck, 
  CheckCircle2, 
  Clock, 
  ChevronRight
} from 'lucide-react';

interface HomePageProps {
  health: HealthStatus | null;
  loading: boolean;
  onRefresh?: () => void;
  onOpenFutureFeature: (featureName: string, targetPhase: string, description: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({
  health,
  loading,
  onOpenFutureFeature,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);

  const roadmapPhases = [
    {
      num: '0',
      title: 'Requirements & Architecture',
      status: 'VERIFIED COMPLETE',
      active: false,
      completed: true,
      desc: '8 ADRs, OpenAPI 3.1 contract, data dictionary, schema contracts, Winnowing calibration policy.',
    },
    {
      num: '1',
      title: 'Engineering Foundation & Infrastructure',
      status: 'IMPLEMENTED & TESTED',
      active: true,
      completed: true,
      desc: 'FastAPI backend, PostgreSQL 16 + pgvector, Alembic migrations, Redis RQ worker, React Vite frontend, Docker Compose.',
    },
    {
      num: '2',
      title: 'Document Ingestion & Multi-Format Parsing',
      status: 'SCHEDULED',
      active: false,
      completed: true,
      desc: 'PDF, DOCX, TXT parsers, Unicode NFC normalization, passage chunking, language hint validation.',
    },
    {
      num: '3',
      title: 'Detection Core & Hybrid Scoring',
      status: 'SCHEDULED',
      active: false,
      completed: true,
      desc: 'Winnowing fingerprinting (k=25, w=16), BM25 lexical retrieval, Multilingual E5 dense vector embeddings, hybrid ranker.',
    },
    {
      num: '4',
      title: 'Corpus Indexing & Candidate Search',
      status: 'SCHEDULED',
      active: false,
      completed: false,
      desc: 'Scalable corpus storage, HNSW/IVFFlat pgvector index tuning, collection partitioning, one-to-many search.',
    },
    {
      num: '5',
      title: 'Human Review & PDF Reports',
      status: 'SCHEDULED',
      active: false,
      completed: false,
      desc: 'Interactive side-by-side match viewer, false-positive exclusions, human audit decisions, ReportLab PDF export.',
    },
    {
      num: '6',
      title: 'Evaluation, Calibration & Tuning',
      status: 'SCHEDULED',
      active: false,
      completed: false,
      desc: 'Multilingual benchmark validation, cross-lingual threshold calibration, precision/recall verification.',
    },
    {
      num: '7',
      title: 'Production Hardening & Operations',
      status: 'SCHEDULED',
      active: false,
      completed: false,
      desc: 'Load testing, security auditing, disaster recovery rehearsal, rate limiting, production rollout.',
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner / Hero */}
      <section className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-8 shadow-xs">
        <div className="max-w-4xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-indigo-50 border border-indigo-200/70 rounded-full text-xs font-semibold text-indigo-700 mb-3">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
            <span>Developer Status & Infrastructure Diagnostics</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            System Infrastructure & Architecture
          </h2>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            High-performance hybrid analysis foundation integrating lexical fingerprinting (Winnowing)
            and semantic cross-lingual dense vectors (Multilingual E5) across English, Hindi, and Telugu.
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
            <span className="font-mono text-slate-700">FastAPI</span>
            <span>•</span>
            <span className="font-mono text-slate-700">SQLite Dev Adapter</span>
            <span>•</span>
            <span className="font-mono text-slate-700">Bounded ThreadPoolExecutor</span>
            <span>•</span>
            <span className="font-mono text-slate-700">React 18 + Vite</span>
          </div>
        </div>
      </section>

      {/* Infrastructure Status Grid */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Live Infrastructure Status
          </h3>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium transition"
          >
            {showRawJson ? 'Hide Raw Response' : 'View Health JSON'}
          </button>
        </div>

        <StatusIndicator health={health} loading={loading} />

        {showRawJson && health && (
          <div className="mt-3 p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono text-xs text-emerald-400 overflow-x-auto">
            <pre>{JSON.stringify(health, null, 2)}</pre>
          </div>
        )}
      </section>

      {/* Architectural Pillars / Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-2.5 shadow-xs">
          <div className="p-2 w-fit bg-indigo-50 text-indigo-600 rounded-lg border border-indigo-100">
            <Database className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">Relational & Vector Data Store</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Normalized tables managed via SQLite adapter and production PostgreSQL schema. Full support for
            Multilingual E5 passage embeddings with cosine distance indexing.
          </p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-2.5 shadow-xs">
          <div className="p-2 w-fit bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-100">
            <Cpu className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">Asynchronous Task Queue</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Local bounded ThreadPoolExecutor adapter decoupling long-running document ingestion, Winnowing hash
            generation, dense embedding inference, and comparison jobs from HTTP request threads.
          </p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-2.5 shadow-xs">
          <div className="p-2 w-fit bg-purple-50 text-purple-600 rounded-lg border border-purple-100">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-slate-900">Security & API Contracts</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Strict OpenAPI 3.1 specification adherence with RFC 7807 problem details error envelopes.
            Role-based authentication with HS256 algorithm pinning.
          </p>
        </div>
      </section>

      {/* Roadmap Phase Matrix */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4 shadow-xs">
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Eight-Phase Development Roadmap Status
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Strict sequential execution: each phase builds upon fully verified foundation deliverables.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {roadmapPhases.map((phase) => (
            <div
              key={phase.num}
              onClick={() => {
                if (!phase.completed) {
                  onOpenFutureFeature(phase.title, `Phase ${phase.num}`, phase.desc);
                }
              }}
              className={`p-3.5 rounded-xl border transition flex flex-col justify-between ${
                phase.active
                  ? 'bg-indigo-50/70 border-indigo-300 shadow-xs'
                  : phase.completed
                  ? 'bg-slate-50/60 border-emerald-200'
                  : 'bg-white border-slate-200 hover:border-slate-300 cursor-pointer'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[11px] font-bold font-mono text-slate-500">
                    PHASE {phase.num}
                  </span>
                  {phase.completed ? (
                    <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {phase.active ? 'PHASE 1 LIVE' : 'VERIFIED'}
                    </span>
                  ) : (
                    <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
                      UPCOMING
                    </span>
                  )}
                </div>
                <h5 className="text-xs font-bold text-slate-900 mb-1">{phase.title}</h5>
                <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-3">{phase.desc}</p>
              </div>

              {!phase.completed && (
                <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-indigo-600 font-medium">
                  <span>View phase details</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
