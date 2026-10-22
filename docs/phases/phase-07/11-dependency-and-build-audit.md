# Phase 7 — Dependency Audit & Build Reproducibility

## 1. Backend Dependency Tree (`apps/backend/pyproject.toml`)
- **FastAPI / Server:** `fastapi==0.143.0`, `uvicorn==0.54.0`, `pydantic==2.14.1`
- **NLP / ML:** `torch==2.14.1`, `transformers==5.19.0`, `numpy==2.5.4`, `scikit-learn==1.9.1`
- **Document Processing:** `pypdf==6.20.1`, `python-docx==1.2.0`, `pypdfium2==5.14.0`
- **Reporting:** `reportlab==5.0.1`, `pillow==12.3.0`
- **Database & Storage:** `sqlalchemy==2.1.4`, `alembic==1.20.0`
- **Testing:** `pytest==9.1.1`, `httpx==0.28.1`

## 2. Frontend Dependency Tree (`apps/web/package.json`)
- **Framework:** `react==18.3.1`, `react-dom==18.3.1`
- **Build & Bundler:** `vite==5.4.21`, `typescript==5.9.3`
- **Styling:** `tailwindcss==3.4.19`, `autoprefixer==10.6.1`, `postcss==8.5.30`
- **Icons:** `lucide-react==0.453.0`
- **Testing:** `vitest==2.1.9`, `@testing-library/react==16.3.3`, `jsdom==25.0.1`

## 3. Build Reproducibility Sign-Off
- Clean compilation confirmed: `tsc && vite build` completed in 2.79s with 0 errors.
- Bundle output:
  - `dist/index.html`: 0.56 kB
  - `dist/assets/index-*.css`: 43.07 kB
  - `dist/assets/index-*.js`: 279.65 kB
