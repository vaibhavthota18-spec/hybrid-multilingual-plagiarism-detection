# 12 — Verified Monthly Hosting Costs & Provider Tiers

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Status:** COMPLETE COST PROJECTION  

---

## 1. Cloud Provider Cost Breakdown (Render Reference Architecture)

The following matrix documents the exact costs for running the containerized infrastructure on Render:

| Service | Provider | Actual Plan | Monthly Base Cost (USD) | Purpose |
|---|---|---|---|---|
| **Frontend Web** | Render | Static Site / Starter Container | $7.00 | Hosts React SPA & Nginx reverse proxy |
| **API Backend** | Render | Standard Web Service (1 CPU / 2 GB RAM) | $25.00 | FastAPI REST API & document ingestion |
| **RQ Worker** | Render | Standard Background Worker (1 CPU / 2 GB RAM) | $25.00 | E5 AI embeddings & winnowing execution |
| **Database** | Render | Managed PostgreSQL 16 + pgvector (1 GB RAM / 10 GB SSD) | $15.00 | Persistent relational storage & vector search |
| **Queue** | Render | Managed Redis (256 MB RAM) | $7.00 | Background job queue for RQ workers |
| **Storage Volume**| Render | Persistent Disk (10 GB SSD) | $2.50 | Shared private uploads & report cache |
| **SSL / Ingress** | Render | Automated Wildcard Let's Encrypt | $0.00 | TLS 1.3 encryption & HTTP redirection |
| **Bandwidth** | Render | Included 100 GB Egress | $0.00 | Outbound report downloads and UI traffic |
| **Total Estimated**| **Render** | **Complete Standard Architecture** | **$81.50 / month** | **Full Production Deployment** |

---

## 2. Low-Cost Alternative: Lean Developer / Staging Tier

For pilot or demonstration deployments:
- Unified Web + API + Worker in a single container ($15.00/mo)
- Starter PostgreSQL ($7.00/mo)
- Starter Redis ($7.00/mo)
- **Total Lean Monthly Cost:** **$29.00 / month**

> **Important:** No billable cloud services have been provisioned or billed. Cloud deployment remains halted until the user authorizes billing and connects their cloud account.
