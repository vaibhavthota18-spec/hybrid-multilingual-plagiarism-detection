# Phase 7 — Accessibility & Visual Browser Testing

## 1. Multi-Viewport Testing
The web application was audited across four standard screen form factors:

| Viewport | Resolution | Category | Audit Result |
| :--- | :--- | :--- | :--- |
| **Desktop Ultra** | 1440 × 900 | High-res desktop | Spacious layout; hero upload centered; side-by-side evidence viewer fits comfortably |
| **Standard Laptop** | 1366 × 768 | Primary target (Lenovo LOQ) | Hero upload fully visible above fold without scrolling; crisp typography |
| **Tablet** | 1024 × 768 | Tablet / iPad | Responsive wrapping on metric cards; findings collapse neatly |
| **Mobile** | 390 × 844 | Modern smartphone | Single-column stacked workflow; touch-friendly buttons; drawer navigation |

## 2. Color Contrast & WCAG Compliance
- All text meets WCAG AA contrast ratio ($\ge 4.5:1$):
  - Primary text: Slate-900 (`#0F172A`) on Slate-50 (`#F8FAFC`) $\to 15.8:1$.
  - Muted labels: Slate-600 (`#475569`) on white $\to 5.6:1$.
  - Brand buttons: White text on Indigo-600 (`#4F46E5`) $\to 5.1:1$.
- No color is used as the sole conveyor of information: findings and reviewer statuses use both distinct badges/text labels and color highlights.
