import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  FileText,
  UploadCloud,
  Trash2,
  Eye,
  Plus,
  RefreshCw,
  FolderOpen,
  Search,
  Sparkles,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';
import { DocumentMetadata, Collection } from '../types/generated/api';
import {
  listDocuments,
  uploadDocument,
  deleteDocument,
  listCollections,
  createCollection,
  listCollectionDocuments,
  addDocumentToCollection,
  removeDocumentFromCollection,
} from '../lib/api/documents';
import { TextPreviewModal } from '../components/TextPreviewModal';

interface MyDocumentsPageProps {
  onUseDocumentInComparison: (doc: DocumentMetadata) => void;
}

export const MyDocumentsPage: React.FC<MyDocumentsPageProps> = ({
  onUseDocumentInComparison,
}) => {
  const [activeTab, setActiveTab] = useState<'documents' | 'collections'>('documents');
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'name'>('date_desc');

  // Upload modal / trigger
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Preview Modal
  const [previewDoc, setPreviewDoc] = useState<{ id: string; name: string } | null>(null);

  // Collection detail / create state
  const [showCreateCol, setShowCreateCol] = useState<boolean>(false);
  const [newColName, setNewColName] = useState<string>('');
  const [newColDesc, setNewColDesc] = useState<string>('');
  const [selectedCol, setSelectedCol] = useState<Collection | null>(null);
  const [colDocs, setColDocs] = useState<DocumentMetadata[]>([]);
  const [loadingColDocs, setLoadingColDocs] = useState<boolean>(false);
  const [addDocId, setAddDocId] = useState<string>('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [docsRes, colsRes] = await Promise.all([
        listDocuments(100, 0),
        listCollections(100, 0),
      ]);
      setDocuments(docsRes.items || []);
      setCollections(colsRes.items || []);
    } catch (err: any) {
      console.error('Failed to load documents data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    setIsUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(file);
      await loadData();
    } catch (err: any) {
      setUploadError(err?.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDocument = async (docId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    try {
      await createCollection(newColName.trim(), newColDesc.trim() || undefined);
      setNewColName('');
      setNewColDesc('');
      setShowCreateCol(false);
      await loadData();
    } catch (err: any) {
      alert(`Failed to create collection: ${err.message}`);
    }
  };

  const handleSelectCollection = async (col: Collection) => {
    setSelectedCol(col);
    setLoadingColDocs(true);
    try {
      const res = await listCollectionDocuments(col.collection_id);
      setColDocs(res.documents || []);
    } catch (err: any) {
      console.error('Failed to load collection docs', err);
    } finally {
      setLoadingColDocs(false);
    }
  };

  const handleAddDocToCollection = async () => {
    if (!selectedCol || !addDocId) return;
    try {
      await addDocumentToCollection(selectedCol.collection_id, addDocId);
      setAddDocId('');
      handleSelectCollection(selectedCol);
      loadData();
    } catch (err: any) {
      alert(`Failed to add document to collection: ${err.message}`);
    }
  };

  const handleRemoveDocFromCollection = async (docId: string) => {
    if (!selectedCol) return;
    try {
      await removeDocumentFromCollection(selectedCol.collection_id, docId);
      setColDocs((prev) => prev.filter((d) => d.document_id !== docId));
      loadData();
    } catch (err: any) {
      alert(`Failed to remove document: ${err.message}`);
    }
  };

  // Filter & sort documents
  const filteredDocs = documents
    .filter((doc) => {
      const q = searchQuery.toLowerCase();
      return (
        doc.filename.toLowerCase().includes(q) ||
        (doc.title && doc.title.toLowerCase().includes(q))
      );
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.filename.localeCompare(b.filename);
      if (sortBy === 'date_asc') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  const getLanguageLabel = (lang?: string) => {
    switch (lang) {
      case 'hi':
        return 'Hindi (हिन्दी)';
      case 'te':
        return 'Telugu (తెలుగు)';
      default:
        return 'English';
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">My Documents</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage your uploaded documents and reference collections for similarity comparisons.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleUploadFile}
            className="hidden"
          />
          <button
            type="button"
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5 disabled:opacity-50"
          >
            {isUploading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <UploadCloud className="w-3.5 h-3.5" />
            )}
            <span>{isUploading ? 'Uploading...' : 'Upload Document'}</span>
          </button>

          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="p-2 text-slate-500 hover:text-slate-800 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition"
            title="Refresh documents"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Tabs & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => {
              setActiveTab('documents');
              setSelectedCol(null);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'documents'
                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200/80 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200'
            }`}
          >
            All Documents ({documents.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('collections')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'collections'
                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200/80 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200'
            }`}
          >
            Collections ({collections.length})
          </button>
        </div>

        {activeTab === 'documents' && (
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-48 sm:w-60"
              />
            </div>

            <select
              value={sortBy}
              onChange={(e: any) => setSortBy(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="date_desc">Newest First</option>
              <option value="date_asc">Oldest First</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
        )}
      </div>

      {/* ==================== TAB 1: ALL DOCUMENTS ==================== */}
      {activeTab === 'documents' && (
        <div>
          {loading ? (
            <div className="text-center py-16 text-slate-400 text-xs flex flex-col items-center gap-2">
              <RefreshCw className="w-5 h-5 animate-spin text-indigo-600" />
              <span>Loading documents...</span>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-xs">
              <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">No documents found</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                {documents.length === 0
                  ? 'You have not uploaded any documents yet. Click "Upload Document" to add files.'
                  : 'No documents match your search query.'}
              </p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
              <div className="divide-y divide-slate-100">
                {filteredDocs.map((doc) => {
                  const ext = doc.filename.split('.').pop()?.toUpperCase() || 'FILE';
                  const dateStr = new Date(doc.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  });

                  return (
                    <div
                      key={doc.document_id}
                      className="p-4 sm:px-6 hover:bg-slate-50/70 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                    >
                      <div className="flex items-center space-x-3.5 min-w-0">
                        <div className="p-2.5 bg-slate-50 border border-slate-200 text-slate-600 rounded-xl flex-shrink-0">
                          <FileCheck2 className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-semibold text-slate-900 truncate">
                              {doc.filename}
                            </h3>
                            <span className="px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded text-[10px] font-semibold">
                              {ext}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                                doc.status === 'completed'
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : doc.status === 'processing'
                                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                  : 'bg-rose-50 text-rose-700 border border-rose-200'
                              }`}
                            >
                              {doc.status}
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1">
                            <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                            <span>•</span>
                            <span>{getLanguageLabel(doc.detected_language)}</span>
                            <span>•</span>
                            <span>{doc.word_count || Math.round(doc.char_count / 5)} words</span>
                            <span>•</span>
                            <span>{dateStr}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                        <button
                          type="button"
                          onClick={() => onUseDocumentInComparison(doc)}
                          className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold border border-indigo-200/80 transition flex items-center gap-1.5"
                        >
                          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                          <span>Compare</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setPreviewDoc({ id: doc.document_id, name: doc.filename })}
                          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
                          title="Preview Text"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        <button
                          type="button"
                          onClick={() => handleDeleteDocument(doc.document_id, doc.filename)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                          title="Delete Document"
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
      )}

      {/* ==================== TAB 2: COLLECTIONS ==================== */}
      {activeTab === 'collections' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Reference Collections
            </h2>
            <button
              type="button"
              onClick={() => setShowCreateCol(true)}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Collection</span>
            </button>
          </div>

          {showCreateCol && (
            <form
              onSubmit={handleCreateCollection}
              className="p-4 bg-white border border-indigo-200 rounded-xl shadow-xs space-y-3"
            >
              <h3 className="text-xs font-bold text-slate-900">Create New Collection</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Collection Name *"
                  value={newColName}
                  onChange={(e) => setNewColName(e.target.value)}
                  required
                  className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <input
                  type="text"
                  placeholder="Description (Optional)"
                  value={newColDesc}
                  onChange={(e) => setNewColDesc(e.target.value)}
                  className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowCreateCol(false)}
                  className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
                >
                  Save Collection
                </button>
              </div>
            </form>
          )}

          {collections.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-xs">
              <FolderOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">No collections yet</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Group reference documents together to run bulk background comparisons.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {collections.map((col) => (
                <div
                  key={col.collection_id}
                  onClick={() => handleSelectCollection(col)}
                  className={`p-5 rounded-2xl border cursor-pointer transition shadow-xs ${
                    selectedCol?.collection_id === col.collection_id
                      ? 'bg-indigo-50/60 border-indigo-400 ring-1 ring-indigo-300'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg border border-indigo-100">
                      <FolderOpen className="w-5 h-5 text-indigo-600" />
                    </div>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                      {col.document_count} doc(s)
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mt-3 truncate">{col.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {col.description || 'No description provided.'}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Collection Inspector View */}
          {selectedCol && (
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Collection: {selectedCol.name}
                  </h3>
                  <p className="text-xs text-slate-500">{selectedCol.description}</p>
                </div>
                <button
                  onClick={() => setSelectedCol(null)}
                  className="text-xs text-slate-400 hover:text-slate-600"
                >
                  Close
                </button>
              </div>

              {/* Add document to collection */}
              <div className="flex items-center gap-2">
                <select
                  value={addDocId}
                  onChange={(e) => setAddDocId(e.target.value)}
                  className="flex-1 text-xs bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800"
                >
                  <option value="">-- Choose document to add --</option>
                  {documents
                    .filter((d) => !colDocs.some((cd) => cd.document_id === d.document_id))
                    .map((d) => (
                      <option key={d.document_id} value={d.document_id}>
                        {d.filename}
                      </option>
                    ))}
                </select>
                <button
                  type="button"
                  disabled={!addDocId}
                  onClick={handleAddDocToCollection}
                  className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold"
                >
                  Add Document
                </button>
              </div>

              {loadingColDocs ? (
                <div className="text-center py-6 text-xs text-slate-400">Loading collection documents...</div>
              ) : colDocs.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-500">
                  No documents in this collection yet. Select a document above to add it.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden">
                  {colDocs.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="p-3 flex items-center justify-between text-xs hover:bg-slate-50"
                    >
                      <span className="font-medium text-slate-800 truncate">{doc.filename}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveDocFromCollection(doc.document_id)}
                        className="text-slate-400 hover:text-rose-600 p-1"
                        title="Remove from collection"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Preview Modal */}
      {previewDoc && (
        <TextPreviewModal
          isOpen={Boolean(previewDoc)}
          documentId={previewDoc.id}
          filename={previewDoc.name}
          onClose={() => setPreviewDoc(null)}
        />
      )}
    </div>
  );
};

export default MyDocumentsPage;
