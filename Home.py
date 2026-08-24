# Home.py
import streamlit as st

import db
import sidebar
import ui
from utils import get_tourney_owner_and_name

st.set_page_config(page_title="Cricket Scheduler Pro", page_icon="assets/logo.png", layout="wide")
ui.inject_global_css()
sidebar.render()

# --- Main Page Content ---
tname = st.session_state.get('tournament_name', 'Cricket Scheduler Pro')
if st.session_state.user_logged_in:
    ui.hero(tname, "Your tournament command center", "🏆")

    flyer = st.session_state.get('flyer_image')
    if flyer:
        fc1, fc2, fc3 = st.columns([1, 2, 1])
        with fc2:
            st.image(f"data:image/png;base64,{flyer}", use_container_width=True)

    owner, _ = get_tourney_owner_and_name()
    if owner:
        ui.sponsor_carousel(db.get_sponsors(owner))

    st.subheader("Welcome to your Tournament Dashboard")
    st.info("Use the navigation panel on the left to manage your tournament.")

    if st.session_state.get('teams'):
        c1, c2, c3 = st.columns(3)
        c1.metric("Teams Registered", len(st.session_state.get('teams', [])))
        c2.metric("Groups Created", len(st.session_state.get('groups', {})))
        c3.metric("League Matches", len(st.session_state.get('schedule', [])))
else:
    ui.hero("Cricket Scheduler Pro", "The all-in-one platform to plan, schedule and run your cricket tournament.", "🏆")
    st.markdown("Please **login** or **register** using the panel on the left to begin.")
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
