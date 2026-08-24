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
"""
import json

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    url = None
    try:
        url = st.secrets["connections"]["db"]["url"]
    except (KeyError, FileNotFoundError):
        url = None

    if url:
        return create_engine(url, pool_pre_ping=True)
    return create_engine("sqlite:///cricplan.db", connect_args={"check_same_thread": False})


def _pk(engine: Engine) -> str:
    return "INTEGER PRIMARY KEY AUTOINCREMENT" if engine.dialect.name == "sqlite" else "SERIAL PRIMARY KEY"


def _bool(engine: Engine) -> str:
    return "BOOLEAN NOT NULL DEFAULT 0" if engine.dialect.name == "sqlite" else "BOOLEAN NOT NULL DEFAULT FALSE"


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
                linked_owner TEXT,
                linked_tournament TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS teams (
                id {pk},
                team_name TEXT NOT NULL,
                captain_username TEXT NOT NULL,
                owner_username TEXT NOT NULL,
                tournament_name TEXT NOT NULL,
                contact_email TEXT,
                contact_phone TEXT,
                players TEXT,
                approved {bool_col},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_username, team_name)
            )
        """))
        # One row per organizer: an organizer runs a single active tournament
        # at a time (matches how every page already treats it). Renaming the
        # tournament updates this row in place instead of forking a new one,
        # which is what let a captain's "join a tournament" picker show a
        # stale pre-rename entry.
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS tournament_data (
                id {pk},
                owner_username TEXT UNIQUE NOT NULL,
                tournament_name TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Sponsor logos are stored in the database (base64 PNG), not as
        # uploaded files — Streamlit Cloud's disk doesn't persist, same
        # reason everything else here lives in the DB rather than on disk.
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS sponsors (
                id {pk},
                owner_username TEXT NOT NULL,
                sponsor_name TEXT NOT NULL,
                image_data TEXT,
                link_url TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        _ensure_sponsor_logo_optional(conn, engine, pk)
    return engine


def _ensure_sponsor_logo_optional(conn, engine: Engine, pk: str) -> None:
    """One-time migration: sponsors.image_data used to be NOT NULL. A
    database created before logos became optional still has that
    constraint, which CREATE TABLE IF NOT EXISTS above can't retroactively
    lift — so fix it up here if needed."""
    if engine.dialect.name == "sqlite":
        col = next((c for c in conn.execute(text("PRAGMA table_info(sponsors)")).all() if c[1] == "image_data"), None)
        if col and col[3] == 1:  # notnull flag
            conn.execute(text("ALTER TABLE sponsors RENAME TO sponsors_old"))
            conn.execute(text(f"""
                CREATE TABLE sponsors (
                    id {pk},
                    owner_username TEXT NOT NULL,
                    sponsor_name TEXT NOT NULL,
                    image_data TEXT,
                    link_url TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                INSERT INTO sponsors (id, owner_username, sponsor_name, image_data, link_url, sort_order, created_at)
                SELECT id, owner_username, sponsor_name, image_data, link_url, sort_order, created_at FROM sponsors_old
            """))
            conn.execute(text("DROP TABLE sponsors_old"))
    else:
        conn.execute(text("ALTER TABLE sponsors ALTER COLUMN image_data DROP NOT NULL"))


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
                 linked_owner: str | None = None, linked_tournament: str | None = None) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (username, email, password_hash, role, approved, linked_owner, linked_tournament)
            VALUES (:u, :e, :p, :r, :a, :lo, :lt)
        """), {"u": username, "e": email, "p": password_hash, "r": role, "a": approved,
                "lo": linked_owner, "lt": linked_tournament})


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
        rows = conn.execute(text(
            "SELECT username, email, role, approved, linked_owner, linked_tournament, created_at "
            "FROM users ORDER BY created_at"
        )).mappings().all()
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


def delete_user(username: str) -> None:
    engine = init_db()
    with engine.begin() as conn:
        # Cascade: drop any teams captained by this account so they don't
        # linger as orphans pointing at a deleted user.
        conn.execute(text("DELETE FROM teams WHERE captain_username = :u"), {"u": username})
        conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": username})


# --- Teams -----------------------------------------------------------------

def create_team(team_name: str, captain_username: str, owner_username: str, tournament_name: str,
                 contact_email: str, contact_phone: str, players: list[str]) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO teams (team_name, captain_username, owner_username, tournament_name,
                                contact_email, contact_phone, players, approved)
            VALUES (:tn, :cu, :ou, :tour, :ce, :cp, :pl, :ap)
        """), {"tn": team_name, "cu": captain_username, "ou": owner_username, "tour": tournament_name,
                "ce": contact_email, "cp": contact_phone, "pl": json.dumps(players), "ap": False})


