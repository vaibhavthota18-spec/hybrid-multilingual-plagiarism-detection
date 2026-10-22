/**
 * Document, Reference Collection, and Comparison Preparation API Client
 * Conforms strictly to Phase 2 contracts
 */

import { apiFetch } from './client';
import {
  DocumentMetadata,
  DocumentListResponse,
  DocumentTextPreview,
  DocumentPassagesResponse,
  Collection,
  CollectionListResponse,
  CollectionDocumentsResponse,
  ValidateComparisonRequest,
  ValidateComparisonResponse,
} from '../../types/generated/api';

/**
 * Uploads a document (PDF, DOCX, TXT) via multipart/form-data.
 */
export async function uploadDocument(
  file: File,
  title?: string,
  languageHint: string = 'auto'
): Promise<DocumentMetadata> {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  formData.append('language_hint', languageHint);

  return await apiFetch<DocumentMetadata>('/api/v1/documents', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Retrieves paginated list of uploaded documents.
 */
export async function listDocuments(limit = 50, offset = 0): Promise<DocumentListResponse> {
  return await apiFetch<DocumentListResponse>(`/api/v1/documents?limit=${limit}&offset=${offset}`);
}

/**
 * Retrieves single document metadata and processing status.
 */
export async function getDocument(documentId: string): Promise<DocumentMetadata> {
  return await apiFetch<DocumentMetadata>(`/api/v1/documents/${documentId}`);
}

/**
 * Retrieves raw extracted document text for preview.
 */
export async function getDocumentTextPreview(documentId: string): Promise<DocumentTextPreview> {
  return await apiFetch<DocumentTextPreview>(`/api/v1/documents/${documentId}/text`);
}

/**
 * Retrieves segmented document passages with code-point offsets.
 */
export async function getDocumentPassages(documentId: string): Promise<DocumentPassagesResponse> {
  return await apiFetch<DocumentPassagesResponse>(`/api/v1/documents/${documentId}/passages`);
}

/**
 * Permanently deletes a document from storage and database.
 */
export async function deleteDocument(documentId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/documents/${documentId}`, {
    method: 'DELETE',
  });
}

/**
 * Creates a new private reference collection.
 */
export async function createCollection(
  name: string,
  description?: string,
  isPublic = false
): Promise<Collection> {
  return await apiFetch<Collection>('/api/v1/collections', {
    method: 'POST',
    body: JSON.stringify({
      name,
      description,
      is_public_within_tenant: isPublic,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

/**
 * Retrieves list of authorized reference collections.
 */
export async function listCollections(limit = 50, offset = 0): Promise<CollectionListResponse> {
  return await apiFetch<CollectionListResponse>(`/api/v1/collections?limit=${limit}&offset=${offset}`);
}

/**
 * Retrieves collection details.
 */
export async function getCollection(collectionId: string): Promise<Collection> {
  return await apiFetch<Collection>(`/api/v1/collections/${collectionId}`);
}

/**
 * Lists all documents linked within a reference collection.
 */
export async function listCollectionDocuments(
  collectionId: string
): Promise<CollectionDocumentsResponse> {
  return await apiFetch<CollectionDocumentsResponse>(`/api/v1/collections/${collectionId}/documents`);
}

/**
 * Adds an existing processed document into a reference collection.
 */
export async function addDocumentToCollection(
  collectionId: string,
  documentId: string
): Promise<void> {
  await apiFetch<void>(`/api/v1/collections/${collectionId}/documents`, {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId }),
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

/**
 * Removes a document link from a reference collection.
 */
export async function removeDocumentFromCollection(
  collectionId: string,
  documentId: string
): Promise<void> {
  await apiFetch<void>(`/api/v1/collections/${collectionId}/documents/${documentId}`, {
    method: 'DELETE',
  });
}

/**
 * Validates candidate comparison inputs across Direct, One-to-Many, and Corpus modes.
 */
export async function validateComparison(
  request: ValidateComparisonRequest
): Promise<ValidateComparisonResponse> {
  return await apiFetch<ValidateComparisonResponse>('/api/v1/comparisons/validate', {
    method: 'POST',
    body: JSON.stringify(request),
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

export async function pollDocumentUntilComplete(
  documentId: string,
  intervalMs = 500,
  maxAttempts = 30
): Promise<DocumentMetadata> {
  let attempts = 0;
  while (attempts < maxAttempts) {
    const doc = await getDocument(documentId);
    if (doc.status === 'completed') {
      return doc;
    }
    if (doc.status === 'failed') {
      throw new Error(doc.warnings || 'Document processing failed');
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    attempts++;
  }
  return await getDocument(documentId);
}

export const documentsApi = {
  uploadDocument,
  listDocuments,
  getDocument,
  getDocumentText: getDocumentTextPreview,
  getDocumentTextPreview,
  deleteDocument,
  createCollection,
  listCollections,
  listCollectionDocuments,
  addDocumentToCollection,
  removeDocumentFromCollection,
  validateComparison,
  pollDocumentUntilComplete,
};

