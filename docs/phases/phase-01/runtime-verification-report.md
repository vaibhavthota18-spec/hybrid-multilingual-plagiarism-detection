# Phase 1: Real Runtime Verification & Integration Test Report

**System:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Phase:** 1 — Engineering Foundation & Infrastructure  
**Host Machine:** Windows 11 Home Single Language (Build 26200, 64-bit)  
**Execution Environment:** Native Host with Python 3.12.10, Node.js 20.18.0, npm 10.8.2  
**Date of Execution:** October 14, 2026  
**Document Version:** 1.0.0  

---

## 1. Executive Test Summary

All host-accessible runtime verification, type safety, unit testing, schema derivation, and contract validation suites were executed against real runtimes on the user's new Windows 11 laptop. Zero results were simulated or fabricated.

| Test Category | Executed Command | Passed | Failed | Skipped | Exit Code | Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **OpenAPI 3.1 Contract** | `powershell scripts/validate_contract.ps1` | **10** | 0 | 0 | 0 | **PASS** |
| **Phase 0 Integrity** | `powershell scripts/validate_phase0.ps1` | **56** | 0 | 0 | 0 | **PASS** |
| **Backend Unit & API** | `apps/backend/.venv/Scripts/pytest.exe -v apps/backend/tests` | **32** | 0 | 0 | 0 | **PASS** |
| **Frontend TypeScript** | `npm run typecheck` in `apps/web` | **100% Clean** | 0 | 0 | 0 | **PASS** |
| **Frontend Components** | `npm run test` (Vitest) in `apps/web` | **8** | 0 | 0 | 0 | **PASS** |
| **Production Web Build**| `npm run build` (Vite) in `apps/web` | **Success (dist/)** | 0 | 0 | 0 | **PASS** |
| **OpenAPI Schema Export**| `python scripts/export_openapi.py` | **Exported** | 0 | 0 | 0 | **PASS** |
| **Docker Engine & WSL2**| `docker compose up` | *Blocked* | - | - | - | **BLOCKED ON BIOS** |

---

## 2. Detailed Backend Pytest Results (32 Tests)

The backend test suite was executed using Python 3.12.10 in the dedicated virtual environment `apps/backend/.venv`:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend
configfile: pyproject.toml
plugins: anyio-4.15.1, asyncio-1.4.0
collected 32 items

apps\backend\tests\test_config.py::test_default_settings PASSED          [  3%]
apps\backend\tests\test_config.py::test_database_url_formatting PASSED   [  6%]
apps\backend\tests\test_config.py::test_cors_origins_parsing PASSED      [  9%]
apps\backend\tests\test_config.py::test_production_guardrail_weak_secret PASSED [ 12%]
apps\backend\tests\test_config.py::test_production_guardrail_debug_mode PASSED [ 15%]
apps\backend\tests\test_config.py::test_secret_string_masking PASSED     [ 18%]
apps\backend\tests\test_errors.py::test_error_envelope_structure PASSED  [ 21%]
apps\backend\tests\test_errors.py::test_domain_exception_defaults PASSED [ 25%]
apps\backend\tests\test_errors.py::test_exception_handler_middleware PASSED [ 28%]
apps\backend\tests\test_health.py::test_health_status_model_validation PASSED [ 31%]
apps\backend\tests\test_health.py::test_health_endpoint_healthy PASSED   [ 34%]
apps\backend\tests\test_health.py::test_health_endpoint_degraded_db PASSED [ 37%]
apps\backend\tests\test_health.py::test_health_endpoint_degraded_redis PASSED [ 40%]
apps\backend\tests\test_health.py::test_root_health_route_alias PASSED   [ 43%]
apps\backend\tests\test_models.py::test_table_registration_completeness PASSED [ 46%]
apps\backend\tests\test_models.py::test_primary_keys_defined PASSED      [ 50%]
apps\backend\tests\test_models.py::test_foreign_key_relationships PASSED [ 53%]
apps\backend\tests\test_models.py::test_vector_column_definition PASSED  [ 56%]
apps\backend\tests\test_models.py::test_fingerprint_indexes PASSED       [ 59%]
apps\backend\tests\test_security.py::test_jwt_token_creation_and_decoding PASSED [ 62%]
apps\backend\tests\test_security.py::test_jwt_token_expiration_rejection PASSED [ 65%]
apps\backend\tests\test_security.py::test_jwt_invalid_signature_rejection PASSED [ 68%]
apps\backend\tests\test_security.py::test_jwt_algorithm_pinning PASSED   [ 71%]
apps\backend\tests\test_security.py::test_auth_me_authenticated PASSED   [ 75%]
apps\backend\tests\test_security.py::test_auth_me_unauthenticated PASSED [ 78%]
apps\backend\tests\test_security.py::test_rbac_admin_probe_authorized PASSED [ 81%]
apps\backend\tests\test_security.py::test_rbac_admin_probe_forbidden_for_student PASSED [ 84%]
apps\backend\tests\test_worker.py::test_ping_job_execution PASSED        [ 87%]
apps\backend\tests\test_worker.py::test_simulate_calculation_operations PASSED [ 90%]
apps\backend\tests\test_worker.py::test_simulate_calculation_division_by_zero PASSED [ 93%]
apps\backend\tests\test_worker.py::test_simulate_calculation_unknown_operation PASSED [ 96%]
apps\backend\tests\test_worker.py::test_failing_job_error_propagation PASSED [100%]

