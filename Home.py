# Home.py
import streamlit as st

import db
import sidebar
import ui
from utils import get_active_tournament_id

st.set_page_config(page_title="Cricket Scheduler Pro", page_icon="assets/logo.png", layout="wide")
ui.inject_global_css()
sidebar.render()


def _tournament_overview(subtitle: str) -> None:
    tname = st.session_state.get('tournament_name', 'Cricket Scheduler Pro')
    ui.hero(tname, subtitle, "🏆")

    registration_link = st.session_state.get('registration_link')
    if registration_link:
        rc1, rc2, rc3 = st.columns([1, 2, 1])
        with rc2:
            st.link_button("📝 Register Your Team", registration_link, width='stretch', type="primary")

    flyer = st.session_state.get('flyer_image')
    if flyer:
        fc1, fc2, fc3 = st.columns([1, 2, 1])
        with fc2:
            st.image(f"data:image/png;base64,{flyer}", width='stretch')

    tid = get_active_tournament_id()
    if tid:
        ui.sponsor_carousel(db.get_sponsors(tid))

    if st.session_state.get('teams'):
        c1, c2, c3 = st.columns(3)
        c1.metric("Teams Registered", len(st.session_state.get('teams', [])))
        c2.metric("Groups Created", len(st.session_state.get('groups', {})))
        c3.metric("League Matches", len(st.session_state.get('schedule', [])))


# --- Main Page Content ---
if st.session_state.user_logged_in:
    _tournament_overview("Your tournament command center")
    st.subheader("Welcome to your Tournament Dashboard")
    st.info("Use the navigation panel on the left to manage your tournament.")

elif st.session_state.get('public_tournament_id'):
    _tournament_overview("Browsing as a guest")
    st.info(
        "Use the navigation panel on the left for the League Schedule, League Results, and Knockout "
        "Fixture — no login required. Log in or register from the sidebar if you're a team captain, "
        "player, or organizer."
    )

else:
    ui.hero("Cricket Scheduler Pro", "The all-in-one platform to plan, schedule and run your cricket tournament.", "🏆")
    st.markdown("No tournaments have been set up yet. Please **login** or **register** using the panel on the left to begin.")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("#### 🧢 Teams self-register")
            st.caption("Team captains sign up, register their roster, and wait for organizer approval.")
    with c2:
        with st.container(border=True):
            st.markdown("#### 🗓️ Auto-scheduling")
            st.caption("Groups, round-robin fixtures, grounds and umpires generated automatically.")
    with c3:
        with st.container(border=True):
            st.markdown("#### 📊 Live standings")
            st.caption("Track results, net run rate, and the knockout bracket in one place.")
