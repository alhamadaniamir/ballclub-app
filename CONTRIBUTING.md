# Contributing - MAB Sports Ballclub Frontend

Thanks for your interest in improving the frontend. This document covers the
setup, conventions, and workflow specific to this Vue 3 + Vite app.

## Development setup

1. Install Node.js 20+ and npm.
2. `npm install`
3. `cp .env.example .env` and set `VITE_API_URL` to your backend (default
   `http://localhost:8000/api`). You'll want the backend (`backend` branch)
   running too.
4. `npm run dev` and open http://localhost:5173

## Branch and PR workflow

- The default branch is `frontend`. Branch from it: `git checkout -b feat/<short-name>`.
- Keep PRs focused and small. Reference any related issue.
- Ensure `npm run build` succeeds before opening a PR (this is what Vercel runs).
- Describe user-facing changes and include screenshots for UI changes.

## Coding conventions

- **Vue**: Composition API with `<script setup>`. One component per file, PascalCase filenames.
- **Imports**: use the `@/` alias (configured in `jsconfig.json` / Vite) instead of long relative paths.
- **UI**: reuse the shadcn-vue primitives in `src/components/ui`. Do not hand-roll
  buttons/inputs/dialogs that already exist there. New shadcn components go via
  `npx shadcn-vue@latest add <name>`.
- **Icons**: use `@phosphor-icons/vue` (e.g. `PhUser`), not inline SVG or other icon sets.
- **Styling**: Tailwind CSS v4 utility classes; stick to the brand tokens/CSS
  variables already defined in `src/style.css`. The app is dark-themed.
- **Validation**: add/extend Zod schemas in `src/lib/validation.js`; surface the
  first error via `firstIssueMessage`.
- **API calls**: go through `src/lib/api.js` (the shared `request` client that
  attaches the auth token and handles 401), not raw `fetch`.
- **Comments**: prefer self-explanatory code; add comments only where intent is
  non-obvious.

## Before you submit

- [ ] `npm run build` passes
- [ ] No console errors in the browser during a manual smoke test
- [ ] New UI is responsive (works with the mobile bottom nav)
- [ ] No secrets committed; `.env` stays local (`.env.example` documents keys)

## Reporting bugs / requesting features

Open a GitHub issue with clear steps to reproduce (for bugs) or a description of
the use case (for features). Include the browser and screen size when relevant.