======================= 32 passed, 3 warnings in 8.91s ========================
```

---

## 3. Detailed Frontend Verification Results (8 Tests & Build)

Executed using Node.js v20.18.0 and npm 10.8.2 in `apps/web`:

```
=== [1/3] TypeScript Typecheck ===
> tsc --noEmit
(Completed with 0 errors)

=== [2/3] Vitest Unit Tests ===
> vitest run
 RUN  v2.1.9 C:/Users/vaibh/OneDrive/Documents/plagarism engine/apps/web

 ✓ tests/client.test.ts (3 tests) 5ms
 ✓ tests/Header.test.tsx (3 tests) 44ms
 ✓ tests/App.test.tsx (2 tests) 237ms

 Test Files  3 passed (3)
      Tests  8 passed (8)
   Duration  1.73s

=== [3/3] Production Bundle Build ===
> tsc && vite build
vite v5.4.21 building for production...
✓ 1579 modules transformed.
dist/index.html                   0.56 kB │ gzip:  0.37 kB
dist/assets/index-COTBQ5Vz.css   18.39 kB │ gzip:  4.06 kB
dist/assets/index-DIcnUOFq.js   174.44 kB │ gzip: 54.19 kB
✓ built in 2.25s
```

---

## 4. OpenAPI 3.1.0 Contract Conformance

Automated verification of `contracts/openapi.yaml` via `scripts/validate_contract.ps1`:
* `openapi: 3.1.0`: **PASS**
* `/health` and `getHealthStatus`: **PASS**
* `HealthStatus` schema: **PASS**
* `ErrorEnvelope` schema: **PASS**
* `/documents` endpoint: **PASS**
* `/analyses` endpoint: **PASS**
* `/analyses/{analysis_id}/report` PDF endpoint: **PASS**
* `/analyses/{analysis_id}/findings/{finding_id}/reviews`: **PASS**
* `BearerAuth` security scheme: **PASS**
* Schema export generated cleanly to `contracts/generated/openapi.json`.

---

## 5. Docker Desktop & WSL2 Runtime Blocker Analysis

* **Condition:** Hardware virtualization flag `VirtualizationFirmwareEnabled` is `False`.
* **Classification:** **EXTERNAL ENVIRONMENT BLOCKER (NON-CODE)**
* **Mitigation Recorded:**
  All container-dependent definitions (`compose.yml`, `infra/docker/Dockerfile.backend`, `Dockerfile.worker`, `Dockerfile.web`, `nginx.conf`, named volumes) are verified syntactically and structurally ready.
  The user has been provided with the setup checkpoint and instructions in `docs/phases/phase-01/laptop-setup-checkpoint.md` to enable VT-x / SVM in BIOS.
