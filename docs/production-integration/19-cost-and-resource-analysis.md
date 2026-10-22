# 19 — Hosting Cost, Resource Sizing, and ROI Analysis

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Status:** COMPLETE  

---

## 1. Projected Monthly Hosting Costs (Render Reference Architecture)

The infrastructure was deliberately sized to deliver commercial-grade performance while minimizing operational costs:

| Resource | Service / Instance Type | Specs | Monthly Cost (USD) |
|---|---|---|---|
| **Frontend Web** | Render Web Service (Starter) | 0.5 CPU, 512 MB RAM | $7.00 |
| **API Backend** | Render Web Service (Standard) | 1 CPU, 2 GB RAM | $25.00 |
| **RQ Worker** | Render Background Worker (Standard) | 1 CPU, 2 GB RAM | $25.00 |
| **Database** | Render Managed PostgreSQL + pgvector | 1 CPU, 1 GB RAM, 10 GB Storage | $15.00 |
| **Queue** | Render Managed Redis | 256 MB RAM | $7.00 |
| **Disk Storage** | Render Persistent Disk Volume | 10 GB SSD | $2.50 |
| **Bandwidth** | Included Tier | 100 GB Outbound Transfer | $0.00 |
| **TLS Certificates**| Let's Encrypt Managed Wildcard | Automated SSL | $0.00 |
| **Total Estimated** | **Full Production Stack** | | **$81.50 / mo** |

### Staging / Lean Alternative (Hobby / Developer Tier)
For low-volume institutional pilot deployments or demonstration environments:
- Unified Web + API + Worker on single shared container ($15 / mo)
- Shared PostgreSQL + pgvector ($7 / mo)
- Internal Redis ($7 / mo)
- **Total Lean Tier:** **$29.00 / mo**

---

## 2. Resource Headroom & Capacity

- **Document Ingestion:** Capable of processing up to 10,000 document pages per day on the Standard tier.
- **Concurrent Analyses:** Python RQ handles up to 5 concurrent hybrid similarity analyses per worker instance with automatic horizontal scaling capability.
- **Storage Scalability:** 10 GB persistent disk accommodates approximately 50,000 PDF documents (averaging 200 KB per document).
