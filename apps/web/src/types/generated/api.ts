/**
 * Contract-Derived TypeScript Interfaces
 * Conforms directly to contracts/openapi.yaml
 */

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  timestamp: string;
  database: 'connected' | 'disconnected';
  redis: 'connected' | 'disconnected';
  worker_pool: 'operational' | 'degraded';
  version?: string;
}

export interface ErrorDetail {
  field?: string;
  issue: string;
  location?: string;
  type?: string;
}

export interface ErrorBody {
  code: string;
  message: string;
  status: number;
  timestamp: string;
  request_id?: string;
  details?: ErrorDetail[];
}

export interface ErrorEnvelope {
  error: ErrorBody;
}

export type UserRole = 'STUDENT' | 'FACULTY' | 'RESEARCHER' | 'ADMIN';

export interface UserPrincipal {
  user_id: string;
  email: string;
  role: UserRole;
  display_name?: string;
}

export type ComparisonMode = 'direct' | 'one_to_many' | 'corpus';
export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type JobExecutionStage = 'extracting' | 'indexing' | 'analyzing' | 'aggregating';
export type MatchCategory = 'IDENTICAL' | 'PARAPHRASE' | 'CROSS_LINGUAL';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export interface PaginationMetadata {
  total_items: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface DocumentMetadata {
  document_id: string;
  filename: string;
  mime_type: string;
  sha256_hash: string;
  file_size_bytes: number;
  page_count: number;
  char_count: number;
  word_count?: number;
  detected_language: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  created_at: string;
  title?: string;
  warnings?: string;
}

export interface DocumentListResponse {
  items: DocumentMetadata[];
  pagination: PaginationMetadata;
}

export interface DocumentTextPreview {
  document_id: string;
  filename: string;
  status: string;
  char_count: number;
  word_count: number;
  detected_language: string;
  raw_text: string;
  warnings?: string;
}

export interface Passage {
  id: string;
  document_id: string;
  sequence_index: number;
  start_offset: number;
  end_offset: number;
  text_content: string;
  token_count: number;
  page_number: number;
  language: string;
}

export interface DocumentPassagesResponse {
  document_id: string;
  filename: string;
  total_passages: number;
  passages: Passage[];
}

export interface Collection {
  collection_id: string;
  name: string;
  description?: string;
  document_count: number;
  is_public_within_tenant: boolean;
  created_at: string;
}

export interface CollectionListResponse {
  items: Collection[];
  pagination: PaginationMetadata;
}

export interface CollectionDocumentsResponse {
  collection_id: string;
  collection_name: string;
  total_documents: number;
  documents: DocumentMetadata[];
}

export interface ValidateComparisonRequest {
  submission_document_id: string;
  mode: 'direct' | 'one_to_many' | 'corpus';
  reference_document_id?: string;
  reference_document_ids?: string[];
  collection_id?: string;
}

export interface ValidateComparisonResponse {
  status: 'ready' | 'error';
  mode: string;
  submission_document: {
    document_id: string;
    filename: string;
    char_count: number;
    word_count: number;
    detected_language: string;
  };
  reference_count: number;
  references: Array<{
    document_id: string;
    filename: string;
    char_count: number;
    detected_language: string;
  }>;
  message: string;
  phase_boundary_status: string;
}

export type DetectionMode = 'lexical' | 'semantic' | 'hybrid';

export interface ModelInfo {
  model_name: string;
  revision: string;
  embedding_dim: number;
  max_seq_length: number;
  device: string;
  is_gpu: boolean;
  normalization: string;
  query_prefix?: string;
  passage_prefix?: string;
}

export interface CreateAnalysisRequest {
  submission_document_id: string;
  mode: 'direct' | 'one_to_many' | 'corpus';
  detection_mode?: DetectionMode;
  reference_document_id?: string;
  reference_document_ids?: string[];
  collection_id?: string;
  exclude_citations?: boolean;
  exclude_references?: boolean;
}

export interface AnalysisJobStatus {
  job_id: string;
  analysis_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  current_step?: string;
  progress_percent: number;
  error_code?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface SimilarityFinding {
  finding_id: string;
  category: 'exact_copy' | 'near_exact_rewrite' | 'paraphrase' | 'potential_translation';
  confidence: 'high' | 'moderate' | 'low';
  submission_start_offset: number;
  submission_end_offset: number;
  submission_excerpt: string;
  reference_document_id: string;
  reference_source_title: string;
  reference_start_offset: number;
  reference_end_offset: number;
  reference_excerpt: string;
  reference_page_number?: number;
  lexical_similarity?: number;
  semantic_similarity?: number;
  is_quoted?: boolean;
  is_excluded?: boolean;
  language_pair?: string;
  model_name?: string;
  review_decision?: 'unreviewed' | 'keep' | 'exclude' | 'quoted_cited' | 'needs_review';
  reviewer_notes?: string;
  reviewer_updated_at?: string;
}

export interface ReviewFindingResponse {
  finding: SimilarityFinding;
  analysis_id: string;
  original_evidence_coverage_percent: number;
  reviewer_adjusted_coverage_percent: number;
  reviewed_findings_count: number;
  total_findings_count: number;
  status_counts: Record<string, number>;
}

export interface SourceBreakdown {
  reference_document_id: string;
  source_title: string;
  matched_passage_count: number;
  lexical_coverage_percent: number;
  semantic_coverage_percent: number;
}

export interface AnalysisResult {
  analysis_id: string;
  submission_document_id: string;
  submission_filename?: string;
  mode: 'direct' | 'one_to_many' | 'corpus';
  detection_mode?: DetectionMode;
  status: string;
  overall_lexical_coverage_percent: number;
  overall_semantic_coverage_percent: number;
  net_adjusted_score_percent: number;
  hybrid_evidence_coverage_percent?: number;
  reviewer_adjusted_coverage_percent?: number;
  reviewed_findings_count?: number;
  reviewer_notes?: string;
  matched_source_count: number;
  total_findings_count: number;
  findings: SimilarityFinding[];
  sources: SourceBreakdown[];
  model_metadata?: ModelInfo;
  created_at?: string;
  completed_at?: string;
}

export interface AnalysisSummary {
  analysis_id: string;
  submission_document_id: string;
  submission_filename?: string;
  mode: string;
  detection_mode?: string;
  status: string;
  lexical_coverage: number;
  semantic_coverage: number;
  net_score?: number;
  matched_source_count: number;
  total_findings_count: number;
  processing_time_ms?: number;
  created_at: string;
}

export interface PaginatedAnalyses {
  items: AnalysisSummary[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
}

