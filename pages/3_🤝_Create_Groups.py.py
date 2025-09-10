import streamlit as st
from utils import save_tourney_data, is_organizer
import random

if not st.session_state.get('user_logged_in') or not is_organizer(): st.warning("This page is for organizers only.", icon="🔒"); st.stop()

st.title("🤝 Create Groups") 
if not st.session_state.teams: st.warning("Please add teams first."); st.stop()
st.info("Groups need at least 3 teams for the League Stage's automatic team-as-umpire system.")
max_g = len(st.session_state.teams) // 3
if max_g == 0 and len(st.session_state.teams) > 0: max_g = 1
num_g = st.number_input("Number of groups", 1, max(1,max_g), min(2, max(1,max_g)), disabled=(len(st.session_state.teams) < 3))
if st.button("Generate Groups", use_container_width=True, disabled=(len(st.session_state.teams) < 3)):
    shuffled = random.sample(st.session_state.teams, len(st.session_state.teams)); st.session_state.groups = {f"Group {chr(65+i)}":[] for i in range(num_g)}
    for i, t in enumerate(shuffled): st.session_state.groups[f"Group {chr(65+(i%num_g))}"].append(t)
    st.session_state.schedule = []; save_tourney_data(); st.rerun()
if st.session_state.groups:
    st.markdown("---")
    cols = st.columns(len(st.session_state.groups))
    for i, (name, teams) in enumerate(st.session_state.groups.items()):
        with cols[i]: st.subheader(name); st.markdown('\n'.join(f'- {t}' for t in teams))