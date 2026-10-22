# ADR-0006: Tenant-Isolated Storage & Hard Deletion (Right to Erasure)

- **Status:** Accepted
- **Deciders:** Principal Software Architect, Application Security Engineer, Privacy & Data Governance Engineer
- **Date:** October 2026
- **Technical Story:** Data lifecycle, user privacy, and hard deletion mechanics

---

## Context
Commercial plagiarism platforms face severe legal and ethical pushback for unilaterally retaining submitted student essays in private corporate databases without consent. Academic privacy regulations (GDPR, FERPA, Indian DPDP Act) mandate that users retain full ownership of their intellectual property, including the right to complete erasure.

## Decision
1. **Private by Default:** Uploaded documents are private to the submitting user account. They are NEVER automatically indexed into institutional or public corpora without explicit, affirmative consent.
2. **Reliable Multi-Tier Deletion Lifecycle (Right to Erasure):** Document deletion spans multiple storage tiers (relational database, physical filesystem, Redis cache, and backup archives). Because cross-system operations cannot be executed in a single atomic transaction, the platform implements a reliable, fenced, and verifiable workflow upon `DELETE /api/v1/documents/{id}`:
   - **Access Invalidation & Fencing:** Authorization is verified; document status is marked `status = 'DELETING'` in DB; active processing tasks are invalidated via Redis fencing tokens (`fence:doc:{id}`).
   - **Durable Deletion Ledger:** An independent, append-only deletion tombstone is recorded outside standard relational snapshot trees to survive and govern restore events.
   - **Operational Purge (ACID DB & Idempotent FS):**
     - Cascading foreign keys delete rows across `findings`, `embeddings` (in `pgvector`), `fingerprints`, `passages`, `collection_documents`, `document_sources`, and `documents`.
     - Storage service idempotently unlinks raw uploads (`storage/uploads/{id}.*`), extracted text, and generated PDF reports.
     - Redis job keys and candidate caches are evicted. Background retry workers guarantee cleanup completion if transient file locks occur.
   - **Disaster Recovery Anti-Resurrection & Retention Limits:**
     - Encrypted daily database snapshots and WAL archives retain disaster recovery states for up to 30 days.
     - In the event of a disaster recovery restoration from a historical snapshot, a mandatory startup hook reconciles the database against the independent Durable Deletion Ledger to re-purge any resurrected records before serving traffic.
     - Physical filesystem blocks remain unallocated on underlying media until overwritten by subsequent writes per standard operating system storage dynamics.
3. **Storage Boundary:** Document uploads are stored outside the public web server document root in dedicated tenant-prefixed directories using random UUIDs rather than original filenames. In containerized environments, persistence uses Docker named volumes insulated from host cloud sync.

## Alternatives Considered
1. **Soft Deletion (`is_deleted = true`):** Rejected for document payloads. Soft-deleted documents still leave private student manuscripts on disk, creating privacy and legal compliance liabilities.
2. **Retaining Hashes / Vectors After Raw Text Deletion:** Rejected. Embeddings and fingerprint hashes can be subjected to model inversion or reconstruction attacks, leaking sensitive text content.

## Rationale
Full compliance with academic privacy principles and privacy laws. Users can trust the platform to check draft manuscripts without fear of unauthorized retention.

## Consequences & Trade-offs
- **Positive:** Complete privacy compliance, zero residual data leakage risk, clean disk hygiene.
- **Negative:** Deletion is permanent and irreversible. Once deleted, historical analysis reports cannot be regenerated without re-uploading the original file.

## Validation Requirements
Automated integration test executing document deletion and asserting:
1. Zero rows remain across `documents`, `passages`, `fingerprints`, `embeddings`, and `findings`.
2. `os.path.exists(file_path)` returns `False`.