def get_teams_for_owner(owner_username: str) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT * FROM teams WHERE owner_username = :ou ORDER BY created_at
        """), {"ou": owner_username}).mappings().all()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["players"] = json.loads(d["players"]) if d.get("players") else []
        except json.JSONDecodeError:
            d["players"] = []
        result.append(d)
    return result


def get_teams_for_captain(captain_username: str) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM teams WHERE captain_username = :cu ORDER BY created_at"
        ), {"cu": captain_username}).mappings().all()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["players"] = json.loads(d["players"]) if d.get("players") else []
        except json.JSONDecodeError:
            d["players"] = []
        result.append(d)
    return result


def approve_team(team_id: int) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("UPDATE teams SET approved = :a WHERE id = :id"), {"a": True, "id": team_id})


def delete_team(team_id: int) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM teams WHERE id = :id"), {"id": team_id})


# --- Tournament data (schedule, groups, results, checklist, ...) ---------

def load_tournament_data(owner_username: str) -> dict:
    if not owner_username:
        return {}
    engine = init_db()
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT data FROM tournament_data WHERE owner_username = :ou"
        ), {"ou": owner_username}).mappings().first()
    if not row:
        return {}
    try:
        return json.loads(row["data"])
    except json.JSONDecodeError:
        return {}


def save_tournament_data(owner_username: str, tournament_name: str, data: dict) -> None:
    if not owner_username or not tournament_name:
        return
    engine = init_db()
    payload = json.dumps(data)
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO tournament_data (owner_username, tournament_name, data, updated_at)
            VALUES (:ou, :tn, :d, CURRENT_TIMESTAMP)
            ON CONFLICT (owner_username)
            DO UPDATE SET tournament_name = excluded.tournament_name, data = excluded.data, updated_at = CURRENT_TIMESTAMP
        """), {"ou": owner_username, "tn": tournament_name, "d": payload})


def list_tournaments() -> list[tuple[str, str]]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT owner_username, tournament_name FROM tournament_data ORDER BY owner_username"
        )).all()
    return [(r[0], r[1]) for r in rows]


# --- Sponsors --------------------------------------------------------------

def add_sponsor(owner_username: str, sponsor_name: str, image_data: str, link_url: str | None = None) -> None:
    engine = init_db()
    with engine.begin() as conn:
        next_order = conn.execute(text(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM sponsors WHERE owner_username = :ou"
        ), {"ou": owner_username}).scalar_one()
        conn.execute(text("""
            INSERT INTO sponsors (owner_username, sponsor_name, image_data, link_url, sort_order)
            VALUES (:ou, :name, :img, :link, :ord)
        """), {"ou": owner_username, "name": sponsor_name, "img": image_data, "link": link_url, "ord": next_order})


def get_sponsors(owner_username: str) -> list[dict]:
    engine = init_db()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM sponsors WHERE owner_username = :ou ORDER BY sort_order, created_at"
        ), {"ou": owner_username}).mappings().all()
    return [dict(r) for r in rows]


def delete_sponsor(sponsor_id: int) -> None:
    engine = init_db()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sponsors WHERE id = :id"), {"id": sponsor_id})
