import React from 'react';
import { FileSearch, FolderOpen, History } from 'lucide-react';

export interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenFutureFeature?: (featureName: string, targetPhase: string, description: string) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    {
      id: 'home',
      label: 'Home',
      icon: FileSearch,
    },
    {
      id: 'documents',
      label: 'My Documents',
      icon: FolderOpen,
    },
    {
      id: 'history',
      label: 'History',
      icon: History,
    },
  ];

  return (
    <nav className="border-b border-slate-200/80 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-2 py-2.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg transition ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 border border-indigo-200/80 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
