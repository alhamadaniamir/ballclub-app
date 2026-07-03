# MAB Sports Ballclub - Frontend

Vue 3 + Vite single-page app for managing a basketball ballclub: owner
dashboard, session queue management, member directory, payments, and a public
join flow. This is the **frontend** branch of
[adam-ctrlc/ballclub-app](https://github.com/adam-ctrlc/ballclub-app); the
FastAPI backend lives on the [`backend`](https://github.com/adam-ctrlc/ballclub-app/tree/backend)
branch.

Live: https://mab-ballclub.vercel.app

## Tech stack

- **Vue 3** (Composition API, `<script setup>`)
- **Vite** build tooling and dev server
- **Vue Router 4** (auth-guarded dashboard routes + a public join route)
- **Tailwind CSS v4** with a dark brand theme
- **shadcn-vue** (Reka UI) components in `src/components/ui`
- **Phosphor Icons** (`@phosphor-icons/vue`)
- **Zod** for form validation, **Chart.js** + **vue-chartjs** for dashboard charts
- **@internationalized/date** for the history date-range picker

## Prerequisites

- Node.js 20+ and npm
- A running instance of the backend API (see the `backend` branch)

## Getting started

```bash
npm install
cp .env.example .env      # then edit VITE_API_URL if needed
npm run dev               # starts Vite on http://localhost:5173
```

### Environment variables

| Variable       | Description                 | Example                     |
| -------------- | --------------------------- | --------------------------- |
| `VITE_API_URL` | Base URL of the backend API | `http://localhost:8000/api` |

`VITE_*` variables are inlined at build time, so changing `VITE_API_URL`
requires a rebuild/redeploy.

## Scripts

| Command           | Description                     |
| ----------------- | ------------------------------- |
| `npm run dev`     | Start the Vite dev server (HMR) |
| `npm run build`   | Production build to `dist/`     |
| `npm run preview` | Preview the production build    |

## Project structure

```
src/
  components/
    auth/          Login form
    dashboard/     Dashboard tabs (overview, history, session, members, owners)
    layout/        Sidebar + mobile bottom nav
    members/       Member row
    session/       Session card, player/pending rows, share link
    ui/            shadcn-vue primitives + shared widgets (Modal, Pagination, ...)
  composables/     useAuth, useConfirm
  layouts/         DashboardLayout
  lib/             api.js (fetch client), validation.js (Zod), utils.js, charts.js
  views/           Login, Join (public), Profile, MemberDetail, NotFound
  router/          Route definitions + auth guard
```

## Authentication

The owner logs in at `/login`; the API returns a JWT that is stored in
`localStorage` and sent as a `Bearer` token by `src/lib/api.js`. A navigation
guard redirects unauthenticated users to `/login`. The `/join` route is public
so players can request to join a session via a shared link.

## Deployment (Vercel)

The app deploys as a static site. `vercel.json` rewrites all routes to
`index.html` for SPA client-side routing. Set `VITE_API_URL` in the Vercel
project's environment variables to the deployed backend URL.

## License

Apache License 2.0 - see [LICENSE](./LICENSE). Contributions welcome; see
[CONTRIBUTING.md](./CONTRIBUTING.md).
