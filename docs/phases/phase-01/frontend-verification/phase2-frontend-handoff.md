# Phase 2 Frontend Integration and Handoff Specification

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**From Phase:** Phase 1 — Engineering Foundation and Infrastructure  
**To Phase:** Phase 2 — Document Ingestion and Reference Corpus  
**Handoff Scope:** Reusable Components, API Conventions, Styling Patterns, Upload UI Integration, and Security  
**Handoff Date:** 2026-10-14  

---

## 1. Executive Summary

This handoff document details the architectural conventions, reusable React components, styling systems, and integration points established in Phase 1 for frontend development in Phase 2.

In Phase 2, the primary objective is to build the multi-format Document Ingestion pipeline (PDF, DOCX, TXT text extraction, Unicode NFC normalization, passage chunking, and language hint validation). The Phase 1 frontend is structured specifically to integrate this ingestion workflow cleanly into the existing shell.

---

## 2. Reusable Component Inventory

Phase 2 engineers can import and reuse the following established components:

| Component | File Path | Props & Description |
| :--- | :--- | :--- |
| `Header` | `src/components/Header.tsx` | Accepts `health: HealthStatus`, `loading: boolean`, `onRefresh: () => void`. Top branding and live service status. |
| `Navigation` | `src/components/Navigation.tsx` | Accepts `activeTab`, `setActiveTab`, `onOpenFutureFeature`. Renders tab strip with phase status badges. |
| `Footer` | `src/components/Footer.tsx` | Site-wide footer with language badges (EN • HI • TE) and repository boundaries. |
| `StatusIndicator` | `src/components/StatusIndicator.tsx` | Accepts `health: HealthStatus`, `loading: boolean`. 4-card infrastructure health grid. |
| `FutureFeatureModal` | `src/components/FutureFeatureModal.tsx` | Informational modal dialog for explaining upcoming roadmap phases. |

---

## 3. API Client Conventions (`src/lib/api/client.ts`)

Phase 2 document upload and ingestion endpoints must interact with the backend using the established `apiFetch` utility:

### 3.1 Standard Usage Pattern
```typescript
import { apiFetch } from '@/lib/api/client';
import { DocumentUploadResponse } from '@/types/generated/api';

export async function uploadDocument(formData: FormData): Promise<DocumentUploadResponse> {
  return await apiFetch<DocumentUploadResponse>('/api/v1/documents', {
    method: 'POST',
    body: formData,
    // Do NOT set Content-Type header manually for FormData; browser sets multipart boundary automatically
  });
}
```

### 3.2 Automated Behaviors Built into `apiFetch`
- **Request Tracing:** Automatically attaches `X-Request-ID: web-<timestamp>-<random>` if omitted.
- **Authorization:** Automatically attaches `Authorization: Bearer <token>` if `auth_token` exists in `localStorage`.
- **Content Negotiation:** Automatically defaults `Accept: application/json`.
- **RFC 7807 Error Handling:** Non-2xx responses are parsed into structured `ApiClientError` instances containing:
  - `status`: HTTP status code (e.g. `400`, `413`, `422`).
  - `code`: Machine-readable error code (e.g. `UNSUPPORTED_FILE_TYPE`, `FILE_TOO_LARGE`).
  - `message`: Human-readable error description.
  - `requestId`: Correlation ID from the backend for debugging.
  - `details`: Array of field validation error items.

---

## 4. Document-Upload UI Integration Points in Phase 2

### 4.1 Activating the Document Ingestion Tab
In `src/components/Navigation.tsx`, change the `ingestion` tab configuration:

```typescript
// Update in src/components/Navigation.tsx:
{
  id: 'ingestion',
  label: 'Document Ingestion',
  icon: UploadCloud,
  phase: 'Phase 2',
  isLive: true, // <-- Flip from false to true in Phase 2
  description: 'Multi-format ingestion pipeline for PDF, DOCX, and TXT files...',
}
```

### 4.2 Adding `IngestionPage.tsx`
Create `src/pages/IngestionPage.tsx` and mount it conditionally inside `src/App.tsx`:

```tsx
// Inside src/App.tsx:
{activeTab === 'infrastructure' && <HomePage ... />}
{activeTab === 'ingestion' && <IngestionPage ... />}
```

### 4.3 Proposed Ingestion UI Features for Phase 2:
1. **Drag-and-Drop Dropzone:**
   - Supported extensions: `.pdf`, `.docx`, `.txt`.
   - Client-side size guard: Maximum 50 MB (matching Phase 0 specification).
2. **Language Hint Selector:**
   - Radios or dropdown: `Auto-Detect (Recommended)`, `English (EN)`, `Hindi (HI)`, `Telugu (TE)`.
3. **Ingestion Progress Bar / State Card:**
   - States: `Uploading` → `Extracting Text` → `Normalizing Unicode (NFC)` → `Passage Chunking` → `Indexed`.
4. **Extracted Metadata & Chunks Preview:**
   - Title, word count, character count, detected language, and chunk count.
   - Clean scrollable preview of extracted text passages without any synthetic plagiarism scores.

---

## 5. Established Styling Patterns

- **Card Containers:**
  `bg-slate-900/60 border border-slate-800 rounded-xl p-5`
- **Interactive Buttons (Primary):**
  `px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm rounded-lg transition`
- **Interactive Buttons (Secondary):**
  `px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm rounded-lg transition`
- **Badges:**
  - Success/Live: `bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full`
  - Warning/Degraded: `bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs px-2.5 py-0.5 rounded-full`
  - Error/Offline: `bg-rose-500/10 text-rose-400 border border-rose-500/30 text-xs px-2.5 py-0.5 rounded-full`
  - Informational/Upcoming: `bg-slate-800 text-slate-400 border border-slate-700 text-xs px-2 py-0.5 rounded`

---

## 6. Security and Phase Boundary Enforcement

1. **Strict Boundary Enforcement:**
   Phase 2 is limited to document ingestion and parsing. Do NOT implement Winnowing fingerprints, BM25 indexing, Multilingual E5 vectors, or similarity scoring in Phase 2; those belong to Phase 3 and Phase 4.
2. **Input Sanitization & Safe Display:**
   Extracted text must be rendered using standard React JSX text nodes to ensure automatic escaping against Cross-Site Scripting (XSS). Avoid `dangerouslySetInnerHTML`.
3. **MIME Type Validation:**
   Perform client-side validation on file extensions and MIME types (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`) prior to dispatching upload requests.
4. **Request Correlation:**
   Every document upload request must preserve the generated `X-Request-ID` to allow tracing through the FastAPI backend and Redis RQ worker.

---

## 7. Conclusion

The Phase 1 frontend provides a modular, type-safe foundation. Phase 2 engineers can seamlessly enable the `Document Ingestion` tab and plug in the upload dropzone and metadata preview components using the conventions defined herein.
