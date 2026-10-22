import React from 'react';
import { Database, Cpu, Activity, HardDrive, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { HealthStatus } from '../types/generated/api';

interface StatusIndicatorProps {
  health: HealthStatus | null;
  loading: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ health, loading }) => {
  const getStatusBadge = (state: string | undefined) => {
    if (loading) {
      return (
        <span className="inline-flex items-center text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full font-medium">
          Checking...
        </span>
      );
    }
    if (state === 'connected' || state === 'operational' || state === 'healthy') {
      return (
        <span className="inline-flex items-center text-xs text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-2 py-0.5 rounded-full font-semibold">
          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
          {state.toUpperCase()}
        </span>
      );
    }
    if (state === 'degraded') {
      return (
        <span className="inline-flex items-center text-xs text-amber-700 bg-amber-50 border border-amber-200/80 px-2 py-0.5 rounded-full font-semibold">
          <AlertTriangle className="w-3 h-3 mr-1 text-amber-600" />
          DEGRADED
        </span>
      );
    }
    return (
      <span className="inline-flex items-center text-xs text-rose-700 bg-rose-50 border border-rose-200/80 px-2 py-0.5 rounded-full font-semibold">
        <XCircle className="w-3 h-3 mr-1 text-rose-600" />
        DISCONNECTED
      </span>
    );
  };

  const services = [
    {
      name: 'Local Metadata Database',
      spec: 'SQLite WAL Dev Adapter / PostgreSQL Schema',
      icon: Database,
      status: health?.database,
      detail: 'Relational metadata, passage offsets, and dense vector embeddings storage.',
    },
    {
      name: 'Task Dispatch Broker',
      spec: 'Native ThreadPoolExecutor / Redis RQ Adapter',
      icon: Activity,
      status: health?.redis,
      detail: 'Job queue dispatch, worker synchronization, and cache acceleration.',
    },
    {
      name: 'Similarity Worker Pool',
      spec: 'Bounded ThreadPoolExecutor / RQ Daemon',
      icon: Cpu,
      status: health?.worker_pool,
      detail: 'Asynchronous document extraction, candidate search, and scoring jobs.',
    },
    {
      name: 'FastAPI Backend Engine',
      spec: `FastAPI Async Server (v${health?.version || '1.0.0'})`,
      icon: HardDrive,
      status: health?.status,
      detail: 'REST API, RFC 7807 problem envelopes, and JWT Bearer security.',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
      {services.map((svc) => {
        const Icon = svc.icon;
        return (
          <div
            key={svc.name}
            className="p-4 bg-white border border-slate-200/90 rounded-xl flex flex-col justify-between hover:border-slate-300 shadow-xs transition"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <div className="p-2 bg-slate-100 rounded-lg text-slate-700">
                  <Icon className="w-4 h-4" />
                </div>
                {getStatusBadge(svc.status)}
              </div>
              <h3 className="text-xs font-bold text-slate-900 mb-0.5">{svc.name}</h3>
              <p className="text-[11px] text-indigo-600 font-mono mb-1.5">{svc.spec}</p>
              <p className="text-[11px] text-slate-500 leading-relaxed">{svc.detail}</p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 text-[10px] text-slate-400 flex justify-between">
              <span>Execution</span>
              <span className="font-mono">Localhost</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
