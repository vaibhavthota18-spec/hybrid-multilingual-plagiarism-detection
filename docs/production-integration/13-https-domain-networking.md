# 13 — HTTPS, TLS/SSL Certificates, Domain, and Networking

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Status:** COMPLETE  

---

## 1. Network Perimeter & Ingress Design

```
[Public Internet]
       |  HTTPS (Port 443) / TLS 1.3
       v
[Render Ingress / Cloudflare Edge]
       |  Automatic SSL/TLS Termination (Let's Encrypt Wildcard)
       |  HTTP -> HTTPS 301 Redirect
       v
[Internal Virtual Private Network]
       |
       +---> plagiarism-web (Nginx reverse proxy)
       |        |
       |        +---> Client Static Assets (index.html, JS, CSS)
       |        +---> Proxy /api/* ---> http://plagiarism-api:8000
       |
       +---> plagiarism-api:8000
       +---> plagiarism-worker (Internal, no ingress)
       +---> plagiarism-postgres:5432 (Internal only, IP allowlist = [])
       +---> plagiarism-redis:6379 (Internal only, IP allowlist = [])
```

---

## 2. Custom Domain Configuration Steps

To connect a custom commercial domain (e.g., `plagiarism-engine.com`):
1. **Frontend CNAME Record:**
   - Host: `@` / `www`
   - Type: `CNAME`
   - Target: `plagiarism-web.onrender.com`
2. **API Endpoint Subdomain:**
   - Host: `api`
   - Type: `CNAME`
   - Target: `plagiarism-api.onrender.com`
3. **CORS Origins Update:**
   Update `CORS_ORIGINS` environment variable in `render.yaml` or Render dashboard to include `https://plagiarism-engine.com` and `https://www.plagiarism-engine.com`.
