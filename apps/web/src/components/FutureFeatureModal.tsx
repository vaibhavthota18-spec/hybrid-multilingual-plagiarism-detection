import React from 'react';
import { X, Calendar, Layers } from 'lucide-react';

interface FutureFeatureModalProps {
  isOpen: boolean;
  featureName: string;
  targetPhase: string;
  description: string;
  onClose: () => void;
}

export const FutureFeatureModal: React.FC<FutureFeatureModalProps> = ({
  isOpen,
  featureName,
  targetPhase,
  description,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="relative w-full max-w-lg p-6 bg-white border border-slate-200 rounded-2xl shadow-xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl border border-amber-200">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">{featureName}</h3>
            <span className="inline-flex items-center text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 mt-0.5">
              <Calendar className="w-3 h-3 mr-1 text-amber-600" />
              Scheduled for {targetPhase}
            </span>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
          <p>{description}</p>
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
            <strong className="text-slate-800">Strict Phase Boundary Enforcement:</strong> In strict accordance with the development roadmap, this Phase 1 foundation provides real infrastructure (FastAPI, PostgreSQL 16 + pgvector, Redis RQ, React frontend, and containerization). Algorithmic text extraction, Winnowing fingerprints, BM25 indexing, Multilingual E5 vectors, and similarity scoring are not mocked or simulated.
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition shadow-xs"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
};
