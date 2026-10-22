# 02 — Hosted URLs, Target Services, and Provisioning Blueprint

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Status:** BLUEPRINT READY — AWAITING CLOUD ACCOUNT AUTHORIZATION  

---

## 1. Deployed Service Registry & URL Status

| Service Name | Intended Role | Declared Address / Domain | Live Internet Status |
|---|---|---|---|
| **`plagiarism-web`** | React 18 SPA via Nginx | `https://plagiarism-web.onrender.com` | **NOT YET CREATED** |
| **`plagiarism-api`** | FastAPI REST Application | `https://plagiarism-api.onrender.com` | **NOT YET CREATED** |
| **`plagiarism-worker`**| Python RQ Background Worker | Internal (Private Network) | **NOT YET CREATED** |
| **`plagiarism-postgres`**| Managed PostgreSQL 16 + pgvector| Internal (`plagiarism-postgres:5432`) | **NOT YET CREATED** |
| **`plagiarism-redis`** | Managed Redis 7 Key-Value Queue | Internal (`plagiarism-redis:6379`) | **NOT YET CREATED** |
| **`plagiarism-storage`**| Persistent Shared Disk Volume | Mount `/app/storage` (10 GB) | **NOT YET CREATED** |

---

## 2. Requirements to Transition from Blueprint to Live URL

To bring the application live to an actual public HTTPS address, the following three prerequisites are required from the user:

1. **Initialize Git Repository and Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "feat: complete production infrastructure and plagiarism detection platform"
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. **Authorize Render Account & Blueprint:**
   - Link the GitHub repository in the Render Dashboard ([dashboard.render.com](https://dashboard.render.com)).
   - Select **New + -> Blueprint** and point to `render.yaml`.
3. **Approve Recurring Plan Costs:**
   - Standard Tier (~$81.50/mo) or Lean Tier (~$29.00/mo) as documented in `12-verified-monthly-hosting-cost.md`.
