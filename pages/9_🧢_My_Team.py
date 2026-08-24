# pages/9_🧢_My_Team.py
import streamlit as st

import db
import sidebar
import ui

ui.inject_global_css()
sidebar.render()
ui.guard_login()

ui.page_header("My Team", "Register your team roster for the tournament you joined.", "🧢")

if st.session_state.get('role') != "Team Captain":
    st.info("Only users registered as **Team Captain** can register a team here.")
    st.stop()

owner = st.session_state.get('linked_owner')
tname = st.session_state.get('tournament_name')
if not owner or not tname:
    st.warning("Your account isn't linked to a tournament. Please contact your organizer.")
    st.stop()

st.caption(f"Registering for **{ui.esc(tname)}**, organized by **{ui.esc(owner)}**")

my_teams = db.get_teams_for_captain(st.session_state.username)

if my_teams:
    for t in my_teams:
        with st.container(border=True):
            status = ui.esc("Approved ✅") if t['approved'] else ui.esc("Pending organizer approval ⏳")
            st.markdown(f"### {ui.esc(t['team_name'])}", unsafe_allow_html=True)
            st.markdown(
                f'<span class="{"cric-pill-approved" if t["approved"] else "cric-pill-pending"}">{status}</span>',
                unsafe_allow_html=True,
            )
            if t.get('players'):
                st.markdown("**Players:** " + ", ".join(ui.esc(p) for p in t['players']))
            if t.get('contact_email') or t.get('contact_phone'):
                st.caption(f"Contact: {ui.esc(t.get('contact_email') or '')} {ui.esc(t.get('contact_phone') or '')}".strip())
    st.info("Need changes? Ask your tournament organizer to update or remove your registration.")
else:
    st.markdown("You haven't registered a team yet.")
    with st.form("register_team_form"):
        team_name = st.text_input("Team Name")
        contact_email = st.text_input("Contact Email")
        contact_phone = st.text_input("Contact Phone")
        players_raw = st.text_area("Players (one per line)", height=150)
        submitted = st.form_submit_button("Register Team", type="primary", use_container_width=True)
        if submitted:
            players = [p.strip() for p in players_raw.splitlines() if p.strip()]
            if not team_name.strip():
                st.warning("Team name is required.")
            elif not players:
                st.warning("Add at least one player.")
            else:
                existing = {t['team_name'] for t in db.get_teams_for_owner(owner)}
                if team_name.strip() in existing:
                    st.error("A team with this name is already registered for this tournament.")
                else:
                    db.create_team(
                        team_name=team_name.strip(), captain_username=st.session_state.username,
                        owner_username=owner, tournament_name=tname,
                        contact_email=contact_email.strip(), contact_phone=contact_phone.strip(),
                        players=players,
                    )
                    st.success("Team registered! It will appear in the tournament once your organizer approves it.")
                    st.rerun()
