# LinkNote

LinkNote is a local-first note automation app. It collects Bilibili links from WeChat File Transfer Assistant, clipboard, or manual paste, then generates a daily report and a per-video note workspace with transcript reference, Markdown output, mind map, and AI Q&A.

The project is built for small-team collaboration:

- FastAPI backend
- React + Vite frontend
- local runtime workspace
- Windows-friendly startup scripts
- OpenAI-compatible model providers
- Bilibili subtitle/audio extraction

## What It Does

- Collect Bilibili links from:
  - WeChat File Transfer Assistant
  - clipboard
  - manual input
- Build a daily report page.
- Generate per-video notes.
- Keep multiple note versions after re-analysis.
- Show source transcript references.
- Generate Markmap mind maps from Markdown.
- Ask questions against the current note and transcript.
- Run scheduled daily collection locally.

## Requirements

- Windows 10/11
- Python 3.12+
- Node.js 20+
- npm
- ffmpeg recommended for audio/video processing
- A model provider API key for analysis and transcription

Public Bilibili videos with platform subtitles may work without cookies. Restricted videos usually need `cookies.txt` or browser-cookie fallback.

## Quick Start

Clone the repository, then run:

```powershell
cd linknote
.\scripts\bootstrap.cmd
.\scripts\start-app.cmd
```

The packaged app opens from the FastAPI server:

```text
http://127.0.0.1:8765/
```

For development mode with Vite hot reload:

```powershell
cd linknote
.\scripts\start-dev.cmd
```

Development frontend:

```text
http://127.0.0.1:3015/
```

## First Run Setup

Open `Settings` in the app and configure:

- WeChat `chatlog` root if you want WeChat ingestion.
- Model provider and model.
- API key or API-key environment variable.
- Optional Bilibili `cookies.txt` path.
- Optional audio transcription provider/model.

Runtime settings are saved under:

```text
workspace/runtime/linknote.json
```

That file is ignored by Git because it can contain local paths and secrets.

## Repository Layout

```text
linknote/
  backend/                 FastAPI backend
  frontend/                React + Vite frontend
  scripts/                 Windows startup/bootstrap scripts
  docs/                    Architecture and collaboration documentation
  workspace/               Local runtime data, ignored by Git
  linknote.example.json    Sanitized config example
```

## Backend Layout

```text
backend/app/
  analysis/        OpenAI-compatible generation and prompt workflow
  config/          Settings schema, defaults, path normalization
  downloaders/     Bilibili subtitle/audio/video fetching
  ingest/          Clipboard and WeChat input collection
  models/          Dataclasses for media, notes, reports
  routers/         FastAPI route contracts
  services/        Business orchestration and persistence
  transcription/   Audio transcription adapters
```

## Frontend Layout

```text
frontend/src/
  api.ts           Backend API client and payload normalization
  app/             App shell and shared components
  layouts/         Page layout wrappers
  pages/           Route-level screens and page-local components
  types.ts         Frontend API types
```

## Collaboration Docs

- `CONTRIBUTING.md`: branch, PR, and review workflow
- `docs/CODE_GUIDE.md`: naming, comments, and module-boundary rules
- `docs/ARCHITECTURE.md`: system overview
- `docs/LINKNOTE_MIGRATION_PLAN.md`: historical migration notes and early-scope decisions
- `docs/LINKNOTE_PROJECT_BOOK.md`: longer project book and implementation notes

## Common Commands

Install everything and build the frontend:

```powershell
.\scripts\bootstrap.cmd
```

Start packaged local app:

```powershell
.\scripts\start-app.cmd
```

Start backend and frontend dev servers:

```powershell
.\scripts\start-dev.cmd
```

Backend only:

```powershell
cd backend
python -m app.run_local
```

Frontend only:

```powershell
cd frontend
npm install
npm run dev
```

Build frontend:

```powershell
cd frontend
npm run build
```

## Runtime Data Policy

Do not commit:

- `workspace/`
- `linknote.json`
- `cookies.txt`
- API keys
- WeChat databases
- downloaded audio/video
- generated notes
- local browser profiles

Use `linknote.example.json` and `backend/.env.example` for examples.

## Troubleshooting

- `Frontend dependencies are missing`: run `scripts\bootstrap.cmd`.
- `Missing backend dependencies`: run `cd backend; python -m pip install -e .`.
- `No enabled model provider`: enable a provider in Settings.
- `API Key missing`: configure an API key in Settings or set the configured environment variable.
- `Bilibili cookies required`: set `cookies.txt` or enable browser-cookie fallback.
- `WeChat data directory unavailable`: fix the `chatlog` path in Settings.
- Long videos stay in progress for a while: local audio transcription can be CPU-heavy; the UI shows the current analysis stage.

## License

MIT
