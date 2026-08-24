# db.py
"""Persistence layer.

Reads/writes go through SQLAlchemy so the same code works against a local
SQLite file (zero-config local development) and a hosted Postgres database
such as Supabase (required for real persistence once deployed, since
Streamlit Community Cloud's local filesystem is wiped on every restart).

To point the app at Postgres/Supabase, add this to `.streamlit/secrets.toml`:

    [connections.db]
    url = "postgresql+psycopg2://postgres:<password>@<host>:5432/postgres"

Without that secret, the app falls back to a local `cricplan.db` SQLite file.

Each organizer/admin can own multiple tournaments (identified by a stable
`id`); `tournament_name` is globally unique across the whole app so it can
be browsed and linked to by name alone, with no "by <owner>" qualifier
needed to tell two tournaments apart.
"""
import json

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    url = None
    try:
        url = st.secrets["connections"]["db"]["url"]
    except (KeyError, FileNotFoundError):
        url = None

    if url:
        # NullPool: opens a fresh connection per checkout instead of
        # reusing pooled ones. Hosted poolers (Supabase's pgbouncer in
        # particular) can silently drop or recycle backend connections
        # between requests in ways a long-lived SQLAlchemy pool doesn't
        # always detect even with pool_pre_ping, surfacing as an opaque
        # OperationalError on whatever query runs next. A low-traffic
        # Streamlit app doesn't need connection reuse badly enough to be
        # worth that fragility.
        return create_engine(url, poolclass=NullPool, pool_pre_ping=True)
    return create_engine("sqlite:///cricplan.db", connect_args={"check_same_thread": False})


def _pk(engine: Engine) -> str:
    return "INTEGER PRIMARY KEY AUTOINCREMENT" if engine.dialect.name == "sqlite" else "SERIAL PRIMARY KEY"


def _bool(engine: Engine) -> str:
    return "BOOLEAN NOT NULL DEFAULT 0" if engine.dialect.name == "sqlite" else "BOOLEAN NOT NULL DEFAULT FALSE"


def _table_columns(conn, engine: Engine, table: str) -> set[str]:
    if engine.dialect.name == "sqlite":
        return {c[1] for c in conn.execute(text(f"PRAGMA table_info({table})")).all()}
    rows = conn.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = :t"
    ), {"t": table}).all()
    return {r[0] for r in rows}


