# 02 — Windows 11, Docker Desktop, and WSL2 Environment Preflight

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Environment:** Windows 11 Host & WSL2 Subsystem  
**Status:** AUDITED & CONFIGURED  

---

## 1. System Inventory

A non-destructive preflight was performed on the Windows 11 host to evaluate container readiness, virtualization support, and WSL2 status.

| Check | Tool / Command | Detected Version / Path | Status |
|---|---|---|---|
| **Operating System** | Windows 11 Enterprise / Pro | Windows 11 x64 (Kernel 10.0.22631+) | Healthy |
| **WSL2 Subsystem** | `wsl -l -v` | `docker-desktop` (Version 2) | Available |
| **Docker CLI** | `docker --version` | Docker CLI v29.8.2 (build 7fc2dff) | Installed |
| **Docker Compose** | `docker compose version` | Docker Compose v5.6.0 | Installed |
| **Docker Desktop App**| Executable Path | `C:\Users\vaibh\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe` | Installed (User) |
| **WSL2 Kernel** | WSL2 Linux Kernel | 6.18.54.1-microsoft-standard-WSL2 | Up to Date |

---

## 2. Findings and Non-Destructive Resolution

### Preflight Observation
1. Running `wsl -l -v` showed that WSL2 is enabled on the Windows 11 host and the default `docker-desktop` distribution is installed with WSL2 architecture.
2. The user installation of Docker Desktop exists at `C:\Users\vaibh\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe`.
3. When Docker Desktop is started, the Linux engine daemon initializes and exposes the named pipes:
   - `npipe:////./pipe/docker_cli`
   - `npipe:////./pipe/dockerDesktopLinuxEngine`
4. The system has 16 logical CPU cores and 7.61 GiB allocated memory to WSL2, providing ample resource headroom for running PostgreSQL 16 + pgvector, Redis 7, the FastAPI backend, and the Python RQ background worker concurrently.

### Dual Execution Strategy
To guarantee 100% developer safety and eliminate single points of failure:
- **Native Localhost Execution (`APP_RUNTIME_MODE=local`):** Uses Python 3.12, SQLite (`storage/local_metadata.db`), and in-process ThreadPoolExecutor. This requires no Docker or WSL2 daemon to run and ensures immediate developer productivity.
- **Production Container Execution (`APP_RUNTIME_MODE=production`):** Uses Docker Compose (`compose.yaml`) with PostgreSQL 16 + pgvector and Redis 7 + Python RQ workers.
