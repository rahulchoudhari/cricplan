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

- **Admin / Tournament Organizer** — run a tournament: set its name, manage grounds/umpires, approve team registrations and new accounts, generate groups/schedule, enter results, run the knockout bracket.
- **Team Captain** — after an organizer approves their account, registers their team's roster on the "My Team" page; the team needs a second approval (from the organizer) before it appears in the tournament.
- **Player** — view-only account, auto-approved at signup.

Admins get a **User Management** page (sidebar) for direct CRUD on accounts and roles — approve, change role, delete, or create an account outright without going through self-registration.

## Branding

- The club logo (`assets/logo.png`) is used as the sidebar mark, the browser tab icon, and on the Home hero. Swap that file to rebrand; a downscaled copy for inline use lives alongside it at `assets/logo_small.png` — regenerate it if you replace the logo (any square PNG resized to ~160×160 works).
- **Tournament flyer** — organizers upload one flyer image on the Tournament Setup page; it displays on the Home page for everyone in that tournament.
- **Sponsors** — organizers add sponsor logos (+ optional link) on the Manage Resources page; they display as a scrolling carousel on the Home page. Like everything else, sponsor logos and the flyer are stored in the database (base64), not on disk, so they survive restarts on Streamlit Community Cloud.
