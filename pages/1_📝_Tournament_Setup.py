# pages/1_📝_Tournament_Setup.py
import streamlit as st

import db
import images
import sidebar
import ui
from utils import save_tourney_data, is_organizer, get_tourney_owner_and_name

ui.inject_global_css()
sidebar.render()
ui.guard_login()

ui.page_header("Tournament Setup", "Name your tournament and manage the teams competing in it.", "📝")

if not is_organizer():
    st.subheader("Registered Teams")
    if st.session_state.get('teams'):
        for team in st.session_state.teams:
            st.markdown(f"- {team}")
    else:
        ui.empty_state("No teams have been added yet.")
    st.stop()

# --- Organizer's view ---
def _rename_tournament():
    st.session_state.tournament_name = st.session_state.tournament_name_input
    save_tourney_data()


st.text_input("Tournament Name", value=st.session_state.tournament_name, key="tournament_name_input", on_change=_rename_tournament)

st.markdown("#### 🖼️ Tournament Flyer")
flyer = st.session_state.get('flyer_image')
if flyer:
    st.image(f"data:image/png;base64,{flyer}", width=320)
    if st.button("Remove Flyer"):
        st.session_state.flyer_image = None
        save_tourney_data()
        st.rerun()
else:
    uploaded_flyer = st.file_uploader("Upload a flyer image", type=["png", "jpg", "jpeg", "webp"], key="flyer_uploader")
    if uploaded_flyer is not None:
        try:
            st.session_state.flyer_image = images.process_upload(uploaded_flyer, max_dim=1200)
            save_tourney_data()
            st.rerun()
        except images.UploadTooLarge as e:
            st.error(str(e))
st.markdown("---")

owner, tname = get_tourney_owner_and_name()
pending_teams = [t for t in db.get_teams_for_owner(owner) if not t['approved']]

if pending_teams:
    st.markdown("#### 🧢 Pending team registrations")
    st.caption("Team captains registered these teams themselves. Approve to add them to the tournament.")
    for t in pending_teams:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{ui.esc(t['team_name'])}**  ·  captain: {ui.esc(t['captain_username'])}", unsafe_allow_html=True)
                if t.get('players'):
                    st.caption("Players: " + ", ".join(t['players']))
                if t.get('contact_email') or t.get('contact_phone'):
                    st.caption(f"Contact: {t.get('contact_email') or ''} {t.get('contact_phone') or ''}".strip())
            with c2:
                if st.button("✅ Approve", key=f"approve_team_{t['id']}", use_container_width=True):
                    db.approve_team(t['id'])
                    if t['team_name'] not in st.session_state.teams:
                        st.session_state.teams.append(t['team_name'])
                        save_tourney_data()
                    st.rerun()
            with c3:
                if st.button("🗑️ Reject", key=f"reject_team_{t['id']}", use_container_width=True):
                    db.delete_team(t['id'])
                    st.rerun()
    st.markdown("---")

with st.form("add_team_form", clear_on_submit=True):
    st.markdown("**Add a team directly** (e.g. walk-in teams without a captain account)")
    name = st.text_input("New Team Name")
    submitted = st.form_submit_button("Add Team")
    if submitted and name and name not in st.session_state.teams:
        st.session_state.teams.append(name)
        save_tourney_data()
        st.rerun()

st.markdown("---")
st.subheader(f"Registered Teams ({len(st.session_state.teams)})")
if st.session_state.teams:
    for team in st.session_state.teams:
        c1, c2 = st.columns([0.9, 0.1])
        c1.write(team)
        if c2.button("🗑️", key=f"del_{team}"):
            st.session_state.teams.remove(team)
            if team in st.session_state.league_results:
                del st.session_state.league_results[team]
            save_tourney_data()
            st.rerun()
else:
    ui.empty_state("No teams registered yet — add one above, or wait for team captains to self-register.")
