import React, { useEffect, useState, useRef } from 'react';
import {
  AnalysisResult,
  SimilarityFinding,
} from '../types/generated/api';
import { analysesApi } from '../lib/api/analyses';
import { documentsApi } from '../lib/api/documents';
import {
  Download,
  Printer,
  CheckCircle2,
  Ban,
  Quote,
  Flag,
  FileText,
  ChevronDown,
  ChevronUp,
  Check,
  ArrowLeft,
  Loader2,
  AlertCircle,
} from 'lucide-react';

interface ResultsDashboardPageProps {
  analysisId: string;
  onBackToIngestion: () => void;
  onOpenHistory?: () => void;
}

interface HighlightSpan {
  start: number;
  end: number;
  findingId: string;
  category: string;
}

export const ResultsDashboardPage: React.FC<ResultsDashboardPageProps> = ({
  analysisId,
  onBackToIngestion,
  onOpenHistory,
}) => {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Selected state for inspection
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  // Raw text cache for highlighting
  const [submissionText, setSubmissionText] = useState<string>('');
  const [referenceText, setReferenceText] = useState<string>('');
  const [isLoadingRefText, setIsLoadingRefText] = useState<boolean>(false);

  // Reviewer action state
  const [reviewerNotesDraft, setReviewerNotesDraft] = useState<string>('');
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Download state
  const [showDownloadMenu, setShowDownloadMenu] = useState<boolean>(false);
  const [downloadingFormat, setDownloadingFormat] = useState<'pdf' | 'html' | 'json' | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadReport = async (format: 'pdf' | 'html' | 'json') => {
    setShowDownloadMenu(false);
    setDownloadingFormat(format);
    setDownloadError(null);

    try {
      const url = `/api/v1/analyses/${analysisId}/report?format=${format}`;
      const headers = new Headers();
      headers.set('X-Request-ID', `web-dl-${Date.now()}`);
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }

      const response = await fetch(url, { headers });

      if (!response.ok) {
        let errMsg = `Failed to generate ${format.toUpperCase()} report (HTTP ${response.status})`;
        try {
          const errJson = await response.json();
          if (errJson?.error?.message) {
            errMsg = errJson.error.message;
          } else if (errJson?.detail) {
            errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          // ignore
        }
        throw new Error(errMsg);
      }

      // Extract filename from Content-Disposition header if available
      let filename = '';
      const disposition = response.headers.get('Content-Disposition');
      if (disposition) {
        const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
        if (utfMatch && utfMatch[1]) {
          filename = decodeURIComponent(utfMatch[1]);
        } else {
          const match = disposition.match(/filename="?([^";]+)"?/i);
          if (match && match[1]) {
            filename = match[1];
          }
        }
      }

      if (!filename) {
        const rawName = (result?.submission_filename || 'Similarity_Report').replace(/\.[^/.]+$/, '');
        const cleanName = rawName.replace(/[^a-zA-Z0-9_\-\.]/g, '_');
        filename = `${cleanName}_Similarity_Report.${format}`;
      }

      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => {
        window.URL.revokeObjectURL(objectUrl);
      }, 1000);
    } catch (err: any) {
      console.error('Download error:', err);
      setDownloadError(err?.message || `Your ${format.toUpperCase()} report couldn't be generated. Please try again.`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  // Detailed breakdown toggle
  const [showDetailedBreakdown, setShowDetailedBreakdown] = useState<boolean>(false);

  // Scroll references for side-by-side inspection
  const subTextContainerRef = useRef<HTMLDivElement>(null);
  const refTextContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadAnalysisResults();
  }, [analysisId]);

  const loadAnalysisResults = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analysesApi.getAnalysisResult(analysisId);
      setResult(data);

      if (data.submission_document_id) {
        const subPreview = await documentsApi.getDocumentText(data.submission_document_id);
        setSubmissionText(subPreview.raw_text);
      }

      if (data.sources && data.sources.length > 0) {
        const firstSrc = data.sources[0];
        setSelectedSourceId(firstSrc.reference_document_id);
        loadReferenceText(firstSrc.reference_document_id);
      }

      if (data.findings && data.findings.length > 0) {
        const f0 = data.findings[0];
        setSelectedFindingId(f0.finding_id);
        setReviewerNotesDraft(f0.reviewer_notes || '');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load analysis results.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadReferenceText = async (refDocId: string) => {
    setIsLoadingRefText(true);
    try {
      const refPreview = await documentsApi.getDocumentText(refDocId);
      setReferenceText(refPreview.raw_text);
    } catch {
      setReferenceText('');
    } finally {
      setIsLoadingRefText(false);
    }
  };

  const handleSelectSource = (srcId: string) => {
    setSelectedSourceId(srcId);
    loadReferenceText(srcId);
    if (result) {
      const srcFinding = result.findings.find((f) => f.reference_document_id === srcId);
      if (srcFinding) {
        handleSelectFinding(srcFinding);
      }
    }
  };

  const handleSelectFinding = (finding: SimilarityFinding) => {
    setSelectedFindingId(finding.finding_id);
    setReviewerNotesDraft(finding.reviewer_notes || '');
    setSaveSuccessMsg(null);
    if (finding.reference_document_id !== selectedSourceId) {
      setSelectedSourceId(finding.reference_document_id);
      loadReferenceText(finding.reference_document_id);
    }

    // Scroll to active highlight in dual pane
    setTimeout(() => {
      const activeMark = document.querySelector(`mark[data-finding-id="${finding.finding_id}"]`);
      if (activeMark) {
        activeMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  // Submit human reviewer decision
  const handleReviewDecision = async (
    decision: 'keep' | 'exclude' | 'quoted_cited' | 'needs_review',
    notesOverride?: string
  ) => {
    if (!selectedFindingId || !result) return;
    setIsSubmittingReview(true);
    setSaveSuccessMsg(null);
    try {
      const noteToSave = notesOverride !== undefined ? notesOverride : reviewerNotesDraft;
      const resp = await analysesApi.reviewFinding(
        result.analysis_id,
        selectedFindingId,
        decision,
        noteToSave
      );

      const updatedFindings = result.findings.map((f) =>
        f.finding_id === selectedFindingId ? resp.finding : f
      );

      setResult({
        ...result,
        findings: updatedFindings,
        reviewer_adjusted_coverage_percent: resp.reviewer_adjusted_coverage_percent,
        reviewed_findings_count: resp.reviewed_findings_count,
      });

      setSaveSuccessMsg(`Decision saved: ${decision.replace('_', ' ')}`);
      setTimeout(() => setSaveSuccessMsg(null), 3000);
    } catch (err: any) {
      alert(`Error saving decision: ${err.message}`);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  // Safe Highlight Renderer with precise Unicode character offsets
  const renderHighlightedContent = (
    fullText: string,
    spans: HighlightSpan[],
    activeFindingId: string | null,
    onSpanClick: (findingId: string) => void
  ) => {
    if (!fullText) {
      return <span className="text-slate-400 italic">No document text available.</span>;
    }
    if (!spans || spans.length === 0) {
      return <span>{fullText}</span>;
    }

    const sorted = [...spans].sort((a, b) => a.start - b.start);
    const elements: React.ReactNode[] = [];
    let cursor = 0;

    sorted.forEach((span, idx) => {
      const s = Math.max(0, Math.min(fullText.length, span.start));
      const e = Math.max(s, Math.min(fullText.length, span.end));

      if (s > cursor) {
        elements.push(<span key={`plain-${idx}`}>{fullText.slice(cursor, s)}</span>);
      }

      if (e > s) {
        const isSelected = span.findingId === activeFindingId;
        const isExact = span.category === 'exact_copy';
        const isNearExact = span.category === 'near_exact_rewrite';
        const isTranslation = span.category === 'potential_translation';

        let bgClass = '';
        if (isSelected) {
          if (isExact) bgClass = 'bg-rose-200 text-rose-950 ring-2 ring-rose-400 font-medium';
          else if (isNearExact) bgClass = 'bg-amber-200 text-amber-950 ring-2 ring-amber-400 font-medium';
          else if (isTranslation) bgClass = 'bg-sky-200 text-sky-950 ring-2 ring-sky-400 font-medium';
          else bgClass = 'bg-purple-200 text-purple-950 ring-2 ring-purple-400 font-medium';
        } else {
          if (isExact) bgClass = 'bg-rose-100/90 text-rose-900 border-b-2 border-rose-400 hover:bg-rose-200';
          else if (isNearExact) bgClass = 'bg-amber-100/90 text-amber-900 border-b-2 border-amber-400 hover:bg-amber-200';
          else if (isTranslation) bgClass = 'bg-sky-100/90 text-sky-900 border-b-2 border-sky-400 hover:bg-sky-200';
          else bgClass = 'bg-purple-100/90 text-purple-900 border-b-2 border-purple-400 hover:bg-purple-200';
        }

        elements.push(
          <mark
            key={`mark-${idx}`}
            data-finding-id={span.findingId}
            onClick={() => onSpanClick(span.findingId)}
            className={`rounded px-1 py-0.5 cursor-pointer transition-all ${bgClass}`}
            title={`Finding: ${span.category} (Click to inspect)`}
          >
            {fullText.slice(s, e)}
          </mark>
        );
      }

      cursor = Math.max(cursor, e);
    });

    if (cursor < fullText.length) {
      elements.push(<span key="plain-tail">{fullText.slice(cursor)}</span>);
    }

    return <>{elements}</>;
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 space-y-4">
        <div className="w-10 h-10 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-800 text-sm font-semibold">Loading Similarity Results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="bg-white border border-rose-200 rounded-2xl p-8 max-w-lg mx-auto my-12 text-center shadow-xs">
        <h3 className="text-base font-bold text-rose-700 mb-2">Results Unavailable</h3>
        <p className="text-slate-600 text-xs mb-6">{error || 'Unknown error occurred while fetching results.'}</p>
        <button
          onClick={onBackToIngestion}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
        >
          Return to Home
        </button>
      </div>
    );
  }

  const findingsList = result.findings || [];
  const sourcesList = result.sources || [];
  const activeFinding = findingsList.find((f) => f.finding_id === selectedFindingId) || findingsList[0] || null;

  const submissionSpans: HighlightSpan[] = findingsList.map((f) => ({
    start: f.submission_start_offset,
    end: f.submission_end_offset,
    findingId: f.finding_id,
    category: f.category,
  }));

  const referenceSpans: HighlightSpan[] = findingsList
    .filter((f) => f.reference_document_id === selectedSourceId)
    .map((f) => ({
      start: f.reference_start_offset,
      end: f.reference_end_offset,
      findingId: f.finding_id,
      category: f.category,
    }));

  const origScore = result.hybrid_evidence_coverage_percent ?? result.overall_lexical_coverage_percent ?? 0;
  const adjScore = result.reviewer_adjusted_coverage_percent ?? origScore;
  const hasReviewerEdits = (result.reviewed_findings_count ?? 0) > 0;

  // Status counts
  const keptCount = findingsList.filter((f) => f.review_decision === 'keep').length;
  const excludedCount = findingsList.filter((f) => f.review_decision === 'exclude' || f.is_excluded).length;
  const quotedCount = findingsList.filter((f) => f.review_decision === 'quoted_cited' || f.is_quoted).length;
  const needsReviewCount = findingsList.filter((f) => !f.review_decision || f.review_decision === 'unreviewed' || f.review_decision === 'needs_review').length;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Report Actions */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Similarity Results
            </h1>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/80 uppercase">
              {result.detection_mode || 'Hybrid'}
            </span>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">
              {result.status}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Document:{' '}
            <strong className="text-slate-800 font-medium">
              {result.submission_filename || result.submission_document_id}
            </strong>
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {onOpenHistory && (
            <button
              onClick={onOpenHistory}
              className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium border border-slate-300 transition shadow-xs"
            >
              History
            </button>
          )}

          {/* Download Report Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDownloadMenu(!showDownloadMenu)}
              disabled={downloadingFormat !== null}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer"
            >
              {downloadingFormat ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Generating {downloadingFormat.toUpperCase()}...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Report</span>
                  <ChevronDown className="w-3.5 h-3.5" />
                </>
              )}
            </button>

            {showDownloadMenu && (
              <div className="absolute right-0 mt-1 w-52 bg-white border border-slate-200 rounded-xl shadow-lg z-50 py-1.5 text-xs text-slate-700">
                <button
                  type="button"
                  onClick={() => handleDownloadReport('pdf')}
                  className="w-full flex items-center px-3.5 py-2 hover:bg-slate-50 font-medium text-slate-800 text-left transition"
                >
                  <FileText className="w-4 h-4 mr-2 text-indigo-600 flex-shrink-0" />
                  <span>PDF Report (Recommended)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDownloadReport('html')}
                  className="w-full flex items-center px-3.5 py-2 hover:bg-slate-50 text-slate-700 text-left transition"
                >
                  <FileText className="w-4 h-4 mr-2 text-slate-400 flex-shrink-0" />
                  <span>Printable HTML</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDownloadReport('json')}
                  className="w-full flex items-center px-3.5 py-2 hover:bg-slate-50 text-slate-700 text-left transition"
                >
                  <FileText className="w-4 h-4 mr-2 text-slate-400 flex-shrink-0" />
                  <span>Export JSON</span>
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => window.print()}
            title="Print report"
            className="p-1.5 bg-white hover:bg-slate-50 text-slate-600 border border-slate-300 rounded-lg shadow-xs"
          >
            <Printer className="w-4 h-4" />
          </button>

          <button
            onClick={onBackToIngestion}
            className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold transition flex items-center gap-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back</span>
          </button>
        </div>
      </div>

      {/* Download Error Banner */}
      {downloadError && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-rose-700 shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{downloadError}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDownloadReport('pdf')}
              className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded font-medium text-xs shadow-xs transition"
            >
              Retry PDF
            </button>
            <button
              onClick={() => setDownloadError(null)}
              className="px-2 py-1 text-rose-600 hover:bg-rose-100 rounded text-xs transition"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Compact Summary Cards (3 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Card 1: Evidence Coverage */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs relative overflow-hidden">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            {hasReviewerEdits ? 'Adjusted Evidence Coverage' : 'Overall Evidence Coverage'}
          </div>
          <div className="text-3xl font-extrabold text-indigo-600 mt-1">
            {`${(hasReviewerEdits ? adjScore : origScore).toFixed(1)}%`}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {hasReviewerEdits ? `Original: ${origScore.toFixed(1)}%` : 'Combined matching passage coverage'}
          </p>
          <div
            className="absolute bottom-0 left-0 h-1 bg-indigo-600"
            style={{ width: `${Math.min(100, hasReviewerEdits ? adjScore : origScore)}%` }}
          />
        </div>

        {/* Card 2: Matching Sources */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Matching Sources</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-1">{result.matched_source_count}</div>
          <p className="text-xs text-slate-400 mt-1">Distinct reference documents</p>
        </div>

        {/* Card 3: Findings Requiring Review */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Findings Requiring Review</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-1">
            {needsReviewCount}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {result.total_findings_count} total detected passages
          </p>
        </div>
      </div>

      {/* Optional Expanded Breakdown Toggle */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-xs">
        <button
          type="button"
          onClick={() => setShowDetailedBreakdown(!showDetailedBreakdown)}
          className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 hover:text-indigo-600 transition"
        >
          <span>Detailed Coverage Breakdown & Scoring</span>
          {showDetailedBreakdown ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showDetailedBreakdown && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 mt-3 border-t border-slate-100 text-xs">
            <div className="p-3 bg-amber-50/60 border border-amber-200/70 rounded-lg">
              <span className="text-[11px] font-bold text-amber-800 uppercase">Lexical Matching</span>
              <div className="text-xl font-bold text-amber-700 mt-0.5">
                {(result.overall_lexical_coverage_percent ?? 0).toFixed(1)}%
              </div>
              <p className="text-[11px] text-amber-600 mt-0.5">Exact token overlap (Winnowing)</p>
            </div>

            <div className="p-3 bg-purple-50/60 border border-purple-200/70 rounded-lg">
              <span className="text-[11px] font-bold text-purple-800 uppercase">Semantic AI Matching</span>
              <div className="text-xl font-bold text-purple-700 mt-0.5">
                {(result.overall_semantic_coverage_percent ?? 0).toFixed(1)}%
              </div>
              <p className="text-[11px] text-purple-600 mt-0.5">Paraphrase passages (E5 embeddings)</p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="text-[11px] font-bold text-slate-700 uppercase">Total Findings</span>
              <div className="text-xl font-bold text-slate-800 mt-0.5">
                {result.total_findings_count}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {keptCount} Kept • {excludedCount} Excluded
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Reviewer Status Tally Bar */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-slate-700">Review Status:</span>
          <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full font-medium border border-emerald-200">
            {keptCount} Kept
          </span>
          <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full font-medium border border-slate-200">
            {excludedCount} Excluded
          </span>
          <span className="px-2 py-0.5 bg-sky-50 text-sky-700 rounded-full font-medium border border-sky-200">
            {quotedCount} Quoted/Cited
          </span>
          {needsReviewCount > 0 && (
            <span className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded-full font-medium border border-amber-200">
              {needsReviewCount} Needs Review
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 text-slate-500 text-[11px] flex-wrap">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-rose-200 border border-rose-400 inline-block" /> Exact Copy
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-amber-200 border border-amber-400 inline-block" /> Near-Exact
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-purple-200 border border-purple-400 inline-block" /> Paraphrase
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-sky-200 border border-sky-400 inline-block" /> Cross-Language
          </span>
        </div>
      </div>

      {/* Matched Reference Sources List */}
      {sourcesList.length > 0 && (
        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
            Matching Reference Sources
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {sourcesList.map((src) => {
              const isSelected = src.reference_document_id === selectedSourceId;
              return (
                <div
                  key={src.reference_document_id}
                  onClick={() => handleSelectSource(src.reference_document_id)}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    isSelected
                      ? 'bg-indigo-50/70 border-indigo-400 ring-1 ring-indigo-300'
                      : 'bg-slate-50/50 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-900 truncate max-w-[180px]" title={src.source_title}>
                      {src.source_title}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {src.matched_passage_count} match(es)
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                    <span className="text-indigo-600 font-medium">{isSelected ? 'Active Source' : 'Click to inspect'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Dual Pane Side-by-Side Highlighted Document Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left Column: Submission Document */}
        <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden flex flex-col h-[520px] shadow-xs">
          <div className="bg-slate-50/80 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Submission Text
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">{submissionText.length} chars</span>
          </div>
          <div
            ref={subTextContainerRef}
            className="p-5 flex-1 overflow-y-auto font-serif text-sm leading-relaxed text-slate-800 select-text bg-white"
          >
            {renderHighlightedContent(submissionText, submissionSpans, selectedFindingId, (fid) => {
              const f = findingsList.find((x) => x.finding_id === fid);
              if (f) handleSelectFinding(f);
            })}
          </div>
        </div>

        {/* Right Column: Reference Document */}
        <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden flex flex-col h-[520px] shadow-xs">
          <div className="bg-slate-50/80 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Reference Source Text{' '}
                {selectedSourceId && (
                  <span className="text-slate-500 lowercase font-normal">
                    ({sourcesList.find((s) => s.reference_document_id === selectedSourceId)?.source_title || 'Document'})
                  </span>
                )}
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              {isLoadingRefText ? 'Loading...' : `${referenceText.length} chars`}
            </span>
          </div>
          <div
            ref={refTextContainerRef}
            className="p-5 flex-1 overflow-y-auto font-serif text-sm leading-relaxed text-slate-800 select-text bg-white"
          >
            {isLoadingRefText ? (
              <div className="flex items-center justify-center h-full text-slate-400 text-xs italic">
                Loading source text...
              </div>
            ) : (
              renderHighlightedContent(referenceText, referenceSpans, selectedFindingId, (fid) => {
                const f = findingsList.find((x) => x.finding_id === fid);
                if (f) handleSelectFinding(f);
              })
            )}
          </div>
        </div>
      </div>

      {/* Selected Finding Reviewer Inspector Card */}
      {activeFinding && (
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <span className="text-sm font-bold text-slate-900">Finding Review & Decision</span>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-semibold uppercase ${
                  activeFinding.category === 'exact_copy'
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : activeFinding.category === 'near_exact_rewrite'
                    ? 'bg-amber-50 text-amber-700 border border-amber-200'
                    : activeFinding.category === 'potential_translation'
                    ? 'bg-sky-50 text-sky-700 border border-sky-200'
                    : 'bg-purple-50 text-purple-700 border border-purple-200'
                }`}
              >
                {activeFinding.category.replace('_', ' ')}
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase bg-slate-100 text-slate-600">
                Confidence: {activeFinding.confidence}
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                Decision: {activeFinding.review_decision || 'Unreviewed'}
              </span>
            </div>

            <div className="text-xs text-slate-500 font-mono">
              Offsets: [{activeFinding.submission_start_offset} - {activeFinding.submission_end_offset}]
            </div>
          </div>

          {/* Excerpts Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="text-[10px] uppercase font-bold mb-1.5 text-indigo-700">
                Submission Excerpt
              </div>
              <p className="text-slate-800 leading-relaxed font-serif text-xs">{activeFinding.submission_excerpt}</p>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="text-[10px] uppercase font-bold mb-1.5 text-amber-700">
                Reference Excerpt ({activeFinding.reference_source_title})
              </div>
              <p className="text-slate-800 leading-relaxed font-serif text-xs">{activeFinding.reference_excerpt}</p>
            </div>
          </div>

          {/* Reviewer Action Controls */}
          <div className="pt-2 border-t border-slate-100 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <span className="text-xs font-bold text-slate-700">Reviewer Action:</span>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  disabled={isSubmittingReview}
                  onClick={() => handleReviewDecision('keep')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeFinding.review_decision === 'keep'
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Keep (Confirmed)
                </button>

                <button
                  type="button"
                  disabled={isSubmittingReview}
                  onClick={() => handleReviewDecision('exclude')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeFinding.review_decision === 'exclude' || activeFinding.is_excluded
                      ? 'bg-slate-700 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-700 border border-slate-200 hover:bg-slate-200'
                  }`}
                >
                  <Ban className="w-3.5 h-3.5" />
                  Exclude (False Positive)
                </button>

                <button
                  type="button"
                  disabled={isSubmittingReview}
                  onClick={() => handleReviewDecision('quoted_cited')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeFinding.review_decision === 'quoted_cited' || activeFinding.is_quoted
                      ? 'bg-sky-600 text-white shadow-xs'
                      : 'bg-sky-50 text-sky-800 border border-sky-200 hover:bg-sky-100'
                  }`}
                >
                  <Quote className="w-3.5 h-3.5" />
                  Quoted / Cited
                </button>

                <button
                  type="button"
                  disabled={isSubmittingReview}
                  onClick={() => handleReviewDecision('needs_review')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeFinding.review_decision === 'needs_review'
                      ? 'bg-amber-600 text-white shadow-xs'
                      : 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100'
                  }`}
                >
                  <Flag className="w-3.5 h-3.5" />
                  Needs Review
                </button>
              </div>
            </div>

            {/* Notes Input */}
            <div className="flex items-center gap-2 pt-1">
              <input
                type="text"
                value={reviewerNotesDraft}
                onChange={(e) => setReviewerNotesDraft(e.target.value)}
                placeholder="Optional reviewer notes / explanation..."
                className="flex-1 text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              <button
                type="button"
                disabled={isSubmittingReview}
                onClick={() => handleReviewDecision((activeFinding.review_decision as any) || 'keep', reviewerNotesDraft)}
                className="px-3 py-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 rounded-lg text-xs font-semibold transition"
              >
                Save Note
              </button>
            </div>

            {saveSuccessMsg && (
              <div className="text-[11px] text-emerald-700 font-semibold flex items-center gap-1">
                <Check className="w-3 h-3" />
                {saveSuccessMsg}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDashboardPage;
