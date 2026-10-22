# Phase 6 — UI Redesign and Minimalist Design System

## 1. Executive Overview
Phase 6 transforms the Multilingual Plagiarism Detection platform into a professional, commercial-grade SaaS web product inspired by the user-centric simplicity and intuitive flow of **iLovePDF**. 

The goal was to replace developer-centric metrics displays, raw database monitors, and cluttered card grids with a distraction-free, light-themed interface where any student, educator, or researcher can upload documents and inspect similarity findings within seconds.

## 2. Core Visual Identity and Tokens
- **Background Palette:** Clean Slate-50 (`#F8FAFC`) canvas with pure White (`#FFFFFF`) cards and Slate-100/200 (`#F1F5F9` / `#E2E8F0`) borders.
- **Brand Colors:**
  - Primary Accent: Indigo-600 (`#4F46E5`), Indigo-700 (`#4338CA`) for primary actions.
  - Success / Safe: Emerald-600 (`#059669`) / Emerald-50 (`#ECFDF5`).
  - Warning / Moderate: Amber-500 (`#F59E0B`) / Amber-50 (`#FFFBEB`).
  - Danger / High Plagiarism: Rose-600 (`#E11D48`) / Rose-50 (`#FFF1F2`).
- **Typography:** System font stack (`Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`) optimized for legibility across English, Hindi (Devanagari), and Telugu scripts.
- **Zero Unnecessary Flourishes:** No glowing neon gradients, 3D card tilts, floating chatbots, or unprompted modal overlays.

## 3. Structural Reorganization & Information Architecture
- **Primary Viewports:**
  1. **New Analysis (Central Hero Flow):** Single-page, 5-stage progressive disclosure workflow (`WorkflowPage.tsx`).
  2. **Results & Review Dashboard:** Clean dual-pane side-by-side evidence viewer with inline reviewer controls (`ResultsDashboardPage.tsx`).
  3. **Analysis History:** Searchable, chronological log of prior audits (`AnalysisHistoryPage.tsx`).
  4. **Document Library:** Private repository of uploaded documents and collections (`IngestionPage.tsx`).
- **Secondary Developer Console (Relocation of Raw Diagnostics):**
  - Database pool status (PostgreSQL/SQLite), Redis queues, raw vector embedding dimensions (384d), and internal JSON dumps are cleanly separated into a secondary "Infrastructure & Health" view, keeping the primary user flow completely uncluttered.
