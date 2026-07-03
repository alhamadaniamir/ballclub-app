# MAB Sports Ballclub - Behind the Scenes

This is the engine that powers the [MAB Sports Ballclub](https://mab-ballclub.vercel.app)
app. You don't see it directly, but it's what remembers everything and keeps the
app working: your members, your game sessions, who has paid, and the login that
keeps the club's data private.

Think of the app you tap on as the front desk, and this as the back office that
stores the records and does the bookkeeping.

## What it takes care of

- **Signing in.** Checks owner usernames and passwords and keeps the club's data
  secure.
- **Sessions and queues.** Keeps each game session, the players in line, fees, and
  who has paid.
- **Members.** Stores your player list and each member's history (sessions played
  and payments).
- **Join requests.** Handles players requesting to join a session from a shared
  link, so owners can approve them.
- **Totals and reports.** Adds up revenue and stats for the dashboard, and creates
  the spreadsheet (CSV) downloads.

## Where it lives

- The live service runs online (in Singapore for speed) and connects to a secure
  cloud database.
- It pairs with the app's front end, which is on the
  [`frontend`](https://github.com/adam-ctrlc/ballclub-app/tree/frontend) branch.
- Nothing here needs to be touched to use the app, just open
  [mab-ballclub.vercel.app](https://mab-ballclub.vercel.app) and sign in.

## For developers

This is a Python (FastAPI) service backed by MongoDB. If you want to run it
locally, set it up, or contribute, the full technical instructions, environment
setup, and testing steps are in [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

Free to use and build on under the Apache License 2.0. See [LICENSE](./LICENSE).
