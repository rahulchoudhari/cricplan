# pages/1_📝_Tournament_Setup.py
import streamlit as st

import db
import images
import sidebar
import ui
from utils import save_tourney_data, is_organizer, get_active_tournament_id, load_tournament_state, clear_tournament_widget_cache, tourney_widget_key

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

# --- Organizer's view: switch between / create tournaments -----------------
me = st.session_state.username
my_tournaments = db.get_tournaments_for_owner(me)
active_id = get_active_tournament_id()

if my_tournaments:
    names = [t['tournament_name'] for t in my_tournaments]
    ids = [t['id'] for t in my_tournaments]
    current_idx = ids.index(active_id) if active_id in ids else 0
    c1, c2 = st.columns([3, 1])
    with c1:
        picked_name = st.selectbox("My Tournaments", names, index=current_idx, key=tourney_widget_key("tourney_switcher"))
    picked_id = ids[names.index(picked_name)]
    if picked_id != active_id:
        st.session_state.active_tournament_id = picked_id
        load_tournament_state()
        clear_tournament_widget_cache()
        st.rerun()
else:
    st.info("You don't have any tournaments yet — create one below to get started.")

with st.expander("➕ Create a new tournament", expanded=not my_tournaments):
    with st.form("create_tournament_form", clear_on_submit=True):
        new_tourney_name = st.text_input("Tournament Name")
        if st.form_submit_button("Create", type="primary"):
            new_tourney_name = new_tourney_name.strip()
            if not new_tourney_name:
                st.warning("Enter a tournament name.")
            else:
                new_id = db.create_tournament(me, new_tourney_name)
                if new_id is None:
                    st.error(f'A tournament named "{new_tourney_name}" already exists — tournament names must be unique. Pick a different name.')
                else:
                    st.session_state.active_tournament_id = new_id
                    load_tournament_state()
                    clear_tournament_widget_cache()
                    st.success(f'Created "{new_tourney_name}".')
                    st.rerun()

if not active_id:
    st.stop()

st.markdown("---")

# --- Rename (must stay globally unique) -------------------------------------
_name_key = tourney_widget_key("tournament_name_input")


def _rename_tournament():
    new_name = st.session_state[_name_key].strip()
    if not new_name or new_name == st.session_state.tournament_name:
        return
    if db.rename_tournament(active_id, new_name):
        st.session_state.tournament_name = new_name
    else:
        st.session_state['_rename_error'] = new_name


st.text_input("Tournament Name", value=st.session_state.tournament_name, key=_name_key, on_change=_rename_tournament)
rename_error = st.session_state.pop('_rename_error', None)
if rename_error:
    st.error(f'"{rename_error}" is already taken by another tournament — still named "{st.session_state.tournament_name}".')

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

pending_teams = [t for t in db.get_teams_for_tournament(active_id) if not t['approved']]

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
                if st.button("✅ Approve", key=f"approve_team_{t['id']}", width='stretch'):
                    db.approve_team(t['id'])
                    if t['team_name'] not in st.session_state.teams:
                        st.session_state.teams.append(t['team_name'])
                        save_tourney_data()
                    st.rerun()
            with c3:
                if st.button("🗑️ Reject", key=f"reject_team_{t['id']}", width='stretch'):
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

st.markdown("---")
with st.expander("⚠️ Danger Zone"):
    st.warning(
        "Deleting this tournament permanently removes its teams, groups, schedule, results, knockout "
        "bracket, checklist, flyer, and sponsors. Team captains and players linked to it keep their "
        "accounts but are unlinked from it. This cannot be undone."
    )
    current_name = st.session_state.tournament_name
    confirm = st.text_input(f'Type "{current_name}" to confirm deletion', key="delete_tournament_confirm")
    if st.button("Delete This Tournament", type="primary", disabled=(confirm != current_name)):
        db.delete_tournament(active_id)
        remaining = [t for t in my_tournaments if t['id'] != active_id]
        st.session_state.active_tournament_id = remaining[0]['id'] if remaining else None
        st.session_state.tournament_name = "New Tournament"
        load_tournament_state()
        clear_tournament_widget_cache()
        st.success("Tournament deleted.")
        st.rerun()
