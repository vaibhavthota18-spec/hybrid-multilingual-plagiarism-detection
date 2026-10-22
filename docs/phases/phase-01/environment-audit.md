# Phase 1: Pre-Installation Windows Environment Audit

**System:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** 1 — Engineering Foundation & Infrastructure  
**Host Machine:** New Windows 11 Laptop  
**Date of Audit:** October 14, 2026  
**Document Version:** 1.0.0  

---

## 1. Operating System and Hardware Architecture

A comprehensive, read-only system audit was performed via Windows Management Instrumentation (CIM/WMI) and PowerShell:

| Parameter | Detected Value | Assessment / Compatibility |
| :--- | :--- | :--- |
| **Operating System** | Microsoft Windows 11 Home Single Language | Supported by Docker Desktop (with WSL2 backend). |
| **OS Version / Build** | Version 10.0.26200, Build 26200 (64-bit) | Modern Windows 11 build supporting WSL2 and Compose. |
| **CPU Architecture** | x86_64 / AMD64 (1 physical CPU, 16 logical cores) | High compute capacity for parallel processing. |
| **Physical Memory (RAM)** | 16,873,545,728 bytes (~16 GB) | Exceeds minimum 8 GB requirement for full stack. |
| **Storage (Drive C:)** | Used: ~181 GB \| **Free: ~328 GB** | Ample disk capacity for containers and tools. |
| **User Elevation** | Non-Elevated (`IsAdmin: False`) | Standard user privileges; UAC required for drivers. |

---

## 2. Hardware Virtualization & WSL2 Subsystem Status

### 2.1 Critical Hardware Virtualization Finding
* **Firmware Virtualization Check (`Win32_Processor`):**
  ```powershell
  VirtualizationFirmwareEnabled : False
  ```
* **Impact Analysis:** Hardware-assisted virtualization (Intel VT-x or AMD-V / SVM) is currently **DISABLED** in the computer's UEFI/BIOS settings.
* **Requirements:**
  1. WSL2 Linux kernel virtualization cannot initialize until hardware virtualization is enabled in the BIOS/UEFI.
  2. Docker Desktop's Linux container engine relies on WSL2 and will fail to boot without firmware virtualization.
* **Resolution Action:** The user must enter UEFI/BIOS during boot (typically pressing F2, F10, F12, or Del) and enable "Intel Virtualization Technology" or "AMD SVM / SVM Mode".

### 2.2 Windows Subsystem for Linux (WSL) Status
* **Query Result:**
  ```
  The Windows Subsystem for Linux is not installed. 
  You can install by running 'wsl.exe --install'.
  ```
* **Assessment:** WSL2 is missing and requires installation after hardware virtualization is enabled.

---

## 3. Package Management & Tooling Inventory

| Tool / Subsystem | Installed | Detected Version | Executable Location | Required Action | Status |
| :--- | :---: | :---: | :--- | :--- | :---: |
| **Windows Package Manager** | **YES** | Built-in | `C:\Users\vaibh\AppData\Local\Microsoft\WindowsApps\winget.exe` | Use for official unattended installations. | Verified Active |
| **Python** | **YES** *(Alpha)* | 3.15.0 alpha | `C:\Users\vaibh\AppData\Local\Programs\Python\Python315\python.exe` | Install stable Python 3.12 LTS for backend dependencies. | In Progress |
| **Python Launcher** | **YES** | Built-in `py` | `C:\Users\vaibh\AppData\Local\Programs\Python\Launcher\py.exe` | Selects target Python version via `py -3.12`. | Verified Active |
| **Node.js** | **NO** | None in PATH | None detected | Install Node.js 20 LTS via `winget`. | Missing |
| **npm** | **NO** | None in PATH | None detected | Installed automatically with Node.js. | Missing |
| **Git** | **NO** | None in PATH | None detected | Install Git for Windows via `winget`. | Missing |
| **Docker CLI / Desktop** | **NO** | None in PATH | None detected | Install Docker Desktop after BIOS virtualization is enabled. | Blocked on BIOS |
| **WSL2** | **NO** | Not installed | `wsl.exe` present, distro absent | Install via `wsl --install --no-distribution` after BIOS virtualization. | Blocked on BIOS |

---

## 4. Host Network Connectivity Verification

Outbound network connectivity from the Windows host was tested against official package registries using native HTTP web requests:
* **https://nodejs.org:** Connected (HTTP 200 OK)
* **https://pypi.org:** Connected (HTTP 200 OK)
* **https://registry.npmjs.org:** Connected (HTTP 200 OK)
* **https://github.com:** Connected (HTTP 200 OK)

**Conclusion:** The Windows host has unhindered, full outbound internet connectivity to all official package repositories. Previous pip failures were caused by the Antigravity sandbox network isolation, not Windows network connectivity.
