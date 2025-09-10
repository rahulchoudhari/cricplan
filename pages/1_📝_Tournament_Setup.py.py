# pages/1_📝_Tournament_Setup.py
import streamlit as st
from utils import save_tourney_data, is_organizer

if not st.session_state.get('user_logged_in'):
    st.warning("Please log in to manage the tournament.", icon="🔒")
    st.stop()

st.title("📝 Tournament Setup")
if not is_organizer():
    st.info("This page is for organizers. You can view registered teams below.")
    st.subheader("Registered Teams")
    st.write(st.session_state.get('teams', []))
    st.stop()

# Organizer's view
st.text_input("Tournament Name", key="tournament_name", on_change=save_tourney_data)
with st.form("add_team_form", clear_on_submit=True):
    name = st.text_input("New Team Name"); submitted = st.form_submit_button("Add Team")
    if submitted and name and name not in st.session_state.teams:
        st.session_state.teams.append(name); save_tourney_data(); st.rerun()
if st.session_state.teams:
    st.subheader("Registered Teams")
    for team in st.session_state.teams:
        c1,c2 = st.columns([0.9,0.1]); c1.write(team)
        if c2.button("🗑️", key=f"del_{team}"):
            st.session_state.teams.remove(team)
            if team in st.session_state.league_results: del st.session_state.league_results[team]
            save_tourney_data(); st.rerun()