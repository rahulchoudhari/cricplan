# pages/1_📝_Tournament_Setup.py
import streamlit as st

import db
import images
import sidebar
import ui
from utils import save_tourney_data, is_organizer, can_manage_tournament, get_active_tournament_id, load_tournament_state, clear_tournament_widget_cache, tourney_widget_key

ui.inject_global_css()
sidebar.render()
ui.guard_login()

ui.page_header("Tournament Setup", "Name your tournament and manage the teams competing in it.", "📝")

me = st.session_state.username

if not can_manage_tournament():
    st.subheader("Registered Teams")
    if st.session_state.get('teams'):
        for team in st.session_state.teams:
            st.markdown(f"- {team}")
    else:
        ui.empty_state("No teams have been added yet.")
    st.stop()

is_owner = is_organizer()  # Admin or Tournament Organizer -- can create/rename/delete, assign Managers

# --- Switch between / create tournaments ------------------------------------
my_tournaments = db.get_tournaments_for_owner(me) if is_owner else db.get_tournaments_for_manager(me)
active_id = get_active_tournament_id()

if my_tournaments:
    labels = [ui.tournament_option_label(t) for t in my_tournaments]
    ids = [t['id'] for t in my_tournaments]
    current_idx = ids.index(active_id) if active_id in ids else 0
    switcher_label = "My Tournaments" if is_owner else "My Assigned Tournaments"
    picked_label = st.selectbox(switcher_label, labels, index=current_idx, key=tourney_widget_key("tourney_switcher"))
    picked_id = ids[labels.index(picked_label)]
    if picked_id != active_id:
        st.session_state.active_tournament_id = picked_id
        load_tournament_state()
        clear_tournament_widget_cache()
        st.rerun()
elif is_owner:
    st.info("You don't have any tournaments yet — create one below to get started.")
else:
    st.info("You haven't been assigned to any tournaments yet. Ask an organizer to add you as a manager.")

if is_owner:
    with st.expander("➕ Create a new tournament", expanded=not my_tournaments):
        with st.form("create_tournament_form", clear_on_submit=True):
            new_tourney_name = st.text_input("Tournament Name")
            new_tourney_date = st.date_input("Tournament Date (optional)", value=None)
            if st.form_submit_button("Create", type="primary"):
                new_tourney_name = new_tourney_name.strip()
                if not new_tourney_name:
                    st.warning("Enter a tournament name.")
                else:
                    new_id = db.create_tournament(me, new_tourney_name)
                    if new_id is None:
                        st.error(f'A tournament named "{new_tourney_name}" already exists — tournament names must be unique. Pick a different name.')
                    else:
                        if new_tourney_date:
                            db.set_tournament_date(new_id, new_tourney_date)
                        st.session_state.active_tournament_id = new_id
                        load_tournament_state()
                        clear_tournament_widget_cache()
                        st.success(f'Created "{new_tourney_name}".')
                        st.rerun()

if not active_id:
    st.stop()

st.markdown("---")

# --- Name, date (owner only -- name must stay globally unique) -------------
if is_owner:
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

    current_tournament = db.get_tournament(active_id) or {}
    _date_key = tourney_widget_key("tournament_date_input")

    def _update_tournament_date():
        db.set_tournament_date(active_id, st.session_state[_date_key])

    st.date_input(
        "Tournament Date (optional)", value=current_tournament.get('tournament_date'),
        key=_date_key, on_change=_update_tournament_date,
    )
else:
    st.markdown(f"### {ui.esc(st.session_state.tournament_name)}", unsafe_allow_html=True)
    current_tournament = db.get_tournament(active_id) or {}
    if current_tournament.get('tournament_date'):
        st.caption(f"📅 {current_tournament['tournament_date'].strftime('%B %d, %Y')}")

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

# --- Registration link (e.g. a Google Form for team/player sign-up) -------
_reg_link_key = tourney_widget_key("registration_link_input")

def _update_registration_link():
    st.session_state.registration_link = st.session_state[_reg_link_key]
    save_tourney_data()

st.markdown("#### 🔗 Registration Link")
st.caption("Paste the registration form link (e.g. a Google Form) team captains and players should fill out to join this tournament.")
st.text_input("Registration Form Link", value=st.session_state.registration_link, key=_reg_link_key, on_change=_update_registration_link)
if st.session_state.registration_link:
    st.caption(f"[Open the registration form]({st.session_state.registration_link})")
st.markdown("---")

# --- Managers (owner only -- delegating access, so only an owner grants it) -
if is_owner:
    st.markdown("#### 👥 Managers")
    st.caption("Managers can help run this tournament (schedule, teams, resources, results) but can't rename, delete, or create tournaments.")
    current_managers = db.get_managers_for_tournament(active_id)
    if current_managers:
        for mgr in current_managers:
            c1, c2 = st.columns([0.85, 0.15])
            c1.write(f"🔑 {mgr}")
            if c2.button("Remove", key=f"remove_mgr_{mgr}"):
                db.remove_manager(active_id, mgr)
                st.rerun()
    else:
        ui.empty_state("No managers assigned yet.")

    manager_candidates = [
        u['username'] for u in db.list_all_users()
        if u['role'] == 'Manager' and u['approved'] and u['username'] not in current_managers
    ]
    if manager_candidates:
        with st.form("add_manager_form", clear_on_submit=True):
            picked_manager = st.selectbox("Add a manager", manager_candidates)
            if st.form_submit_button("Add Manager"):
                db.add_manager(active_id, picked_manager)
                st.rerun()
    else:
        st.caption("No approved Manager accounts available to add — ask someone to register with the Manager role first.")
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

if is_owner:
    st.markdown("---")
    with st.expander("⚠️ Danger Zone"):
        st.warning(
            "Deleting this tournament permanently removes its teams, groups, schedule, results, knockout "
            "bracket, checklist, flyer, sponsors, and manager assignments. Team captains and players linked "
            "to it keep their accounts but are unlinked from it. This cannot be undone."
        )
        current_name = st.session_state.tournament_name
        confirm = st.text_input(f'Type "{current_name}" to confirm deletion', key="delete_tournament_confirm")
        if st.button("Delete This Tournament", type="primary", disabled=(confirm != current_name)):
            try:
                db.delete_tournament(active_id)
            except Exception as e:
                st.error(f"Delete failed: {e}")
            else:
                remaining = [t for t in my_tournaments if t['id'] != active_id]
                st.session_state.active_tournament_id = remaining[0]['id'] if remaining else None
                st.session_state.tournament_name = "New Tournament"
                load_tournament_state()
                clear_tournament_widget_cache()
                st.success("Tournament deleted.")
                st.rerun()
