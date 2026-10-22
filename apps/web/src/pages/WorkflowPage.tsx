import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  Cpu,
  Layers,
  ArrowRight,
  FileCheck,
  AlertCircle,
  RefreshCw,
  Languages,
  Sparkles,
  ChevronLeft,
} from 'lucide-react';
import { documentsApi } from '../lib/api/documents';
import { analysesApi } from '../lib/api/analyses';
import { DocumentMetadata, DetectionMode, Collection } from '../types/generated/api';

interface WorkflowPageProps {
  onSelectAnalysis: (analysisId: string) => void;
  onNavigateToLibrary: () => void;
  onNavigateToHistory?: () => void;
  initialSubmissionDoc?: DocumentMetadata | null;
}

export const WorkflowPage: React.FC<WorkflowPageProps> = ({
  onSelectAnalysis,
  onNavigateToLibrary,
  onNavigateToHistory,
  initialSubmissionDoc,
}) => {
  // Workflow Stages: upload -> compare -> analyze -> running
  const [currentStage, setCurrentStage] = useState<'upload' | 'compare' | 'analyze' | 'running'>(
    initialSubmissionDoc ? 'compare' : 'upload'
  );

  // Stage 1 State: Submission Document
  const [submissionDoc, setSubmissionDoc] = useState<DocumentMetadata | null>(initialSubmissionDoc || null);
  const [isUploadingSub, setIsUploadingSub] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [subError, setSubError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Stage 2 State: Comparison Mode & References
  const [comparisonType, setComparisonType] = useState<'upload' | 'documents' | 'collection'>('upload');
  const [referenceDoc, setReferenceDoc] = useState<DocumentMetadata | null>(null);
  const [isUploadingRef, setIsUploadingRef] = useState(false);
  const [refError, setRefError] = useState<string | null>(null);
  const [refDragActive, setRefDragActive] = useState(false);
  const refFileInputRef = useRef<HTMLInputElement>(null);

  // Available library documents & collections
  const [libraryDocs, setLibraryDocs] = useState<DocumentMetadata[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  const [isLoadingReferences, setIsLoadingReferences] = useState(false);

  // Stage 3 State: Detection Mode
  const [detectionMode, setDetectionMode] = useState<DetectionMode>('hybrid');

  // Stage 4 State: Running Analysis
  const [runningStep, setRunningStep] = useState<string>('Initializing analysis...');
  const [runningPercent, setRunningPercent] = useState<number>(0);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    if (initialSubmissionDoc) {
      setSubmissionDoc(initialSubmissionDoc);
      setCurrentStage('compare');
    }
  }, [initialSubmissionDoc]);

  // Load Library & Collections when switching to reference selection
  useEffect(() => {
    if (currentStage === 'compare') {
      loadReferenceOptions();
    }
  }, [currentStage, submissionDoc]);

  const loadReferenceOptions = async () => {
    setIsLoadingReferences(true);
    try {
      const [docsRes, colsRes] = await Promise.all([
        documentsApi.listDocuments(50, 0),
        documentsApi.listCollections(50, 0),
      ]);
      const availableDocs = docsRes.items.filter(
        (d) => d.document_id !== submissionDoc?.document_id && d.status === 'completed'
      );
      setLibraryDocs(availableDocs);
      setCollections(colsRes.items || []);
      if (availableDocs.length > 0 && selectedDocIds.length === 0) {
        setSelectedDocIds([availableDocs[0].document_id]);
      }
      if (colsRes.items && colsRes.items.length > 0 && !selectedCollectionId) {
        setSelectedCollectionId(colsRes.items[0].collection_id);
      }
    } catch {
      // Gracefully continue
    } finally {
      setIsLoadingReferences(false);
    }
  };

  // Drag & Drop for Submission
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDropSub = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUploadSubmission(e.dataTransfer.files[0]);
    }
  };

  const handleUploadSubmission = async (file: File) => {
    setSubError(null);
    setIsUploadingSub(true);
    setUploadProgress(20);

    try {
      const timer = setInterval(() => {
        setUploadProgress((prev) => (prev < 90 ? prev + 15 : prev));
      }, 150);

      const doc = await documentsApi.uploadDocument(file);
      clearInterval(timer);
      setUploadProgress(100);

      const completedDoc = await documentsApi.pollDocumentUntilComplete(doc.document_id);
      setSubmissionDoc(completedDoc);
      setCurrentStage('compare');
    } catch (err: any) {
      setSubError(err?.message || 'Failed to upload document. Please ensure a valid PDF, DOCX, or TXT file.');
    } finally {
      setIsUploadingSub(false);
      setUploadProgress(0);
    }
  };

  // Handle Reference Document Upload
  const handleDropRef = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setRefDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUploadReference(e.dataTransfer.files[0]);
    }
  };

  const handleUploadReference = async (file: File) => {
    setRefError(null);
    setIsUploadingRef(true);
    try {
      const doc = await documentsApi.uploadDocument(file);
      const completedDoc = await documentsApi.pollDocumentUntilComplete(doc.document_id);
      setReferenceDoc(completedDoc);
    } catch (err: any) {
      setRefError(err?.message || 'Failed to upload reference document.');
    } finally {
      setIsUploadingRef(false);
    }
  };

  // Toggle selection for multiple library documents
  const toggleDocSelection = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  // Start Similarity Analysis
  const handleStartAnalysis = async () => {
    if (!submissionDoc) return;

    let payload: any = {
      submission_document_id: submissionDoc.document_id,
      detection_mode: detectionMode,
    };

    if (comparisonType === 'upload') {
      if (!referenceDoc) {
        setRefError('Please select or upload a reference document.');
        return;
      }
      payload.mode = 'direct';
      payload.reference_document_id = referenceDoc.document_id;
    } else if (comparisonType === 'documents') {
      if (selectedDocIds.length === 0) {
        setRefError('Please select at least one document from your library.');
        return;
      }
      if (selectedDocIds.length === 1) {
        payload.mode = 'direct';
        payload.reference_document_id = selectedDocIds[0];
      } else {
        payload.mode = 'one_to_many';
        payload.reference_document_ids = selectedDocIds;
      }
    } else if (comparisonType === 'collection') {
      if (!selectedCollectionId) {
        setRefError('Please select a reference collection.');
        return;
      }
      payload.mode = 'corpus';
      payload.collection_id = selectedCollectionId;
    }

    setCurrentStage('running');
    setRunningPercent(15);
    setRunningStep('Submitting document for similarity analysis...');
    setAnalysisError(null);

    try {
      const job = await analysesApi.createAnalysis(payload);

      const result = await analysesApi.pollAnalysisUntilComplete(
        job.analysis_id,
        (status) => {
          setRunningPercent(status.progress_percent || 45);
          if (status.current_step === 'loading_submission') {
            setRunningStep('Reading and normalizing document text...');
          } else if (status.current_step === 'resolving_candidates') {
            setRunningStep('Comparing document with reference sources...');
          } else if (status.current_step === 'lexical_alignment') {
            setRunningStep('Detecting exact and near-exact matching passages...');
          } else if (status.current_step === 'semantic_vector_search') {
            setRunningStep('Evaluating semantic meaning and translations...');
          } else if (status.current_step === 'saving_results') {
            setRunningStep('Generating similarity report & evidence...');
          }
        },
        1000,
        120
      );

      setRunningPercent(100);
      setRunningStep('Analysis completed!');
      setTimeout(() => {
        onSelectAnalysis(result.analysis_id);
      }, 400);
    } catch (err: any) {
      setAnalysisError(err?.message || 'Analysis failed. Please try again.');
      setCurrentStage('analyze');
    }
  };

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
    <div className="max-w-3xl mx-auto py-2 sm:py-6 space-y-6">
      {/* Workflow Step Indicator (Only displayed when in compare/analyze stages) */}
      {currentStage !== 'upload' && currentStage !== 'running' && (
        <div className="flex items-center justify-between px-4 sm:px-6 py-2.5 bg-white border border-slate-200/80 rounded-xl shadow-xs text-xs font-semibold">
          <button
            onClick={() => setCurrentStage('upload')}
            className="flex items-center gap-1.5 text-slate-600 hover:text-indigo-600 transition"
          >
            <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center text-[10px] font-bold">
              ✓
            </span>
            <span>1. Upload</span>
          </button>
          <div className="w-6 h-px bg-slate-200" />
          <div className={`flex items-center gap-1.5 ${currentStage === 'compare' ? 'text-indigo-600 font-bold' : 'text-slate-600'}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${currentStage === 'compare' ? 'bg-indigo-600 text-white' : 'bg-emerald-100 text-emerald-800'}`}>
              {currentStage === 'analyze' ? '✓' : '2'}
            </span>
            <span>2. Compare</span>
          </div>
          <div className="w-6 h-px bg-slate-200" />
          <div className={`flex items-center gap-1.5 ${currentStage === 'analyze' ? 'text-indigo-600 font-bold' : 'text-slate-400'}`}>
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${currentStage === 'analyze' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
              3
            </span>
            <span>3. Analyze</span>
          </div>
        </div>
      )}

      {/* ==================== STAGE 1: UPLOAD (HOMEPAGE) ==================== */}
      {currentStage === 'upload' && (
        <div className="space-y-6 py-4">
          <div className="text-center space-y-2">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Check Document Similarity
            </h1>
            <p className="text-slate-500 text-sm max-w-lg mx-auto">
              Upload a document, compare it with your references, and review matching passages.
            </p>
          </div>

          {/* Central Hero Upload Card */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDropSub}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-2xl p-10 sm:p-14 text-center transition-all border-2 border-dashed ${
              dragActive
                ? 'border-indigo-600 bg-indigo-50/60 shadow-md scale-[1.01]'
                : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50/80 shadow-xs'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleUploadSubmission(e.target.files[0]);
                }
              }}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-xs">
                {isUploadingSub ? (
                  <RefreshCw className="w-7 h-7 animate-spin text-indigo-600" />
                ) : (
                  <UploadCloud className="w-7 h-7 text-indigo-600" />
                )}
              </div>

              <div>
                <button
                  type="button"
                  disabled={isUploadingSub}
                  className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm shadow-sm transition active:scale-95"
                >
                  {isUploadingSub ? 'Processing Document...' : 'Select Document'}
                </button>
                <p className="text-xs text-slate-500 mt-2.5 font-medium">
                  Drop your document here
                </p>
              </div>

              {isUploadingSub && (
                <div className="w-full max-w-xs space-y-1 pt-2">
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <span className="text-[11px] text-slate-500">Extracting text & validating content...</span>
                </div>
              )}

              {subError && (
                <div className="flex items-center text-rose-600 text-xs font-medium bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-lg mt-2">
                  <AlertCircle className="w-4 h-4 mr-1.5 flex-shrink-0" />
                  {subError}
                </div>
              )}

              <div className="flex flex-wrap items-center justify-center gap-2 pt-4 border-t border-slate-100 text-slate-400 text-xs">
                <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded font-medium text-[11px]">
                  PDF
                </span>
                <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded font-medium text-[11px]">
                  DOCX
                </span>
                <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded font-medium text-[11px]">
                  TXT
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-slate-500">Up to 32 MB</span>
                <span className="text-slate-300">•</span>
                <span className="flex items-center text-slate-500">
                  <Languages className="w-3.5 h-3.5 mr-1 text-indigo-500" />
                  English • Hindi • Telugu
                </span>
              </div>
            </div>
          </div>

          {/* Quick Navigation Links Below Upload */}
          <div className="text-center text-xs text-slate-500 space-x-3 pt-2">
            <span>Or manage existing files in</span>
            <button
              type="button"
              onClick={onNavigateToLibrary}
              className="text-indigo-600 hover:text-indigo-800 font-semibold underline"
            >
              My Documents
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={onNavigateToHistory}
              className="text-indigo-600 hover:text-indigo-800 font-semibold underline"
            >
              View History
            </button>
          </div>
        </div>
      )}

      {/* ==================== STAGE 2: COMPARE ==================== */}
      {currentStage === 'compare' && submissionDoc && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Choose Reference Document</h2>
              <p className="text-xs text-slate-500">Select or upload the reference file you want to compare against.</p>
            </div>
            <button
              onClick={() => {
                setSubmissionDoc(null);
                setCurrentStage('upload');
              }}
              className="text-xs text-slate-500 hover:text-slate-800 underline font-medium"
            >
              Change Document
            </button>
          </div>

          {/* Uploaded Submission Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg border border-indigo-100">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <div className="font-semibold text-slate-900 text-sm">{submissionDoc.filename}</div>
                <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                  <span>{(submissionDoc.file_size_bytes / 1024).toFixed(1)} KB</span>
                  <span>•</span>
                  <span>{submissionDoc.word_count || Math.round(submissionDoc.char_count / 5)} words</span>
                  <span>•</span>
                  <span className="px-1.5 py-0.2 bg-slate-100 text-slate-700 rounded text-[10px] font-medium">
                    {getLanguageLabel(submissionDoc.detected_language)}
                  </span>
                </div>
              </div>
            </div>
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
              Ready
            </span>
          </div>

          {/* Reference Document Selector */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3 flex-wrap">
              <button
                type="button"
                onClick={() => setComparisonType('upload')}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                  comparisonType === 'upload'
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Upload Reference File
              </button>
              <button
                type="button"
                onClick={() => setComparisonType('documents')}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                  comparisonType === 'documents'
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Choose from My Documents
              </button>
              <button
                type="button"
                onClick={() => setComparisonType('collection')}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                  comparisonType === 'collection'
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Choose Reference Collection
              </button>
            </div>

            {/* Option 1: Direct File Upload */}
            {comparisonType === 'upload' && (
              <div>
                {referenceDoc ? (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-amber-50 text-amber-600 rounded-lg border border-amber-200">
                        <FileCheck className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-semibold text-slate-900 text-sm">{referenceDoc.filename}</div>
                        <div className="text-xs text-slate-500">
                          {getLanguageLabel(referenceDoc.detected_language)} • {referenceDoc.char_count} chars
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => setReferenceDoc(null)}
                      className="text-xs text-slate-500 hover:text-slate-800 underline font-medium"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDropRef}
                    onClick={() => refFileInputRef.current?.click()}
                    className={`cursor-pointer rounded-xl p-8 text-center border-2 border-dashed transition ${
                      refDragActive
                        ? 'border-indigo-600 bg-indigo-50/50'
                        : 'border-slate-300 hover:border-indigo-400 bg-slate-50/50'
                    }`}
                  >
                    <input
                      ref={refFileInputRef}
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          handleUploadReference(e.target.files[0]);
                        }
                      }}
                      className="hidden"
                    />
                    <div className="flex flex-col items-center space-y-2">
                      <UploadCloud className="w-6 h-6 text-slate-400" />
                      <div className="text-xs font-semibold text-indigo-600 hover:underline">
                        {isUploadingRef ? 'Uploading reference...' : 'Select or drop Reference Document'}
                      </div>
                      <span className="text-[11px] text-slate-400">PDF, DOCX, or TXT up to 32 MB</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Option 2: Choose from My Documents */}
            {comparisonType === 'documents' && (
              <div className="space-y-3">
                {isLoadingReferences ? (
                  <div className="text-center py-6 text-xs text-slate-400">Loading documents...</div>
                ) : libraryDocs.length > 0 ? (
                  <div className="max-h-56 overflow-y-auto space-y-1.5 border border-slate-200 rounded-lg p-2 bg-slate-50/50">
                    {libraryDocs.map((doc) => {
                      const isSelected = selectedDocIds.includes(doc.document_id);
                      return (
                        <div
                          key={doc.document_id}
                          onClick={() => toggleDocSelection(doc.document_id)}
                          className={`p-2.5 rounded-lg border text-xs flex items-center justify-between cursor-pointer transition ${
                            isSelected
                              ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-medium'
                              : 'bg-white border-slate-200 hover:border-slate-300 text-slate-700'
                          }`}
                        >
                          <div className="flex items-center space-x-2 truncate">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {}}
                              className="rounded text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="truncate">{doc.filename}</span>
                          </div>
                          <span className="text-[11px] text-slate-500 flex-shrink-0">
                            {getLanguageLabel(doc.detected_language)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-6 text-xs text-slate-500">
                    No documents available in library.{' '}
                    <button
                      onClick={onNavigateToLibrary}
                      className="text-indigo-600 font-semibold underline"
                    >
                      Go to My Documents
                    </button>
                  </div>
                )}
                <p className="text-[11px] text-slate-400">
                  Select one or more reference files to compare against.
                </p>
              </div>
            )}

            {/* Option 3: Choose Reference Collection */}
            {comparisonType === 'collection' && (
              <div className="space-y-3">
                {collections.length > 0 ? (
                  <select
                    value={selectedCollectionId}
                    onChange={(e) => setSelectedCollectionId(e.target.value)}
                    className="w-full text-xs bg-white border border-slate-300 rounded-lg p-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {collections.map((col) => (
                      <option key={col.collection_id} value={col.collection_id}>
                        {col.name} ({col.document_count} documents)
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="text-center py-6 text-xs text-slate-500">
                    No collections created yet.{' '}
                    <button
                      onClick={onNavigateToLibrary}
                      className="text-indigo-600 font-semibold underline"
                    >
                      Create a collection in My Documents
                    </button>
                  </div>
                )}
              </div>
            )}

            {refError && (
              <div className="text-xs text-rose-600 font-medium bg-rose-50 p-2.5 rounded-lg border border-rose-200">
                {refError}
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                disabled={
                  comparisonType === 'upload'
                    ? !referenceDoc
                    : comparisonType === 'documents'
                    ? selectedDocIds.length === 0
                    : !selectedCollectionId
                }
                onClick={() => {
                  setRefError(null);
                  setCurrentStage('analyze');
                }}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg text-xs shadow-xs transition flex items-center disabled:opacity-50"
              >
                Continue to Analysis
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== STAGE 3: ANALYZE ==================== */}
      {currentStage === 'analyze' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Choose Detection Mode</h2>
              <p className="text-xs text-slate-500">Select the analysis mode calibrated for your document type.</p>
            </div>
            <button
              onClick={() => setCurrentStage('compare')}
              className="text-xs text-slate-500 hover:text-slate-800 underline font-medium flex items-center"
            >
              <ChevronLeft className="w-3.5 h-3.5 mr-1" />
              Back
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Mode 1: Hybrid AI (Recommended) */}
            <div
              onClick={() => setDetectionMode('hybrid')}
              className={`p-5 rounded-xl border-2 cursor-pointer transition ${
                detectionMode === 'hybrid'
                  ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
                  <Sparkles className="w-5 h-5 text-indigo-600" />
                </div>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-indigo-600 text-white">
                  Recommended
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900">Hybrid AI</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Combines exact text matching with semantic AI. Identifies verbatim copies, paraphrases, and multilingual translations.
              </p>
            </div>

            {/* Mode 2: Exact Matching */}
            <div
              onClick={() => setDetectionMode('lexical')}
              className={`p-5 rounded-xl border-2 cursor-pointer transition ${
                detectionMode === 'lexical'
                  ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-amber-100 text-amber-700 rounded-lg">
                  <Layers className="w-5 h-5 text-amber-600" />
                </div>
              </div>
              <h3 className="text-sm font-bold text-slate-900">Exact Text Matching</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Fast word-for-word copy-paste detection and verbatim sentence alignment.
              </p>
            </div>

            {/* Mode 3: Meaning-Based Matching */}
            <div
              onClick={() => setDetectionMode('semantic')}
              className={`p-5 rounded-xl border-2 cursor-pointer transition ${
                detectionMode === 'semantic'
                  ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-purple-100 text-purple-700 rounded-lg">
                  <Cpu className="w-5 h-5 text-purple-600" />
                </div>
              </div>
              <h3 className="text-sm font-bold text-slate-900">Meaning-Based Matching</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Detects paraphrased passages, structural rewrites, and translated content.
              </p>
            </div>
          </div>

          {analysisError && (
            <div className="text-xs text-rose-600 font-medium bg-rose-50 p-3 rounded-lg border border-rose-200">
              {analysisError}
            </div>
          )}

          <div className="pt-2 flex justify-center">
            <button
              type="button"
              onClick={handleStartAnalysis}
              className="px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm shadow-md transition active:scale-95 flex items-center"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Check Similarity
            </button>
          </div>
        </div>
      )}

      {/* ==================== STAGE 4: RUNNING PROGRESS ==================== */}
      {currentStage === 'running' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-10 sm:p-14 text-center shadow-xs space-y-6">
          <div className="w-14 h-14 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center mx-auto text-indigo-600">
            <RefreshCw className="w-7 h-7 animate-spin text-indigo-600" />
          </div>

          <div className="space-y-1.5">
            <h2 className="text-xl font-bold text-slate-900">Checking Document Similarity...</h2>
            <p className="text-xs text-slate-500 max-w-md mx-auto">{runningStep}</p>
          </div>

          <div className="max-w-md mx-auto space-y-1.5">
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                style={{ width: `${runningPercent}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-400 font-mono">
              <span>{runningPercent}%</span>
              <span>Processing</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowPage;
