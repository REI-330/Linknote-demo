# LinkNote Code Guide

This guide defines the baseline collaboration rules for naming, comments, and module boundaries.

## Naming

## Python

- Use full words in public function names.
- Prefer verb-first names for actions:
  - `load_app_config`
  - `run_note_analysis`
  - `collect_health_bootstrap`
- Prefer noun-first names for pure data helpers:
  - `note_record_path`
  - `config_path`
  - `report_to_dict`

## TypeScript / React

- Use `Page` suffix for route-level screens.
- Use `Panel`, `Viewer`, or `Layout` suffix for large UI containers.
- Use `Props` suffix for component props types.
- Keep API-normalization helpers close to `api.ts`.

## Comments

Comments should explain one of three things:

- why a fallback exists
- why a boundary exists
- why a non-obvious implementation choice is intentional

Good examples:

- explain why a process cleanup script kills stale backend/frontend processes
- explain why a config file is ignored in Git
- explain why an analysis task writes progress into `note.json`

Avoid comments that only restate the code.

## Module Boundaries

- `backend/app/config`: configuration loading, normalization, persistence
- `backend/app/services`: orchestration and app-level business logic
- `backend/app/downloaders`: source-specific fetching logic
- `backend/app/routers`: HTTP contract only
- `frontend/src/app`: app shell and cross-page orchestration
- `frontend/src/pages`: route-level pages and large page-specific containers
- `frontend/src/api.ts`: client-side API contract normalization

## Suggested Review Checklist

- Is the file name aligned with what the module actually owns?
- Are public names explicit enough to search for later?
- Did the change add any machine-specific path or secret into the repo?
- If a fallback exists, is the reason documented in code or docs?
- If frontend and backend both changed, is the payload shape still obvious?
