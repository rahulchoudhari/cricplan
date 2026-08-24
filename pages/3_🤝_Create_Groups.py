# pages/3_🤝_Create_Groups.py
import random

import streamlit as st

import sidebar
import ui
from utils import save_tourney_data

ui.inject_global_css()
sidebar.render()
ui.guard_organizer()

ui.page_header("Create Groups", "Randomly split registered teams into balanced groups.", "🤝")

if not st.session_state.teams:
    ui.empty_state("Add teams first on the Tournament Setup page.")
    st.stop()

st.info("Groups need at least 3 teams for the League Stage's automatic team-as-umpire system.")
max_g = len(st.session_state.teams) // 3
if max_g == 0 and len(st.session_state.teams) > 0:
    max_g = 1
num_g = st.number_input("Number of groups", 1, max(1, max_g), min(2, max(1, max_g)), disabled=(len(st.session_state.teams) < 3))
if st.button("Generate Groups", type="primary", width='stretch', disabled=(len(st.session_state.teams) < 3)):
    shuffled = random.sample(st.session_state.teams, len(st.session_state.teams))
    st.session_state.groups = {f"Group {chr(65 + i)}": [] for i in range(num_g)}
    for i, t in enumerate(shuffled):
        st.session_state.groups[f"Group {chr(65 + (i % num_g))}"].append(t)
    st.session_state.schedule = []
    save_tourney_data()
    st.rerun()

if st.session_state.groups:
    st.markdown("---")
    cols = st.columns(len(st.session_state.groups))
    for i, (name, teams) in enumerate(st.session_state.groups.items()):
        with cols[i]:
            with st.container(border=True):
                st.subheader(name)
                st.markdown('\n'.join(f'- {t}' for t in teams))
