import React from 'react';
import { Shield } from 'lucide-react';

interface HeaderProps {
  health?: any;
  loading?: boolean;
  onRefresh?: () => void;
  onNavigateHome?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNavigateHome }) => {
  return (
    <header className="border-b border-slate-200/80 bg-white sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div
          onClick={onNavigateHome}
          className="flex items-center space-x-3 cursor-pointer select-none"
        >
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100 shadow-xs">
            <Shield className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">
              Plagiarism Engine
            </h1>
            <p className="text-xs text-slate-500">
              Multilingual Similarity Detection (English • Hindi • Telugu)
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
