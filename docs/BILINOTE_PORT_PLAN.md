# BiliNote Port Plan

This document defines which BiliNote capabilities should be ported into LinkNote for the first usable release.

## Keep In First Release

- Bilibili-only note generation flow
- prompt-builder-driven note format and note style selection
- transcript-first analysis basis
- per-note markdown output
- markmap-based mind map view
- transcript/reference side panel
- AI chat panel based on note markdown, transcript, and metadata
- manual re-analysis that creates appended versions
- source timestamp jump links
- settings pages for providers, models, transcriber, and schedule
- task status progression in the UI

## Replace With LinkNote-Specific Input Flow

- original BiliNote URL form
  replaced by:
  - WeChat File Transfer Assistant collection
  - clipboard collection
  - manual Bilibili paste

- original task history entrypoint
  replaced by:
  - daily report page as the primary entry
  - note detail page under each daily report item

## Exclude In First Release

- multi-platform downloaders beyond Bilibili
- screenshot insertion into notes
- local video upload flow
- Douyin / Kuaishou / YouTube specific settings and downloader UX
- export formats beyond Markdown

## Backend Migration Order

1. Introduce BiliNote-compatible prompt format/style system into LinkNote analysis layer.
2. Port Bilibili transcript/download orchestration into a dedicated `sources` and `analysis` split.
3. Port note markdown generation and source-link post-processing.
4. Port vector-store and chat tools for note-scoped AI Q&A.
5. Add daily report persistence and retention around the per-note artifacts.

## Frontend Migration Order

1. Rebuild application shell around daily report as the default page.
2. Recreate single-note workspace layout:
   - note content
   - transcript panel
   - mind map mode
   - AI chat side panel
3. Add stacked re-analysis version blocks under the same note page.
4. Recreate settings pages using LinkNote wording and simplified scope.

## Non-Negotiable Constraints

- Do not reintroduce the old knowledge-digest dashboard or report-generation stack.
- Do not let Bilibili-specific logic leak into generic UI state.
- Keep the ingest layer isolated from analysis and note rendering.
- Do not claim a video was understood unless transcript text exists.
