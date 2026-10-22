import React from 'react';
import { ShieldCheck } from 'lucide-react';

interface FooterProps {
  onOpenDiagnostics?: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onOpenDiagnostics }) => {
  return (
    <footer className="border-t border-slate-200/80 bg-white py-6 text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-indigo-600" />
            <span className="text-slate-800 font-semibold">Plagiarism Engine</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-500">Multilingual Similarity Detection (English • Hindi • Telugu)</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-400 text-[11px]">
            <span>Secure Local Inference</span>
            {onOpenDiagnostics && (
              <>
                <span>•</span>
                <button
                  type="button"
                  onClick={onOpenDiagnostics}
                  className="hover:text-indigo-600 underline text-slate-400 hover:text-slate-700 transition"
                  title="Developer diagnostics and health probes"
                >
                  System Diagnostics
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
