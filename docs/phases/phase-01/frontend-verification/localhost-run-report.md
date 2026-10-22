# Phase 1 Localhost Startup and Execution Report

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** Phase 1 — Engineering Foundation and Infrastructure  
**Component:** Localhost Frontend Dev Server (`apps/web`)  
**Execution Date:** 2026-10-14  
**Operating System:** Windows 11  
**Execution Status:** SUCCESSFUL  

---

## 1. Runtime Environment Verification

Prior to launching the server, the local user runtime environment was inspected and verified:

| Runtime / Tool | Verified Version | Installation Path |
| :--- | :--- | :--- |
| **Node.js** | `v20.18.0` LTS | `C:\Users\vaibh\AppData\Local\Programs\NodeJS\node.exe` |
| **npm** | `10.8.2` | `C:\Users\vaibh\AppData\Local\Programs\NodeJS\npm.cmd` |
| **Git** | `2.47.0.windows.1` | `C:\Users\vaibh\AppData\Local\Programs\Git\cmd\git.exe` |
| **Python** | `3.12.10` LTS | `C:\Users\vaibh\AppData\Local\Programs\Python\Python312\python.exe` |

---

## 2. Server Startup Command and Parameters

The Vite development server was started using the following command inside `apps/web`:

```powershell
$env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;" + $env:PATH
npm run dev -- --host 127.0.0.1 --port 5173
```

- **Working Directory:** `C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\web`
- **Host Binding:** `127.0.0.1` (IPv4 localhost)
- **Port:** `5173`
- **Proxy Configuration:** `/api` forwarded to `http://localhost:8000` via `vite.config.ts`

---

## 3. Server Startup Log Output

```text
> plagiarism-web@1.0.0 dev
> vite --host 127.0.0.1 --port 5173

  VITE v5.4.21  ready in 1987 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 4. Localhost URLs and Network Availability

The server successfully bound to the following local addresses:

- **Direct IPv4 Address:** `http://127.0.0.1:5173/`
- **Localhost Alias:** `http://localhost:5173/`

Both addresses resolve immediately and serve the frontend web client.

---

## 5. HTTP Response Verification and Module Transpilation

Direct HTTP probing was executed against the running dev server to confirm proper document delivery and on-demand Vite module transpilation:

### 5.1 Root Document Probe (`/`)
- **HTTP Status:** `200 OK`
- **Content Type:** `text/html; charset=utf-8`
- **DOM Container:** `<div id="root"></div>` verified present.
- **Vite Client Hooks:** `/@vite/client` and `/@react-refresh` scripts injected cleanly.

### 5.2 TypeScript Entry Point Probe (`/src/main.tsx`)
- **HTTP Status:** `200 OK`
- **Transpilation:** Vite successfully transformed React TSX into native ES module code on demand.

### 5.3 Root Component Probe (`/src/App.tsx`)
- **HTTP Status:** `200 OK`
- **Transpilation:** Clean compilation without JSX or TypeScript transpilation errors.

---

## 6. Backend Integration and Decoupling Probe

The frontend was tested under two operational scenarios to verify backend independence and live proxy forwarding:

### Scenario A: Backend Offline (Decoupled Mode)
When the FastAPI backend is not running on port 8000:
- The frontend loads completely without hanging or crashing.
- `fetchHealthStatus()` catches network connection refused errors in `App.tsx`.
- The UI gracefully sets status to `Backend Degraded` with disconnected indicators.
- All tabs, modal dialogs, and roadmap information remain fully interactive.

### Scenario B: Backend Online (Integrated Local Mode)
With the FastAPI backend started on `http://127.0.0.1:8000`:
- Vite dev server forwarded `/api/v1/health` requests seamlessly to `http://localhost:8000/api/v1/health`.
- Probe response:
  ```json
  {
    "status": "degraded",
    "timestamp": "2026-10-14T11:47:12.241118+00:00",
    "database": "disconnected",
    "redis": "disconnected",
    "worker_pool": "degraded",
    "version": "1.0.0"
  }
  ```
- HTTP Status: `200 OK`
- The frontend dynamically consumed the live JSON payload and rendered the appropriate service states.

---

## 7. Failures and Errors

- **Fatal Runtime Errors:** 0
- **Unhandled Exceptions:** 0
- **Port Conflicts:** 0 (port 5173 bound immediately)
- **Compilation Failures:** 0

---

## 8. Conclusion

The Vite development server is fully operational on `http://127.0.0.1:5173/`. It is completely decoupled from backend container dependencies while supporting live proxying whenever local backend services are active.
