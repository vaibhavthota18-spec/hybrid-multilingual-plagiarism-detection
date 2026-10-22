import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Database,
  Trash2,
  Eye,
  CheckCircle2,
  AlertCircle,
  Plus,
  RefreshCw,
  Clock,
  Globe,
  Sliders,
  ArrowRight,
  FileCheck2,
} from 'lucide-react';
import {
  DocumentMetadata,
  Collection,
  ValidateComparisonResponse,
} from '../types/generated/api';
import {
  uploadDocument,
  listDocuments,
  deleteDocument,
  createCollection,
  listCollections,
  listCollectionDocuments,
  addDocumentToCollection,
  removeDocumentFromCollection,
  validateComparison,
} from '../lib/api/documents';
import { analysesApi } from '../lib/api/analyses';
import { TextPreviewModal } from '../components/TextPreviewModal';

export interface IngestionPageProps {
  onNavigateToAnalysis?: (analysisId?: string) => void;
}

export const IngestionPage: React.FC<IngestionPageProps> = ({ onNavigateToAnalysis }) => {
  const [subTab, setSubTab] = useState<'upload' | 'library' | 'collections' | 'comparison'>('upload');
  const [runningAnalysis, setRunningAnalysis] = useState<boolean>(false);


  // Library & Data states
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);
  const [loadingCols, setLoadingCols] = useState<boolean>(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Upload states
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [docTitle, setDocTitle] = useState<string>('');
  const [languageHint, setLanguageHint] = useState<string>('auto');
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Preview Modal state
  const [previewDoc, setPreviewDoc] = useState<{ id: string; name: string } | null>(null);

  // Collection modal & active view
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [collectionDocs, setCollectionDocs] = useState<DocumentMetadata[]>([]);
  const [newColName, setNewColName] = useState<string>('');
  const [newColDesc, setNewColDesc] = useState<string>('');
  const [showCreateCol, setShowCreateCol] = useState<boolean>(false);

  // Comparison Setup states
  const [compMode, setCompMode] = useState<'direct' | 'one_to_many' | 'corpus'>('direct');
  const [detectionMode, setDetectionMode] = useState<'hybrid' | 'lexical' | 'semantic'>('hybrid');
  const [submissionDocId, setSubmissionDocId] = useState<string>('');
  const [directRefDocId, setDirectRefDocId] = useState<string>('');
  const [multiRefDocIds, setMultiRefDocIds] = useState<string[]>([]);
  const [targetCollectionId, setTargetCollectionId] = useState<string>('');
  const [validatingComp, setValidatingComp] = useState<boolean>(false);
  const [compValidationResult, setCompValidationResult] = useState<ValidateComparisonResponse | null>(null);

  // Load documents
  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const res = await listDocuments(100, 0);
      setDocuments(res.items || []);
    } catch (err: any) {
      console.error('Failed to load documents', err);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  // Load collections
  const loadCollections = useCallback(async () => {
    setLoadingCols(true);
    try {
      const res = await listCollections(100, 0);
      setCollections(res.items || []);
    } catch (err: any) {
      console.error('Failed to load collections', err);
    } finally {
      setLoadingCols(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
    loadCollections();
  }, [loadDocuments, loadCollections]);

  // Load collection documents when a collection is selected
  const loadCollectionMembers = useCallback(async (colId: string) => {
    try {
      const res = await listCollectionDocuments(colId);
      setCollectionDocs(res.documents || []);
    } catch (err) {
      console.error('Failed to load collection members', err);
    }
  }, []);

  useEffect(() => {
    if (selectedCollection) {
      loadCollectionMembers(selectedCollection.collection_id);
    }
  }, [selectedCollection, loadCollectionMembers]);

  // Handle Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  // Upload action
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setFeedbackMsg(null);

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      setUploadProgress(`Uploading and processing file ${i + 1} of ${selectedFiles.length}: ${file.name}`);
      try {
        await uploadDocument(file, docTitle || undefined, languageHint);
        successCount++;
      } catch (err: any) {
        failCount++;
        setFeedbackMsg({
          type: 'error',
          text: `Failed to upload '${file.name}': ${err.message || 'Validation error'}`,
        });
      }
    }

    setUploading(false);
    setUploadProgress('');
    setSelectedFiles([]);
    setDocTitle('');
    loadDocuments();

    if (successCount > 0 && failCount === 0) {
      setFeedbackMsg({
        type: 'success',
        text: `Successfully uploaded and processed ${successCount} document(s). Text extracted and passages indexed.`,
      });
    }
  };

  // Delete action
  const handleDeleteDoc = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete '${name}'?`)) return;
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.document_id !== id));
      if (selectedCollection) loadCollectionMembers(selectedCollection.collection_id);
      loadCollections();
      setFeedbackMsg({ type: 'success', text: `Document '${name}' deleted successfully.` });
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: `Failed to delete '${name}': ${err.message}` });
    }
  };

  // Create Collection
  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    try {
      const col = await createCollection(newColName.trim(), newColDesc.trim());
      setCollections((prev) => [col, ...prev]);
      setNewColName('');
      setNewColDesc('');
      setShowCreateCol(false);
      setSelectedCollection(col);
      setFeedbackMsg({ type: 'success', text: `Reference collection '${col.name}' created.` });
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: `Failed to create collection: ${err.message}` });
    }
  };

  // Add document to active collection
  const handleAddToCollection = async (docId: string) => {
    if (!selectedCollection) return;
    try {
      await addDocumentToCollection(selectedCollection.collection_id, docId);
      loadCollectionMembers(selectedCollection.collection_id);
      loadCollections();
      setFeedbackMsg({ type: 'success', text: 'Document added to collection.' });
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: `Failed to add document: ${err.message}` });
    }
  };

  // Remove document from active collection
  const handleRemoveFromCollection = async (docId: string) => {
    if (!selectedCollection) return;
    try {
      await removeDocumentFromCollection(selectedCollection.collection_id, docId);
      loadCollectionMembers(selectedCollection.collection_id);
      loadCollections();
      setFeedbackMsg({ type: 'success', text: 'Document removed from collection.' });
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: `Failed to remove document: ${err.message}` });
    }
  };

  // Validate comparison inputs
  const handleValidateComparison = async () => {
    if (!submissionDocId) {
      setFeedbackMsg({ type: 'error', text: 'Please select a submission document.' });
      return;
    }
    setValidatingComp(true);
    setCompValidationResult(null);
    setFeedbackMsg(null);

    try {
      const res = await validateComparison({
        submission_document_id: submissionDocId,
        mode: compMode,
        reference_document_id: compMode === 'direct' ? directRefDocId : undefined,
        reference_document_ids: compMode === 'one_to_many' ? multiRefDocIds : undefined,
        collection_id: compMode === 'corpus' ? targetCollectionId : undefined,
      });
      setCompValidationResult(res);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Comparison validation failed' });
    } finally {
      setValidatingComp(false);
    }
  };

  // Run Lexical Similarity Analysis
  const handleRunAnalysis = async () => {
    if (!submissionDocId) return;
    setRunningAnalysis(true);
    setFeedbackMsg(null);
    try {
      const job = await analysesApi.createAnalysis({
        submission_document_id: submissionDocId,
        mode: compMode,
        detection_mode: detectionMode,
        reference_document_id: compMode === 'direct' ? directRefDocId : undefined,
        reference_document_ids: compMode === 'one_to_many' ? multiRefDocIds : undefined,
        collection_id: compMode === 'corpus' ? targetCollectionId : undefined,
      });

      // Poll until complete
      await analysesApi.pollAnalysisUntilComplete(job.analysis_id, undefined, 1000, 30);
      if (onNavigateToAnalysis) {
        onNavigateToAnalysis(job.analysis_id);
      } else {
        setFeedbackMsg({
          type: 'success',
          text: `Analysis ${job.analysis_id.substring(0, 8)} completed successfully! Check the Similarity Analysis tab to inspect findings.`,
        });
      }
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: `Analysis execution failed: ${err.message || 'Unknown error'}`,
      });
    } finally {
      setRunningAnalysis(false);
    }
  };


  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-xs font-semibold mb-2">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Phase 4 Multilingual Semantic & Hybrid AI Live</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Document Ingestion & Reference Corpus
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Secure multi-format parsing (PDF, DOCX, TXT), multilingual Unicode extraction (EN • HI • TE), and collection management.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              loadDocuments();
              loadCollections();
            }}
            title="Refresh documents and collections"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg border border-slate-800 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loadingDocs || loadingCols ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedbackMsg && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center justify-between border ${
            feedbackMsg.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
          }`}
        >
          <div className="flex items-center space-x-2">
            {feedbackMsg.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            )}
            <span>{feedbackMsg.text}</span>
          </div>
          <button
            onClick={() => setFeedbackMsg(null)}
            className="text-slate-400 hover:text-white ml-2 text-sm"
          >
            ✕
          </button>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex space-x-2 border-b border-slate-800 pb-2 overflow-x-auto scrollbar-none">
        <button
          onClick={() => setSubTab('upload')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-medium rounded-lg transition whitespace-nowrap ${
            subTab === 'upload'
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Documents</span>
        </button>

        <button
          onClick={() => setSubTab('library')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-medium rounded-lg transition whitespace-nowrap ${
            subTab === 'library'
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Document Library ({documents.length})</span>
        </button>

        <button
          onClick={() => setSubTab('collections')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-medium rounded-lg transition whitespace-nowrap ${
            subTab === 'collections'
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Reference Collections ({collections.length})</span>
        </button>

        <button
          onClick={() => setSubTab('comparison')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-medium rounded-lg transition whitespace-nowrap ${
            subTab === 'comparison'
              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Comparison Setup</span>
        </button>
      </div>

      {/* ==================== SUB-TAB 1: UPLOAD DOCUMENTS ==================== */}
      {subTab === 'upload' && (
        <div className="space-y-6">
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition flex flex-col items-center justify-center ${
              isDragging
                ? 'border-sky-500 bg-sky-500/10'
                : 'border-slate-800 hover:border-slate-700 bg-slate-900/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />

            <div className="p-3 bg-sky-500/10 text-sky-400 rounded-2xl border border-sky-500/20 mb-3">
              <UploadCloud className="w-8 h-8" />
            </div>

            <h3 className="text-base font-semibold text-white">
              Drag and drop source documents here
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              Supports <strong className="text-slate-200">PDF, DOCX, and TXT</strong> up to 30 MiB.
              Files are streamed safely into private private storage and never exposed via public static routes.
            </p>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
            >
              Browse Files from Computer
            </button>
          </div>

          {/* Form Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Document Title (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Comparative Analysis of Multilingual NLP"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Language Hint
              </label>
              <select
                value={languageHint}
                onChange={(e) => setLanguageHint(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="auto">Auto-Detect Script (English, Hindi, Telugu)</option>
                <option value="en">English (en)</option>
                <option value="hi">Hindi (hi - देवनागरी)</option>
                <option value="te">Telugu (te - తెలుగు)</option>
              </select>
            </div>
          </div>

          {/* Selected File Queue */}
          {selectedFiles.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Files Ready for Ingestion ({selectedFiles.length})
              </h4>

              <div className="space-y-2">
                {selectedFiles.map((file, idx) => (
                  <div
                    key={`${file.name}-${idx}`}
                    className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center space-x-3 truncate">
                      <FileText className="w-4 h-4 text-sky-400 flex-shrink-0" />
                      <span className="font-medium text-white truncate">{file.name}</span>
                      <span className="text-slate-500 font-mono">({(file.size / 1024).toFixed(1)} KB)</span>
                    </div>

                    <button
                      onClick={() => setSelectedFiles((prev) => prev.filter((_, i) => i !== idx))}
                      className="p-1 text-slate-400 hover:text-rose-400 transition"
                      title="Remove from queue"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  disabled={uploading}
                  onClick={handleUpload}
                  className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition flex items-center space-x-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>{uploadProgress || 'Processing...'}</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-4 h-4" />
                      <span>Start Document Ingestion & Text Extraction</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================== SUB-TAB 2: DOCUMENT LIBRARY ==================== */}
      {subTab === 'library' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Uploaded Documents ({documents.length})
            </h3>
            <span className="text-xs text-slate-500">Stored in private local filesystem repository</span>
          </div>

          {documents.length === 0 ? (
            <div className="p-12 text-center border border-slate-800 rounded-2xl bg-slate-900/40">
              <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-400">No documents uploaded yet</p>
              <p className="text-xs text-slate-600 mt-1">Switch to the Upload tab to add PDF, DOCX, or TXT files.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="p-4 bg-slate-900/70 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-700 transition"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <FileCheck2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                      <h4 className="text-sm font-semibold text-white truncate">{doc.filename}</h4>
                      {doc.title && (
                        <span className="text-xs text-slate-400 italic truncate max-w-xs">({doc.title})</span>
                      )}
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase border ${
                          doc.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : doc.status === 'processing'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}
                      >
                        {doc.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono">
                      <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span>Pages: {doc.page_count}</span>
                      <span>•</span>
                      <span>Chars: {doc.char_count}</span>
                      <span>•</span>
                      <span className="flex items-center text-sky-400">
                        <Globe className="w-3 h-3 mr-1" />
                        {doc.detected_language.toUpperCase()}
                      </span>
                      <span>•</span>
                      <span className="text-slate-500">
                        Uploaded {new Date(doc.created_at).toLocaleTimeString()}
                      </span>
                    </div>

                    {doc.warnings && (
                      <p className="text-[11px] text-amber-400 italic">Notice: {doc.warnings}</p>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 self-end md:self-center">
                    <button
                      onClick={() => setPreviewDoc({ id: doc.document_id, name: doc.filename })}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition flex items-center space-x-1.5"
                    >
                      <Eye className="w-3.5 h-3.5 text-sky-400" />
                      <span>Preview Text & Passages</span>
                    </button>

                    <button
                      onClick={() => handleDeleteDoc(doc.document_id, doc.filename)}
                      className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                      title="Permanently delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ==================== SUB-TAB 3: REFERENCE COLLECTIONS ==================== */}
      {subTab === 'collections' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Reference Collections (Corpus Management)
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Group verified reference documents into thematic collections for high-scale comparison.
              </p>
            </div>

            <button
              onClick={() => setShowCreateCol(true)}
              className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium rounded-lg transition flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Collection</span>
            </button>
          </div>

          {/* Modal / Form to Create Collection */}
          {showCreateCol && (
            <div className="p-4 bg-slate-900 border border-slate-700 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white">Create New Reference Collection</h4>
                <button onClick={() => setShowCreateCol(false)} className="text-slate-400 hover:text-white">✕</button>
              </div>

              <form onSubmit={handleCreateCollection} className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Collection Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 2026 Academic Literature Corpus"
                    value={newColName}
                    onChange={(e) => setNewColName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Description (Optional)</label>
                  <textarea
                    rows={2}
                    placeholder="Brief description of the reference files..."
                    value={newColDesc}
                    onChange={(e) => setNewColDesc(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateCol(false)}
                    className="px-3 py-1.5 bg-slate-800 text-slate-300 text-xs rounded-lg hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium rounded-lg"
                  >
                    Save Collection
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Collections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {collections.map((col) => {
              const isSelected = selectedCollection?.collection_id === col.collection_id;
              return (
                <div
                  key={col.collection_id}
                  onClick={() => setSelectedCollection(col)}
                  className={`p-4 rounded-xl border transition cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-sky-500/10 border-sky-500/50 shadow-md shadow-sky-500/5'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
                        <Database className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {col.document_count} doc(s)
                      </span>
                    </div>
                    <h4 className="text-sm font-semibold text-white mb-1">{col.name}</h4>
                    <p className="text-xs text-slate-400 line-clamp-2">{col.description || 'No description provided.'}</p>
                  </div>

                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-sky-400">
                    <span>{isSelected ? 'Viewing Membership' : 'Select to manage'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected Collection Membership Manager */}
          {selectedCollection && (
            <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                  <h4 className="text-sm font-bold text-white">
                    Collection: {selectedCollection.name}
                  </h4>
                  <p className="text-xs text-slate-400">
                    {collectionDocs.length} document(s) currently indexed in this reference corpus.
                  </p>
                </div>
              </div>

              {/* Add document dropdown */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-300">Add document from library:</span>
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      handleAddToCollection(e.target.value);
                      e.target.value = '';
                    }
                  }}
                  defaultValue=""
                  className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="" disabled>-- Select uploaded document to add --</option>
                  {documents
                    .filter((d) => !collectionDocs.some((cd) => cd.document_id === d.document_id))
                    .map((d) => (
                      <option key={d.document_id} value={d.document_id}>
                        {d.filename} ({d.detected_language.toUpperCase()})
                      </option>
                    ))}
                </select>
              </div>

              {/* Members List */}
              {collectionDocs.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-4">No documents added to this collection yet.</p>
              ) : (
                <div className="space-y-2">
                  {collectionDocs.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <FileText className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
                        <span className="text-slate-200 font-medium truncate">{doc.filename}</span>
                        <span className="text-slate-500 font-mono">({doc.char_count} chars)</span>
                      </div>
                      <button
                        onClick={() => handleRemoveFromCollection(doc.document_id)}
                        className="text-xs text-slate-400 hover:text-rose-400 transition"
                        title="Remove from collection"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ==================== SUB-TAB 4: COMPARISON SETUP ==================== */}
      {subTab === 'comparison' && (
        <div className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div>
              <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[11px] font-semibold mb-2">
                <Clock className="w-3 h-3" />
                <span>Phase 2 Verification Gate — Preparation for Phase 3 Detection Core</span>
              </div>
              <h3 className="text-base font-bold text-white">
                Comparison Input Validation & Analysis Preparation
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Configure candidate submission documents and reference corpora. Validates that all files are processed,
                non-empty, and free of circular self-comparison. Algorithmic similarity scoring will execute in Phase 3.
              </p>
            </div>

            {/* Mode Selector */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setCompMode('direct')}
                className={`p-3 rounded-xl border text-left transition ${
                  compMode === 'direct'
                    ? 'bg-sky-500/10 border-sky-500/40 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-bold">1. Direct Comparison (1:1)</div>
                <div className="text-[11px] text-slate-400 mt-1">One candidate submission against one reference document.</div>
              </button>

              <button
                type="button"
                onClick={() => setCompMode('one_to_many')}
                className={`p-3 rounded-xl border text-left transition ${
                  compMode === 'one_to_many'
                    ? 'bg-sky-500/10 border-sky-500/40 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-bold">2. One-to-Many (1:N)</div>
                <div className="text-[11px] text-slate-400 mt-1">One submission against multiple specific reference documents.</div>
              </button>

              <button
                type="button"
                onClick={() => setCompMode('corpus')}
                className={`p-3 rounded-xl border text-left transition ${
                  compMode === 'corpus'
                    ? 'bg-sky-500/10 border-sky-500/40 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-bold">3. Corpus Search (1:Collection)</div>
                <div className="text-[11px] text-slate-400 mt-1">One submission against an entire reference collection.</div>
              </button>
            </div>

            {/* Input Selection Forms */}
            <div className="space-y-4 pt-2">
              {/* Submission Document Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Select Submission Document *
                </label>
                <select
                  value={submissionDocId}
                  onChange={(e) => setSubmissionDocId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="">-- Choose submission document --</option>
                  {documents.map((d) => (
                    <option key={d.document_id} value={d.document_id}>
                      {d.filename} ({d.detected_language.toUpperCase()} • {d.char_count} chars • Status: {d.status})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mode-specific references */}
              {compMode === 'direct' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Select Reference Document *
                  </label>
                  <select
                    value={directRefDocId}
                    onChange={(e) => setDirectRefDocId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="">-- Choose reference document --</option>
                    {documents
                      .filter((d) => d.document_id !== submissionDocId)
                      .map((d) => (
                        <option key={d.document_id} value={d.document_id}>
                          {d.filename} ({d.detected_language.toUpperCase()} • {d.char_count} chars)
                        </option>
                      ))}
                  </select>
                </div>
              )}

              {compMode === 'one_to_many' && (
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-slate-300">
                    Select Multiple Reference Documents (Select one or more) *
                  </label>
                  <div className="max-h-48 overflow-y-auto space-y-1.5 p-3 bg-slate-950 border border-slate-800 rounded-xl">
                    {documents
                      .filter((d) => d.document_id !== submissionDocId)
                      .map((d) => {
                        const isChecked = multiRefDocIds.includes(d.document_id);
                        return (
                          <label
                            key={d.document_id}
                            className="flex items-center space-x-2 text-xs text-slate-300 hover:text-white cursor-pointer"
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setMultiRefDocIds((prev) => [...prev, d.document_id]);
                                } else {
                                  setMultiRefDocIds((prev) => prev.filter((id) => id !== d.document_id));
                                }
                              }}
                              className="rounded border-slate-700 bg-slate-900 text-sky-500"
                            />
                            <span>{d.filename}</span>
                            <span className="text-slate-500">({d.detected_language.toUpperCase()} • {d.char_count} chars)</span>
                          </label>
                        );
                      })}
                  </div>
                </div>
              )}

              {compMode === 'corpus' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Select Reference Collection *
                  </label>
                  <select
                    value={targetCollectionId}
                    onChange={(e) => setTargetCollectionId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="">-- Choose reference collection --</option>
                    {collections.map((c) => (
                      <option key={c.collection_id} value={c.collection_id}>
                        {c.name} ({c.document_count} documents)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Strict Phase Boundary: similarity score algorithms will execute in Phase 3.
                </span>
                <button
                  onClick={handleValidateComparison}
                  disabled={validatingComp}
                  className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition flex items-center space-x-2"
                >
                  {validatingComp ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Validating Inputs...</span>
                    </>
                  ) : (
                    <>
                      <FileCheck2 className="w-4 h-4" />
                      <span>Validate Comparison Inputs</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Validation Result Display */}
          {compValidationResult && (
            <div className="p-5 bg-slate-900/90 border border-emerald-500/40 rounded-2xl space-y-4">
              <div className="flex items-center space-x-2 text-emerald-400">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                <h4 className="text-sm font-bold">Comparison Preparation Validated Successfully</h4>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2">
                <p className="text-slate-200 font-semibold">{compValidationResult.message}</p>
                <div className="text-slate-400 flex flex-wrap gap-3">
                  <span>Submission: <strong className="text-white">{compValidationResult.submission_document.filename}</strong></span>
                  <span>•</span>
                  <span>Reference Mode: <strong className="text-white uppercase">{compValidationResult.mode}</strong></span>
                  <span>•</span>
                  <span>Total References: <strong className="text-emerald-400">{compValidationResult.reference_count}</strong></span>
                </div>
              </div>

              {/* Phase 4 Detection Mode Selector & Execution */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-slate-300">
                  Select Detection Engine Mode *
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div
                    onClick={() => setDetectionMode('hybrid')}
                    className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                      detectionMode === 'hybrid'
                        ? 'bg-indigo-950/60 border-indigo-500 text-white ring-1 ring-indigo-500'
                        : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-xs text-indigo-300">Hybrid AI Mode</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/20 text-indigo-300 font-semibold uppercase">Recommended</span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Combines exact Winnowing overlap with Multilingual E5 dense semantic retrieval without double-counting.
                      </p>
                    </div>
                  </div>

                  <div
                    onClick={() => setDetectionMode('lexical')}
                    className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                      detectionMode === 'lexical'
                        ? 'bg-amber-950/60 border-amber-500 text-white ring-1 ring-amber-500'
                        : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-xs text-amber-300">Lexical Only</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-semibold uppercase">Phase 3</span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Verbatim and near-exact matching using deterministic rolling hashes, Winnowing, and BM25 index.
                      </p>
                    </div>
                  </div>

                  <div
                    onClick={() => setDetectionMode('semantic')}
                    className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                      detectionMode === 'semantic'
                        ? 'bg-violet-950/60 border-violet-500 text-white ring-1 ring-violet-500'
                        : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-xs text-violet-300">Semantic AI Only</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-violet-500/20 text-violet-300 font-semibold uppercase">Phase 4</span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Dense vector cosine retrieval for paraphrased content and cross-language pairs (EN • HI • TE).
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Active Analysis Execution Bar */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs text-slate-400">
                  <span className="font-semibold text-indigo-400">Engine Active: </span>
                  {detectionMode === 'hybrid' && 'Hybrid execution (Winnowing + BM25 + Multilingual E5 384d).'}
                  {detectionMode === 'lexical' && 'Lexical execution (Winnowing k=25, w=16 + BM25).'}
                  {detectionMode === 'semantic' && 'Semantic AI execution (Multilingual E5 small dense vectors).'}
                </div>

                <button
                  type="button"
                  onClick={handleRunAnalysis}
                  disabled={runningAnalysis}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition"
                >
                  {runningAnalysis ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Running {detectionMode.toUpperCase()} Analysis...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Execute {detectionMode === 'hybrid' ? 'Hybrid' : detectionMode === 'semantic' ? 'Semantic' : 'Lexical'} Analysis</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Text Preview Modal */}
      <TextPreviewModal
        documentId={previewDoc?.id || null}
        filename={previewDoc?.name || ''}
        isOpen={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
      />
    </div>
  );
};

export default IngestionPage;