@st.cache_resource(show_spinner=False)
def init_db() -> Engine:
    engine = get_engine()
    pk, bool_col = _pk(engine), _bool(engine)
    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS users (
                id {pk},
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                approved {bool_col},
                linked_tournament_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS tournament_data (
                id {pk},
                owner_username TEXT NOT NULL,
                tournament_name TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS teams (
                id {pk},
                tournament_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                captain_username TEXT NOT NULL,
                contact_email TEXT,
                contact_phone TEXT,
                players TEXT,
                approved {bool_col},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tournament_id, team_name)
            )
        """))
        # Sponsor logos are stored in the database (base64 PNG), not as
        # uploaded files — Streamlit Cloud's disk doesn't persist, same
        # reason everything else here lives in the DB rather than on disk.
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS sponsors (
                id {pk},
                tournament_id INTEGER NOT NULL,
                sponsor_name TEXT NOT NULL,
                image_data TEXT,
                link_url TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        _migrate_legacy_single_tournament_schema(conn, engine, pk, bool_col)
    return engine


def _migrate_legacy_single_tournament_schema(conn, engine: Engine, pk: str, bool_col: str) -> None:
    """One-time migration from the old "one tournament per owner" model
    (teams/sponsors scoped by owner_username, tournament_data unique on
    owner_username) to the current "many tournaments per owner, globally
    unique name, everything scoped by tournament_id" model.

    A pre-existing `teams` table from before this change never has a
    `tournament_id` column (CREATE TABLE IF NOT EXISTS above is a no-op
    against it), which is what signals that this migration needs to run.
    A brand-new database always gets the current schema directly and
    never hits this path.
    """
    if "tournament_id" in _table_columns(conn, engine, "teams"):
        return

    # tournament_data: dedupe any names colliding across different owners
    # (e.g. everyone's default was literally "Default Tournament") before
    # the new UNIQUE(tournament_name) constraint can be applied.
    rows = conn.execute(text(
        "SELECT id, owner_username, tournament_name, data, updated_at FROM tournament_data"
    )).all()
    seen = set()
    renamed = []
    for tid, owner, tname, data, updated in rows:
        final_name = tname
        suffix = 2
        while final_name in seen:
            final_name = f"{tname} ({owner} {suffix})" if suffix > 2 else f"{tname} ({owner})"
            suffix += 1
        seen.add(final_name)
        renamed.append((tid, owner, final_name, data, updated))

    conn.execute(text("ALTER TABLE tournament_data RENAME TO tournament_data_old"))
    conn.execute(text(f"""
        CREATE TABLE tournament_data (
            id {pk},
            owner_username TEXT NOT NULL,
            tournament_name TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    for tid, owner, tname, data, updated in renamed:
        conn.execute(text("""
            INSERT INTO tournament_data (id, owner_username, tournament_name, data, updated_at)
            VALUES (:id, :ou, :tn, :d, :u)
        """), {"id": tid, "ou": owner, "tn": tname, "d": data, "u": updated})
    conn.execute(text("DROP TABLE tournament_data_old"))

    owner_to_id = {owner: tid for tid, owner, _tname, _d, _u in renamed}

    # teams: add tournament_id, backfill by matching the team's old owner
    # to that owner's (now single, pre-migration) tournament, then rebuild
    # with the new tournament-scoped unique constraint.
    conn.execute(text("ALTER TABLE teams RENAME TO teams_old"))
    conn.execute(text(f"""
        CREATE TABLE teams (
            id {pk},
            tournament_id INTEGER NOT NULL,
            team_name TEXT NOT NULL,
            captain_username TEXT NOT NULL,
            contact_email TEXT,
            contact_phone TEXT,
            players TEXT,
            approved {bool_col},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tournament_id, team_name)
        )
    """))
    old_teams = conn.execute(text(
        "SELECT id, team_name, captain_username, owner_username, contact_email, contact_phone, players, approved, created_at FROM teams_old"
    )).all()
    for (team_id, team_name, captain, owner, c_email, c_phone, players, approved, created) in old_teams:
        tid = owner_to_id.get(owner)
        if tid is None:
            continue
        conn.execute(text("""
            INSERT INTO teams (id, tournament_id, team_name, captain_username, contact_email, contact_phone, players, approved, created_at)
            VALUES (:id, :tid, :tn, :cu, :ce, :cp, :pl, :ap, :cr)
        """), {"id": team_id, "tid": tid, "tn": team_name, "cu": captain, "ce": c_email, "cp": c_phone,
                "pl": players, "ap": approved, "cr": created})
    conn.execute(text("DROP TABLE teams_old"))

    # sponsors: same idea, simpler (no unique constraint to rebuild around).
    conn.execute(text("ALTER TABLE sponsors ADD COLUMN tournament_id INTEGER"))
    for owner, tid in owner_to_id.items():
        conn.execute(text("UPDATE sponsors SET tournament_id = :tid WHERE owner_username = :ou"), {"tid": tid, "ou": owner})

    # users: replace the (owner, name) pair with a single stable id.
    conn.execute(text("ALTER TABLE users ADD COLUMN linked_tournament_id INTEGER"))
    for owner, tid in owner_to_id.items():
        conn.execute(text(
            "UPDATE users SET linked_tournament_id = :tid WHERE linked_owner = :ou"
        ), {"tid": tid, "ou": owner})


# --- Users ---------------------------------------------------------------

def get_user(username: str) -> dict | None:
    engine = init_db()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE username = :u"), {"u": username}).mappings().first()
        return dict(row) if row else None


def count_users() -> int:
    engine = init_db()
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM users")).scalar_one()


def create_user(username: str, email: str, password_hash: str, role: str, approved: bool,
                 linked_tournament_id: int | None = None) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (username, email, password_hash, role, approved, linked_tournament_id)
            VALUES (:u, :e, :p, :r, :a, :lt)
        """), {"u": username, "e": email, "p": password_hash, "r": role, "a": approved, "lt": linked_tournament_id})


def list_pending_users() -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT username, email, role FROM users WHERE approved = :a ORDER BY created_at"
        ), {"a": False}).mappings().all()
        return [dict(r) for r in rows]


def list_all_users() -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT u.username, u.email, u.role, u.approved, u.linked_tournament_id, u.created_at,
                   t.tournament_name AS linked_tournament_name
            FROM users u
            LEFT JOIN tournament_data t ON t.id = u.linked_tournament_id
            ORDER BY u.created_at
        """)).mappings().all()
        return [dict(r) for r in rows]


