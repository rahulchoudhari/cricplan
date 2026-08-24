# ui.py
"""Shared visual styling and small UI helpers used across every page."""
import base64
import html
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

ROLE_STYLES = {
    "Admin": ("#7C2D12", "#FEF3C7", "cric-badge-admin"),
    "Tournament Organizer": ("#1E3A8A", "#DBEAFE", "cric-badge-organizer"),
    "Team Captain": ("#065F46", "#D1FAE5", "cric-badge-captain"),
    "Player": ("#334155", "#E2E8F0", "cric-badge-player"),
}

LOGO_PATH = Path(__file__).parent / "assets" / "logo_small.png"


def esc(value) -> str:
    """Escape user-controlled text before it goes into raw HTML."""
    return html.escape(str(value), quote=True)


def sanitize_url(url: str | None) -> str | None:
    """Only allow http(s) links through into href attributes, blocking javascript: etc."""
    if not url:
        return None
    url = url.strip()
    try:
        scheme = urlparse(url).scheme.lower()
    except ValueError:
        return None
    return url if scheme in ("http", "https") else None


@st.cache_data(show_spinner=False)
def logo_data_uri() -> str | None:
    if not LOGO_PATH.exists():
        return None
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        }
        [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
        [data-testid="stSidebar"] .cric-badge-admin { color: #7C2D12 !important; background: #FEF3C7 !important; }
        [data-testid="stSidebar"] .cric-badge-organizer { color: #1E3A8A !important; background: #DBEAFE !important; }
        [data-testid="stSidebar"] .cric-badge-captain { color: #065F46 !important; background: #D1FAE5 !important; }
        [data-testid="stSidebar"] .cric-badge-player { color: #334155 !important; background: #E2E8F0 !important; }
        [data-testid="stSidebar"] input {
            color: #0F172A !important;
            background-color: #F8FAFC !important;
        }
        [data-testid="stSidebar"] [data-testid="stForm"] {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1rem;
        }
        [data-testid="stSidebar"] button[kind="secondary"],
        [data-testid="stSidebar"] button[kind="secondary"] * { color: #0F172A !important; }
        [data-testid="stSidebar"] .stTabs [data-baseweb="tab"] { color: #CBD5E1 !important; }
        [data-testid="stSidebar"] .stTabs [aria-selected="true"] { color: #FFFFFF !important; font-weight: 600; }

        div[data-testid="stForm"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
        }
        [data-testid="stMetric"] {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1rem;
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: #2563EB;
            border-color: #2563EB;
        }

        .cric-hero {
            display: flex; align-items: center; gap: 1.5rem;
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 55%, #0EA5E9 100%);
            border-radius: 18px;
            padding: 2.25rem 2.5rem;
            margin-bottom: 1.75rem;
            color: #FFFFFF;
            box-shadow: 0 10px 30px rgba(30, 58, 138, 0.25);
        }
        .cric-hero-logo {
            width: 72px; height: 72px; border-radius: 50%; flex-shrink: 0;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        }
        .cric-hero-text { flex: 1; min-width: 0; }
        .cric-hero h1 { margin: 0; font-size: 2rem; font-weight: 800; color: #FFFFFF; }
        .cric-hero p { margin: 0.4rem 0 0 0; font-size: 1.02rem; color: #DBEAFE; }

        .cric-sponsors { margin-bottom: 1.75rem; }
        .cric-sponsors-label {
            font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
            color: #94A3B8; text-align: center; margin-bottom: 0.75rem;
        }
        .cric-sponsor-carousel {
            overflow: hidden; width: 100%;
            mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
            -webkit-mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
        }
        .cric-sponsor-track {
            display: flex; align-items: center; gap: 3rem; width: max-content;
            animation: cric-scroll 28s linear infinite;
        }
        .cric-sponsor-track img {
            height: 56px; width: auto; max-width: 160px; object-fit: contain;
            filter: grayscale(15%);
        }
        @keyframes cric-scroll {
            from { transform: translateX(0); }
            to { transform: translateX(-50%); }
        }

        .cric-page-header {
            display: flex; align-items: center; gap: 0.65rem;
            margin-bottom: 0.25rem;
        }
        .cric-page-header .icon { font-size: 1.8rem; }
        .cric-page-header h2 { margin: 0; font-weight: 800; color: #0F172A; }
        .cric-subtitle { color: #64748B; margin-bottom: 1.25rem; font-size: 0.95rem; }

        .cric-badge {
            display: inline-block; padding: 0.15rem 0.65rem; border-radius: 999px;
            font-size: 0.78rem; font-weight: 700; letter-spacing: 0.01em;
        }
        .cric-pill-pending {
            display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
            font-size: 0.75rem; font-weight: 700; background: #FEF3C7; color: #92400E;
        }
        .cric-pill-approved {
            display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
            font-size: 0.75rem; font-weight: 700; background: #D1FAE5; color: #065F46;
        }
        .cric-empty {
            text-align: center; padding: 2.5rem 1rem; color: #94A3B8;
            border: 1.5px dashed #E2E8F0; border-radius: 14px;
        }

        .cric-task-section { font-weight: 700; color: #0F172A; margin: 1rem 0 0.5rem 0; font-size: 0.95rem; }
        .cric-task-row {
            display: flex; align-items: baseline; gap: 0.55rem;
            padding: 0.5rem 0.85rem; border-radius: 8px; margin-bottom: 0.35rem;
            background: #F8FAFC; border: 1px solid #E2E8F0; font-size: 0.92rem; color: #0F172A;
        }
        .cric-task-row.cric-task-done {
            background: #D1FAE5; border-color: #A7F3D0; color: #065F46;
        }
        .cric-task-row.cric-task-done .cric-task-name { text-decoration: line-through; text-decoration-color: #34D399; }
        .cric-task-owner { color: #64748B; font-size: 0.82rem; }
        .cric-task-row.cric-task-done .cric-task-owner { color: #047857; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str = "", icon: str = "🏆") -> None:
    logo = logo_data_uri()
    logo_html = f'<img class="cric-hero-logo" src="{logo}" alt="Club logo">' if logo else ""
    st.markdown(
        f"""
        <div class="cric-hero">
            {logo_html}
            <div class="cric-hero-text">
                <h1>{esc(icon)} {esc(title)}</h1>
                {f'<p>{esc(subtitle)}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sponsor_carousel(sponsors: list[dict]) -> None:
    """A CSS-only, infinitely-scrolling strip of sponsor logos."""
    if not sponsors:
        return
    tiles = []
    for s in sponsors:
        img = f'<img src="data:image/png;base64,{s["image_data"]}" alt="{esc(s["sponsor_name"])}" title="{esc(s["sponsor_name"])}">'
        link = sanitize_url(s.get("link_url"))
        tiles.append(f'<a href="{esc(link)}" target="_blank" rel="noopener noreferrer">{img}</a>' if link else img)
    track_html = "".join(tiles) * 2  # duplicated for a seamless loop
    st.markdown(
        f"""
        <div class="cric-sponsors">
            <div class="cric-sponsors-label">Proudly Sponsored By</div>
            <div class="cric-sponsor-carousel">
                <div class="cric-sponsor-track">{track_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    st.markdown(
        f"""
        <div class="cric-page-header"><span class="icon">{esc(icon)}</span><h2>{esc(title)}</h2></div>
        {f'<div class="cric-subtitle">{esc(subtitle)}</div>' if subtitle else ''}
        """,
        unsafe_allow_html=True,
    )


def role_badge(role: str) -> str:
    color, bg, css_class = ROLE_STYLES.get(role, ("#334155", "#E2E8F0", "cric-badge-player"))
    return f'<span class="cric-badge {css_class}" style="color:{color};background:{bg};">{esc(role)}</span>'


def checklist_by_section(tasks: list[dict], section_order: list[str] | None = None) -> None:
    """Read-only, section-grouped checklist where completed tasks render as a green row."""
    if not tasks:
        return
    by_section: dict[str, list[dict]] = {}
    for t in tasks:
        by_section.setdefault(t.get("Section") or "Other", []).append(t)

    section_order = section_order or []
    ordered = [s for s in section_order if s in by_section] + [s for s in by_section if s not in section_order]

    for section in ordered:
        section_tasks = by_section[section]
        done_count = sum(1 for t in section_tasks if t.get("Done"))
        st.markdown(
            f'<div class="cric-task-section">{esc(section)} · {done_count}/{len(section_tasks)}</div>',
            unsafe_allow_html=True,
        )
        rows = []
        for t in section_tasks:
            done = bool(t.get("Done"))
            icon = "✅" if done else "⬜"
            owner = f'<span class="cric-task-owner">· {esc(t["Owner"])}</span>' if t.get("Owner") else ""
            row_class = "cric-task-row cric-task-done" if done else "cric-task-row"
            rows.append(
                f'<div class="{row_class}">{icon} <span class="cric-task-name">{esc(t.get("Task", ""))}</span>{owner}</div>'
            )
        st.markdown("".join(rows), unsafe_allow_html=True)


def empty_state(message: str) -> None:
    st.markdown(f'<div class="cric-empty">{esc(message)}</div>', unsafe_allow_html=True)


def guard_login() -> None:
    if not st.session_state.get("user_logged_in"):
        st.warning("Please log in from the sidebar to view this page.", icon="🔒")
        st.stop()


def guard_organizer() -> None:
    guard_login()
    if st.session_state.get("role") not in ("Admin", "Tournament Organizer"):
        st.warning("This page is for tournament organizers only.", icon="🔒")
        st.stop()
