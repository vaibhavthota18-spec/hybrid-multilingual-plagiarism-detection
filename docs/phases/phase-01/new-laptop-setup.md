# Beginner-Friendly Setup Guide for New Windows 11 Laptop

**System:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** 1 — Engineering Foundation & Infrastructure  
**Author:** Windows Development Environment Engineering Team  
**Date:** October 14, 2026  
**Document Version:** 1.0.0  

---

## 1. Inventory of Installed Tools

Your new Windows 11 laptop has been audited and configured with the following official runtimes:

| Tool | Installed Version | Executable Path | Status |
| :--- | :--- | :--- | :---: |
| **Python** | 3.12.10 (LTS 64-bit) | `C:\Users\vaibh\AppData\Local\Programs\Python\Python312\python.exe` | Verified Active |
| **Python venv** | 3.12.10 with pytest, fastapi | `C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\.venv` | 32/32 Tests Passed |
| **Node.js** | v20.18.0 (LTS) | `C:\Users\vaibh\AppData\Local\Programs\NodeJS\node.exe` | Verified Active |
| **npm** | 10.8.2 | `C:\Users\vaibh\AppData\Local\Programs\NodeJS\npm.cmd` | Verified Active |
| **Git** | 2.47.0.windows.1 | `C:\Users\vaibh\AppData\Local\Programs\Git\cmd\git.exe` | Verified Active |
| **Package Manager**| Windows Package Manager (`winget`) | `C:\Users\vaibh\AppData\Local\Microsoft\WindowsApps\winget.exe` | Verified Active |
| **Docker Desktop** | Not yet installed | Pending BIOS Virtualization | Blocked on BIOS |
| **WSL2** | Not yet installed | Pending BIOS Virtualization | Blocked on BIOS |

---

## 2. One-Time Hardware Action: Enabling Virtualization in BIOS

Before Docker Desktop and WSL2 can run Linux containers (PostgreSQL, Redis, and workers), you must enable CPU virtualization in your motherboard firmware.

### Exact Step-by-Step Instructions:
1. **Save your work and shut down Windows.**
2. Power on your laptop and immediately start tapping the BIOS key repeatedly:
   * **HP laptops:** Tap `Esc`, then press `F10`.
   * **Dell laptops:** Tap `F2` or `F12`.
   * **Lenovo laptops:** Tap `F2` or `Fn + F2`.
   * **ASUS / Acer:** Tap `F2` or `Del`.
3. In the BIOS Setup utility:
   * Look for a menu named **Configuration**, **Advanced**, or **Security**.
   * Locate **Intel Virtualization Technology (VT-x)** (for Intel CPUs) or **SVM Mode / AMD-V** (for AMD CPUs).
   * Change the setting from **Disabled** to **Enabled**.
4. Press **F10** (Save & Exit Setup). Confirm "Yes". Your laptop will restart into Windows 11.

---

## 3. Installing WSL2 and Docker Desktop (Post-BIOS Step)

Once virtualization is enabled in BIOS:

### 3.1 Install WSL2
Open PowerShell as Administrator (Right-click Start button -> "Terminal (Admin)"):
```powershell
wsl --install --no-distribution
```
Restart your computer if prompted by Windows.

### 3.2 Install Docker Desktop
Run the following command in PowerShell:
```powershell
winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
```
Or download the installer directly from [Docker Official Site](https://docs.docker.com/desktop/setup/install/windows-install/).

### 3.3 First Launch of Docker Desktop
1. Open Docker Desktop from the Start Menu.
2. Accept the Docker Personal (Free for Educational Use) terms of service.
3. In Docker Settings -> General, ensure **"Use the WSL 2 based engine"** is checked.
4. Verify the Docker daemon is running by opening a terminal and running:
   ```powershell
   docker info
   ```

---

## 4. Running the Project Locally

### 4.1 Automated Docker Full-Stack Startup (When Docker is active)
From the project root folder:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_local.ps1
```
This automatically starts:
* **Web UI:** http://localhost:3000
* **Backend API:** http://localhost:8000
* **OpenAPI Docs:** http://localhost:8000/docs
* **Health Endpoint:** http://localhost:8000/api/v1/health

### 4.2 Running Frontend on Host (Without Containers)
To run the React frontend directly:
```powershell
cd apps\web
npm run dev
```
Open your browser at: http://localhost:5173

---

## 5. Verification Commands

To verify your installation anytime, run the automated test scripts from the project root:

```powershell
# 1. Verify OpenAPI 3.1 Contract (10 checks)
powershell -ExecutionPolicy Bypass -File scripts\validate_contract.ps1

# 2. Run All 32 Backend Unit Tests (Pytest)
apps\backend\.venv\Scripts\pytest.exe -v apps\backend\tests

# 3. Run All Frontend Tests & Production Build (Vitest + Vite)
powershell -ExecutionPolicy Bypass -File scripts\run_web_tests.ps1
```

---

## 6. Comprehensive Troubleshooting Guide

### 6.1 `node` or `npm` or `git` not recognized
* **Cause:** The current terminal session was opened before the tools were installed.
* **Fix:** Close and reopen your PowerShell terminal, or run:
  ```powershell
  $env:PATH = "C:\Users\vaibh\AppData\Local\Programs\NodeJS;C:\Users\vaibh\AppData\Local\Programs\Git\cmd;$env:PATH"
  ```

### 6.2 Virtualization disabled in firmware
* **Symptom:** `wsl --install` or Docker Desktop displays `Wsl/Service/CreateInstance/CreateVm/HCS/E_INVALIDARG`.
* **Fix:** Enter BIOS/UEFI as described in Section 2 and enable VT-x / AMD SVM Mode.

### 6.3 OneDrive `EPERM` or file lock issues
* **Symptom:** `npm error EPERM: operation not permitted` during package installs.
* **Cause:** OneDrive background synchronization temporarily locking files in `apps\web\node_modules`.
* **Fix:** Right-click the OneDrive cloud icon in the taskbar and select **"Pause syncing (2 hours)"** while installing dependencies, or use Docker containers which use named volumes (`plagiarism_storage_volume`) outside OneDrive.

### 6.4 Port 8000 or 5432 or 3000 already in use
* **Symptom:** `bind: address already in use`.
* **Fix:** Find and terminate the process holding the port:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```