def count_admins() -> int:
    engine = init_db()
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'Admin'")).scalar_one()


def set_user_approved(username: str, approved: bool) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET approved = :a WHERE username = :u"), {"a": approved, "u": username})


def approve_user(username: str) -> None:
    set_user_approved(username, True)


def update_user_role(username: str, role: str) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET role = :r WHERE username = :u"), {"r": role, "u": username})


def set_password(username: str, password_hash: str) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET password_hash = :p WHERE username = :u"), {"p": password_hash, "u": username})


def delete_user(username: str) -> None:
    engine = init_db()
    with engine.begin() as conn:
        # Cascade: drop any teams captained by this account so they don't
        # linger as orphans pointing at a deleted user.
        conn.execute(text("DELETE FROM teams WHERE captain_username = :u"), {"u": username})
        conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": username})


# --- Teams -----------------------------------------------------------------

def create_team(tournament_id: int, team_name: str, captain_username: str,
                 contact_email: str, contact_phone: str, players: list[str]) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO teams (tournament_id, team_name, captain_username, contact_email, contact_phone, players, approved)
            VALUES (:tid, :tn, :cu, :ce, :cp, :pl, :ap)
        """), {"tid": tournament_id, "tn": team_name, "cu": captain_username,
                "ce": contact_email, "cp": contact_phone, "pl": json.dumps(players), "ap": False})


def _parse_team_rows(rows) -> list[dict]:
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["players"] = json.loads(d["players"]) if d.get("players") else []
        except json.JSONDecodeError:
            d["players"] = []
        result.append(d)
    return result


def get_teams_for_tournament(tournament_id: int) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM teams WHERE tournament_id = :tid ORDER BY created_at"
        ), {"tid": tournament_id}).mappings().all()
    return _parse_team_rows(rows)


def get_teams_for_captain(captain_username: str) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM teams WHERE captain_username = :cu ORDER BY created_at"
        ), {"cu": captain_username}).mappings().all()
    return _parse_team_rows(rows)


def approve_team(team_id: int) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("UPDATE teams SET approved = :a WHERE id = :id"), {"a": True, "id": team_id})


def delete_team(team_id: int) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM teams WHERE id = :id"), {"id": team_id})


# --- Tournaments -------------------------------------------------------

def is_tournament_name_taken(tournament_name: str, exclude_id: int | None = None) -> bool:
    engine = init_db()
    with engine.connect() as conn:
        if exclude_id is not None:
            row = conn.execute(text(
                "SELECT 1 FROM tournament_data WHERE tournament_name = :tn AND id != :id"
            ), {"tn": tournament_name, "id": exclude_id}).first()
        else:
            row = conn.execute(text(
                "SELECT 1 FROM tournament_data WHERE tournament_name = :tn"
            ), {"tn": tournament_name}).first()
    return row is not None


def create_tournament(owner_username: str, tournament_name: str, data: dict | None = None) -> int | None:
    """Returns the new tournament's id, or None if the name is already taken."""
    if is_tournament_name_taken(tournament_name):
        return None
    engine = init_db()
    payload = json.dumps(data or {'tournament_name': tournament_name})
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO tournament_data (owner_username, tournament_name, data)
            VALUES (:ou, :tn, :d)
        """), {"ou": owner_username, "tn": tournament_name, "d": payload})
        return result.lastrowid if engine.dialect.name == "sqlite" else conn.execute(
            text("SELECT id FROM tournament_data WHERE tournament_name = :tn"), {"tn": tournament_name}
        ).scalar_one()


def rename_tournament(tournament_id: int, new_name: str) -> bool:
    """Returns False without changing anything if the name is taken by a different tournament."""
    if is_tournament_name_taken(new_name, exclude_id=tournament_id):
        return False
    engine = init_db()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT data FROM tournament_data WHERE id = :id"), {"id": tournament_id}).mappings().first()
        if not row:
            return False
        try:
            data = json.loads(row["data"])
        except json.JSONDecodeError:
            data = {}
        data['tournament_name'] = new_name
        conn.execute(text("""
            UPDATE tournament_data SET tournament_name = :tn, data = :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id
        """), {"tn": new_name, "d": json.dumps(data), "id": tournament_id})
    return True


def get_tournament(tournament_id: int) -> dict | None:
    if not tournament_id:
        return None
    engine = init_db()
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT id, owner_username, tournament_name, updated_at FROM tournament_data WHERE id = :id"
        ), {"id": tournament_id}).mappings().first()
    return dict(row) if row else None


def get_tournaments_for_owner(owner_username: str) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, tournament_name FROM tournament_data WHERE owner_username = :ou ORDER BY tournament_name"
        ), {"ou": owner_username}).mappings().all()
    return [dict(r) for r in rows]


def load_tournament_data(tournament_id: int) -> dict:
    if not tournament_id:
        return {}
    engine = init_db()
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT data FROM tournament_data WHERE id = :id"
        ), {"id": tournament_id}).mappings().first()
    if not row:
        return {}
    try:
        return json.loads(row["data"])
    except json.JSONDecodeError:
        return {}


def save_tournament_data(tournament_id: int, data: dict) -> None:
    if not tournament_id:
        return
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE tournament_data SET data = :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id"
        ), {"d": json.dumps(data), "id": tournament_id})


def list_tournaments() -> list[dict]:
    """Every tournament in the app — for public browsing, registration, and admin management."""
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, owner_username, tournament_name FROM tournament_data ORDER BY tournament_name"
        )).mappings().all()
    return [dict(r) for r in rows]


def delete_tournament(tournament_id: int) -> None:
    """Deletes a tournament and everything scoped to it: the tournament
    data itself (teams list, groups, schedule, results, knockout bracket,
    checklist, flyer), self-registered teams, and sponsors. Team
    captains/players linked to it keep their accounts but are unlinked,
    since the tournament they joined no longer exists."""
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tournament_data WHERE id = :id"), {"id": tournament_id})
        conn.execute(text("DELETE FROM teams WHERE tournament_id = :id"), {"id": tournament_id})
        conn.execute(text("DELETE FROM sponsors WHERE tournament_id = :id"), {"id": tournament_id})
        conn.execute(text(
            "UPDATE users SET linked_tournament_id = NULL WHERE linked_tournament_id = :id"
        ), {"id": tournament_id})


# --- Sponsors --------------------------------------------------------------

def add_sponsor(tournament_id: int, sponsor_name: str, image_data: str | None, link_url: str | None = None) -> None:
    engine = init_db()
    with engine.begin() as conn:
        next_order = conn.execute(text(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM sponsors WHERE tournament_id = :tid"
        ), {"tid": tournament_id}).scalar_one()
        conn.execute(text("""
            INSERT INTO sponsors (tournament_id, sponsor_name, image_data, link_url, sort_order)
            VALUES (:tid, :name, :img, :link, :ord)
        """), {"tid": tournament_id, "name": sponsor_name, "img": image_data, "link": link_url, "ord": next_order})


def get_sponsors(tournament_id: int) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM sponsors WHERE tournament_id = :tid ORDER BY sort_order, created_at"
        ), {"tid": tournament_id}).mappings().all()
    return [dict(r) for r in rows]


def delete_sponsor(sponsor_id: int) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sponsors WHERE id = :id"), {"id": sponsor_id})
