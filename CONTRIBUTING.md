# Contributing to LinkNote

This repository is optimized for a small team collaborating on a local-first Windows app.
The goals are:

- make local setup predictable
- keep runtime data out of Git
- keep backend and frontend boundaries readable
- keep PRs small enough to review quickly

## Quick Start

1. Clone the repository.
2. Run `scripts\bootstrap.cmd`.
3. Run `scripts\start-app.cmd` for the packaged local app.
4. Run `scripts\start-dev.cmd` if you need backend + Vite dev mode.

## Branching

- Use short-lived feature branches.
- Prefer one feature or one bug fix per branch.
- Avoid mixing refactors with behavior changes unless they are tightly coupled.

Suggested branch names:

- `feature/daily-report-filter`
- `fix/bilibili-cookie-detection`
- `docs/setup-guide`

## Pull Requests

Keep each PR focused on one change set:

- what changed
- why it changed
- how it was tested
- any setup or migration impact

If a change touches both backend and frontend, explain the API contract in the PR description.

## Code Style

- Prefer explicit names over abbreviations.
- Keep modules aligned to one responsibility.
- Add short comments only when the control flow or fallback behavior is not obvious.
- Do not commit machine-specific paths, cookies, API keys, chat logs, or generated notes.

See `docs/CODE_GUIDE.md` for the detailed naming and comment conventions used in this repo.

## Testing

Use narrow checks first:

- backend syntax checks for touched files
- small targeted tests
- `npm run build` for frontend changes

Avoid broad, long-running test sweeps unless the change really requires them.

## Runtime Data

Everything under `workspace/` is local runtime state and is intentionally ignored:

- inbox snapshots
- reports
- note records
- downloaded media
- screenshots
- runtime config

Share sanitized examples in `docs/` instead of committing real workspace data.
