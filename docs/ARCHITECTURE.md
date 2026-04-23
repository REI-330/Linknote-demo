# LinkNote Architecture

## Product Shape

- Input sources:
  - WeChat File Transfer Assistant links collected over a time window
  - clipboard link ingestion
  - manual Bilibili link paste
- Primary navigation:
  - daily report page
  - per-note detail page
- Notification:
  - Windows toast opens the current daily report page

## Backend Boundaries

### `config`

Holds runtime configuration, default values, path expansion, and workspace directory creation.

### `ingest`

Owns raw input acquisition only.

- `clipboard.py`: reads the current clipboard text
- `wechat.py`: snapshots WeChat databases and extracts candidate link lines
- `wechat_refresh.py`: refreshes decrypted WeChat export data when needed
- `store.py`: persists raw collected text into dated inbox files

### `downloaders`

- `bilibili.py`: platform-specific media fetch, subtitle fetch, BV normalization, cookies fallback

### `analysis`

- prompt building
- OpenAI-compatible generation
- transcript-first note generation
- markmap derivation from Markdown

### `notes`

- note record persistence
- daily report assembly
- re-analysis version stacking
- retention cleanup

### `daily`

- scheduled runs
- manual runs
- Windows completion notification
- startup doctor and health bootstrap

## Frontend Boundaries

- `app`: shell, routing, layout
- current shell includes:
  - daily report page
  - note workspace
  - settings page
  - health/setup guidance

The UI should keep LinkNote's own product language: daily-report-first navigation, a focused single-note workspace, and a local-app feel that stays simple enough for non-technical users.
