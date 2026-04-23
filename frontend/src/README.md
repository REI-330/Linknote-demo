# Frontend Module Map

Use this file when deciding where a frontend change belongs.

## `api.ts`

All backend calls and response normalization live here. If the backend payload changes, update `types.ts` and the normalizer together.

## `types.ts`

Shared frontend types for API payloads and UI state.

## `app`

The application shell and shared components used across pages.

Examples:

- routing orchestration
- shared markdown rendering
- shared chat panel
- shared provider logo rendering

## `layouts`

Layout wrappers that define page structure but do not own business state.

## `pages`

Route-level screens and page-local components:

- report page
- note detail page
- settings pages
- page-specific workspace components

## Naming Rules

- Route screens use `Page`.
- Large page-local UI units use `Panel`, `Viewer`, or `Layout`.
- Prop types use `Props`.
- Keep user-facing copy in page/components, not in API helpers.
