# Cricket Scheduler Pro

Running a weekend cricket tournament usually means a spreadsheet, a WhatsApp group, and a lot of manual work: chasing team registrations, drawing groups by hand, typing up a round-robin schedule, and then redoing half of it when a team drops out two days before the first match. This app is meant to take that pain away.

It's a Streamlit web app that handles the whole lifecycle of a tournament — team sign-ups, group draws, round-robin scheduling, live results, and a knockout bracket — so an organizer can spend their time actually running the tournament instead of building spreadsheets for it. And because everything lives behind proper accounts and roles, you can hand off pieces of the work (a co-manager, a team captain updating their own roster) without losing control of the tournament itself.

The app is live at **[cricplan.streamlit.app](https://cricplan.streamlit.app/)** — no install needed if you just want to look around or run your own tournament on it.

## What it does

- **Team registration**, either self-serve (captains sign up and wait for approval) or added directly by an organizer.
- **Groups and round-robin scheduling**, generated automatically once teams and grounds/umpires are set up.
- **Live results and standings**, with net run rate factored in.
- **Knockout bracket** for the playoff stage once the league phase wraps up.
- **A prep checklist** for all the non-cricket logistics — water, ice, canopies, trophies, whatever your tournament needs — so nothing gets forgotten on match day.
- **Sponsors and a flyer** on the tournament's home page, because someone paid for that banner and it should be seen.
- **A registration link** (a Google Form, or whatever your sign-up flow is) that you set once and it shows up as a "Register Your Team" button on the tournament's home page, for organizers and casual visitors alike.
- **Multiple tournaments, side by side.** One organizer account can run several tournaments — this year's, last year's archive, a side event — and switch between them from a single picker instead of needing a separate login for each.

Nobody needs to log in just to check the schedule. Anyone can open the app, pick a tournament from the sidebar, and see the fixtures, results, and bracket without an account. Accounts only come into play once someone needs to *change* something.

## Who does what

**Admin** and **Tournament Organizer** are effectively the same thing day-to-day — full control over the tournaments they own. They set the tournament's name and date, manage grounds and umpires, approve team registrations, generate the schedule, enter results, run the knockout stage, and hand out the registration link. The one thing that separates them: only an Admin can approve another Organizer or Admin signing up (a regular Organizer can approve team captains and players, but not a peer), and only an Admin gets the User Management page — the one place to look up any account, reset a password, change a role, or delete a tournament outright.

**Manager** exists for the very common case where an organizer wants help but doesn't want to hand over the whole tournament. An organizer assigns a Manager to one or more specific tournaments, and from that point the Manager can do essentially everything the organizer can on those tournaments — manage teams, run the schedule, enter results, update the checklist. What they *can't* do is create, rename, or delete a tournament, assign other managers, or touch User Management. It's delegation without giving up the keys.

**Team Captain** registers their own team once their account is approved — roster, contact details, the works — for the one tournament they signed up for. That team then needs a second nod from the tournament's organizer before it's officially in.

**Player** is a simple, auto-approved, view-only account — useful for a player who just wants to check their team's schedule and results without anyone needing to vet them first.

Every account past the very first one needs approval from an organizer or admin before it can log in. (The first account you ever register becomes an approved Admin automatically — otherwise nobody could get the tournament started.)

Tournament names are unique across the whole app, which is what lets anyone find and join a tournament by name alone, with no "which organizer's tournament?" ambiguity. And as tournaments pile up year over year, giving one an actual date means the pickers everywhere sort chronologically instead of turning into an alphabetical junk drawer.

## Running it locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run Home.py
```

That's it — no database to set up. With no further configuration, everything is stored in a local `cricplan.db` SQLite file sitting next to the code.

## Putting it online for free

GitHub Pages won't work here — it only serves static files, and this needs a live Python process plus a database. [Streamlit Community Cloud](https://streamlit.io/cloud) is the free option: push this repo to GitHub, connect it at share.streamlit.io, and point it at `Home.py`.

One catch: Streamlit Community Cloud wipes its filesystem on every restart, so the local SQLite file won't survive there. You'll want a small free Postgres database instead — [Supabase](https://supabase.com) is a good fit:

1. Create a free project at supabase.com.
2. Go to Project Settings → Database → Connection string → URI, and use the "Session pooler" connection.
3. In your Streamlit Cloud app's **Secrets** settings, add:

   ```toml
   [connections.db]
   url = "postgresql+psycopg2://postgres:<password>@<host>:5432/postgres"
   ```

   (`.streamlit/secrets.toml.example` has the same, for local testing against Postgres if you'd rather not use SQLite.)

That's the only setup required — the app creates and migrates its own tables the first time it runs.

## Making it your own

- The club logo (`assets/logo.png`) shows up in the sidebar, the browser tab, and on the home page's hero banner. Swap the file to rebrand, and regenerate the small companion copy at `assets/logo_small.png` (any square PNG downscaled to roughly 160×160 works).
- The **tournament flyer** is uploaded per-tournament from the Tournament Setup page and appears on that tournament's home page.
- **Sponsors** (logo plus an optional link) are added from the Manage Resources page and show up as a scrolling carousel on the home page.

Flyers, sponsor logos, and everything else that isn't plain text are stored in the database itself (as base64), not on disk — which is the only reason they survive a restart on Streamlit Community Cloud.
