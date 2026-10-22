# 11 — Hosting Provider Evaluation & Reference Architecture Selection

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Status:** COMPLETE  

---

## 1. Hosting Provider Comparison

Four primary deployment platforms were evaluated against the project's technical requirements:
1. Docker container support with custom Debian packages (Chromium, Indic Noto fonts).
2. Managed PostgreSQL 16 with native `pgvector` extension.
3. Managed Redis 7 for Python RQ worker queues.
4. Shared persistent disk volume accessible across API and background worker services.
5. Predictable pricing without sudden billing spikes.

| Criteria | **Render (Selected)** | **Railway** | **Fly.io** | **AWS (ECS + RDS)** |
|---|---|---|---|---|
| **Blueprint IaC** | `render.yaml` native | `railway.json` | `fly.toml` | Terraform / CloudFormation |
| **PostgreSQL + pgvector**| Native 1-click support | Supported | Supported | Supported via Aurora / RDS |
| **Managed Redis** | Native internal Redis | Supported | Third-party (Upstash) | ElastiCache |
| **Shared Persistent Disk**| Yes (persistent disk attached to service) | Volume per service | Volume per VM | EFS required (complex) |
| **Ease of Setup** | Extremely simple | Simple | Moderate | Complex |
| **Monthly Cost (Est.)** | ~$25 - $35 / mo | ~$20 - $40 / mo | ~$25 - $45 / mo | ~$70 - $120 / mo |

---

## 2. Selected Architecture: Render Blueprint

**Render** was selected as the reference production deployment target because:
1. **Unified Infrastructure-as-Code:** Entire stack (Web, API, Worker, Database, Redis, Volumes) is declaratively provisioned from a single `render.yaml` file.
2. **Automated SSL/TLS:** Free automatic Let's Encrypt wildcard certificates with HTTP to HTTPS auto-redirects.
3. **Internal Networking:** Services (`plagiarism-api`, `plagiarism-worker`, `plagiarism-postgres`, `plagiarism-redis`) communicate over Render's private virtual network, exposing only the Nginx web frontend and API proxy to the public internet.
