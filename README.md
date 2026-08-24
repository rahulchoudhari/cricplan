# Cricket Scheduler Pro

A Streamlit app for planning and running a cricket tournament: team registration, groups, round-robin scheduling, results, and a knockout bracket.

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run Home.py
```

With no further setup, data is stored in a local `cricplan.db` SQLite file. The first account you register becomes an approved Admin automatically; every account after that needs approval from an organizer/admin (visible in the sidebar under "Pending approvals").

## Deploy for free

**GitHub Pages won't work for this app** — it only serves static files, and this is a live Python server with a database. Use [Streamlit Community Cloud](https://streamlit.io/cloud) instead (free tier): push this repo to GitHub, connect it at share.streamlit.io, and point it at `Home.py`.

Streamlit Community Cloud's filesystem is wiped on every restart, so the local SQLite fallback **will not persist** there. Before deploying, create a free Postgres database — [Supabase](https://supabase.com) works well:

1. Create a project at supabase.com (free tier).
2. Project Settings → Database → Connection string → URI (use the "Session pooler" connection).
3. In your Streamlit Cloud app's **Secrets** settings, paste:

   ```toml
   [connections.db]
   url = "postgresql+psycopg2://postgres:<password>@<host>:5432/postgres"
   ```

   (See `.streamlit/secrets.toml.example` for the same, for local use.)

That's the only required config — the app creates its tables automatically on first run.

## Roles

- **Admin / Tournament Organizer** — can own **multiple tournaments** (switch or create new ones from the "My Tournaments" picker on Tournament Setup); for whichever one is active, they set its name, manage grounds/umpires, approve team registrations, generate groups/schedule, enter results, and run the knockout bracket. Registering as a Tournament Organizer or Admin requires approval from an existing **Admin** specifically (a peer Tournament Organizer can't approve that, only participant-facing signups).
- **Team Captain** — after their account is approved, registers their team's roster on the "My Team" page for the one tournament they joined at signup; the team needs a second approval (from that tournament's organizer) before it appears.
- **Player** — view-only account, auto-approved at signup.

Tournament names are **globally unique** across the whole app — that's what lets anyone browse or join one by name alone, with no "by <organizer>" qualifier needed to tell two tournaments apart.

Admins get a **User Management** page (sidebar) for direct CRUD on accounts and roles — approve, change role, delete, or create an account outright without going through self-registration — plus a **Tournaments** section to delete any organizer's tournament (organizers can only delete their own).

Nobody needs an account to browse: **Home, League Schedule, League Results, and Knock Out Fixture** are open to anyone, with a "Browse a Tournament" picker in the sidebar to choose which one to view. Every other page still requires login.

## Branding

- The club logo (`assets/logo.png`) is used as the sidebar mark, the browser tab icon, and on the Home hero. Swap that file to rebrand; a downscaled copy for inline use lives alongside it at `assets/logo_small.png` — regenerate it if you replace the logo (any square PNG resized to ~160×160 works).
- **Tournament flyer** — organizers upload one flyer image on the Tournament Setup page; it displays on the Home page for everyone in that tournament.
- **Sponsors** — organizers add sponsor logos (+ optional link) on the Manage Resources page; they display as a scrolling carousel on the Home page. Like everything else, sponsor logos and the flyer are stored in the database (base64), not on disk, so they survive restarts on Streamlit Community Cloud.
