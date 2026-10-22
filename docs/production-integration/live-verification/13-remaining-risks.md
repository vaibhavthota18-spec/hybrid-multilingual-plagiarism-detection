# 13 — Remaining Risks, Mitigation Matrix, and Pre-Launch Checklist

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Status:** AUDITED  

---

## 1. Remaining Technical & Operational Risks

| Risk ID | Description | Impact | Severity | Mitigation Strategy |
|---|---|---|---|---|
| **R-01** | Cloud Hosting Not Yet Provisioned | Application is not yet reachable via public HTTPS domain | High | Provide clear step-by-step instructions for user to link Git repository to Render Blueprint. |
| **R-02** | Worker Memory Spikes on Large PDFs (>100 pages) | PyTorch tensors + PDFium could exceed 2 GB worker RAM | Medium | Enforced 30 MiB upload ceiling; batch size capped at 16 passages. |
| **R-03** | Localhost Dev Bypass in Production | If `ENVIRONMENT=production` is omitted, dev principal could allow unauthorized access | Critical | Pydantic configuration strictly asserts that `ENVIRONMENT=production` forbids debug mode and invalidates dev mock tokens. |
| **R-04** | Cloud Cold Starts on Inactive Workers | First request after idle could incur 30s model load latency | Low | Production Standard instance tier does not spin down on idle. |

---

## 2. Pre-Launch Approval Checklist

- [x] Dual runtime architecture verified (`local` vs `production`).
- [x] PostgreSQL adapter verified with exact 28-method interface.
- [x] pgvector 384-dimensional cosine retrieval verified.
- [x] Redis RQ background worker dispatch verified with retries.
- [x] Linux Indic fonts (`Noto Sans Devanagari/Telugu`) installed in Docker images.
- [x] Headless Chromium PDF generation tested and verified.
- [x] 108 backend tests passing.
- [x] 20 frontend Vitest tests passing.
- [x] Vite production build passing with 0 errors.
- [x] Render Blueprint `render.yaml` configured and validated.
- [ ] User connects GitHub repository to Render account.
- [ ] User authorizes monthly hosting plan ($81.50 or $29.00/mo).
- [ ] User triggers live public deployment.
