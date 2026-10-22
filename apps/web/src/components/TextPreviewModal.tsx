import React, { useState, useEffect } from 'react';
import { X, FileText, Layers, AlertTriangle, Globe, AlignLeft, RefreshCw } from 'lucide-react';
import { DocumentTextPreview, Passage } from '../types/generated/api';
import { getDocumentTextPreview, getDocumentPassages } from '../lib/api/documents';

interface TextPreviewModalProps {
  documentId: string | null;
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

export const TextPreviewModal: React.FC<TextPreviewModalProps> = ({
  documentId,
  filename,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'text' | 'passages'>('text');
  const [preview, setPreview] = useState<DocumentTextPreview | null>(null);
  const [passages, setPassages] = useState<Passage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !documentId) {
      setPreview(null);
      setPassages([]);
      return;
    }

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [textData, passagesData] = await Promise.all([
          getDocumentTextPreview(documentId),
          getDocumentPassages(documentId),
        ]);
        setPreview(textData);
        setPassages(passagesData.passages || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load document preview data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isOpen, documentId]);

  if (!isOpen) return null;

  const getLanguageLabel = (code: string) => {
    switch (code.toLowerCase()) {
      case 'hi':
        return 'Hindi (Devanagari)';
      case 'te':
        return 'Telugu (Telugu Script)';
      case 'en':
        return 'English (Latin)';
      case 'mixed':
        return 'Mixed Multilingual';
      default:
        return code.toUpperCase();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white truncate max-w-md">{filename}</h3>
                {preview?.detected_language && (
                  <span className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30">
                    <Globe className="w-3 h-3 mr-1" />
                    {getLanguageLabel(preview.detected_language)}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                <span>Chars: <strong className="text-slate-200">{preview?.char_count ?? 0}</strong></span>
                <span>•</span>
                <span>Tokens: <strong className="text-slate-200">{preview?.word_count ?? 0}</strong></span>
                <span>•</span>
                <span>Passages: <strong className="text-slate-200">{passages.length}</strong></span>
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* View Switcher Tabs */}
        <div className="px-5 pt-3 border-b border-slate-800 flex space-x-2 bg-slate-950/40">
          <button
            onClick={() => setActiveTab('text')}
            className={`flex items-center space-x-2 px-3 py-1.5 text-xs font-medium rounded-t-lg transition border-b-2 ${
              activeTab === 'text'
                ? 'border-sky-500 text-sky-400 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlignLeft className="w-3.5 h-3.5" />
            <span>Extracted Raw Text</span>
          </button>
          <button
            onClick={() => setActiveTab('passages')}
            className={`flex items-center space-x-2 px-3 py-1.5 text-xs font-medium rounded-t-lg transition border-b-2 ${
              activeTab === 'passages'
                ? 'border-sky-500 text-sky-400 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Segmented Passages ({passages.length})</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-sky-400 mb-3" />
              <p className="text-sm">Loading extracted document text and passages...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Warnings Banner if any */}
              {preview?.warnings && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-300 text-xs flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>Processing Notes: {preview.warnings}</span>
                </div>
              )}

              {activeTab === 'text' && (
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl font-sans text-sm text-slate-200 whitespace-pre-wrap leading-relaxed max-h-[55vh] overflow-y-auto select-text">
                  {preview?.raw_text ? (
                    preview.raw_text
                  ) : (
                    <span className="text-slate-500 italic">No selectable text extracted from this file.</span>
                  )}
                </div>
              )}

              {activeTab === 'passages' && (
                <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
                  {passages.length === 0 ? (
                    <p className="text-xs text-slate-500 italic py-8 text-center">No passage segments found.</p>
                  ) : (
                    passages.map((p) => (
                      <div
                        key={p.id}
                        className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2 hover:border-slate-700 transition"
                      >
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-sky-400 font-semibold">Passage #{p.sequence_index + 1}</span>
                            <span>•</span>
                            <span className="font-mono">Offsets: [{p.start_offset}, {p.end_offset})</span>
                            <span>•</span>
                            <span>Page: {p.page_number}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                              {p.token_count} tokens
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 font-semibold text-[10px]">
                              {p.language.toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed font-sans">{p.text_content}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex justify-between items-center text-xs text-slate-400">
          <span className="font-mono">Zero-based half-open Unicode code-point spans</span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};
