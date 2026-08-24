# pages/10_🛡️_User_Management.py
import streamlit as st

import auth
import db
import sidebar
import ui
from utils import load_tournament_state, clear_tournament_widget_cache, get_active_tournament_id

ui.inject_global_css()
sidebar.render()
ui.guard_login()

if st.session_state.get('role') != "Admin":
    st.warning("This page is for Admins only.", icon="🔒")
    st.stop()

ui.page_header("User Management", "Create, approve, change roles for, or remove user accounts.", "🛡️")

ROLES = ["Player", "Team Captain", "Manager", "Tournament Organizer", "Admin"]
me = st.session_state.username
users = db.list_all_users()

st.subheader(f"All Users ({len(users)})")
for u in users:
    is_self = u['username'] == me
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2.2, 1.8, 1.3, 1])
        with c1:
            st.markdown(f"**{ui.esc(u['username'])}**", unsafe_allow_html=True)
            st.caption(u['email'])
            if u.get('linked_tournament_name'):
                st.caption(f"Joined: {u['linked_tournament_name']}")
        with c2:
            new_role = st.selectbox(
                "Role", ROLES, index=ROLES.index(u['role']) if u['role'] in ROLES else 0,
                key=f"role_{u['username']}", label_visibility="collapsed", disabled=is_self,
            )
            if not is_self and new_role != u['role']:
                if st.button("Save role", key=f"save_role_{u['username']}", width='stretch'):
                    db.update_user_role(u['username'], new_role)
                    st.rerun()
        with c3:
            if u['approved']:
                st.markdown('<span class="cric-pill-approved">Approved</span>', unsafe_allow_html=True)
                if not is_self and st.button("Revoke", key=f"revoke_{u['username']}", width='stretch'):
                    db.set_user_approved(u['username'], False)
                    st.rerun()
            else:
                st.markdown('<span class="cric-pill-pending">Pending</span>', unsafe_allow_html=True)
                if st.button("Approve", key=f"approve_{u['username']}", width='stretch', type="primary"):
                    db.set_user_approved(u['username'], True)
                    st.rerun()
        with c4:
            if is_self:
                st.caption("You")
            elif st.button("🗑️ Delete", key=f"delete_{u['username']}", width='stretch'):
                db.delete_user(u['username'])
                st.rerun()

        with st.expander("🔑 Reset password"):
            with st.form(f"reset_pw_{u['username']}", clear_on_submit=True):
                new_pw = st.text_input(
                    "New password (min 8 chars, letter & number)", type="password",
                    key=f"new_pw_{u['username']}",
                )
                if st.form_submit_button("Set Password", width='stretch'):
                    if not auth.is_valid_password(new_pw):
                        st.warning("Password must be at least 8 characters and include a letter and a number.")
                    else:
                        db.set_password(u['username'], auth.hash_password(new_pw))
                        st.success(f"Password updated for '{u['username']}'.")

st.markdown("---")
st.subheader("Tournaments")
st.caption("As Admin, you can delete any organizer's tournament — organizers can only delete their own, from their Tournament Setup page.")
tournaments = db.list_tournaments()
if tournaments:
    for t in tournaments:
        team_count = len(db.get_teams_for_tournament(t['id']))
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2.5, 1.5])
            with c1:
                st.markdown(f"**{ui.esc(t['tournament_name'])}**", unsafe_allow_html=True)
                st.caption(f"Organized by {t['owner_username']} · {team_count} team(s)")
            with c2:
                confirm = st.text_input(
                    f'Type "{t["tournament_name"]}" to confirm', key=f"delete_tourney_confirm_{t['id']}",
                    label_visibility="collapsed", placeholder=f'Type "{t["tournament_name"]}" to confirm',
                )
            with c3:
                if st.button("🗑️ Delete", key=f"delete_tourney_{t['id']}", width='stretch', disabled=(confirm != t['tournament_name'])):
                    try:
                        db.delete_tournament(t['id'])
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
                    else:
                        if t['id'] == get_active_tournament_id():
                            remaining = [x for x in db.get_tournaments_for_owner(me) if x['id'] != t['id']]
                            st.session_state.active_tournament_id = remaining[0]['id'] if remaining else None
                            st.session_state.tournament_name = "New Tournament"
                            load_tournament_state()
                            clear_tournament_widget_cache()
                        st.success(f"Tournament '{t['tournament_name']}' deleted.")
                        st.rerun()
else:
    ui.empty_state("No tournaments exist yet.")

st.markdown("---")
st.subheader("Create a new account")
st.caption("Use this to set up an account directly, skipping self-registration and approval.")

tournament_options = ["(none)"] + [t['tournament_name'] for t in tournaments]

with st.form("admin_create_user", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        new_username = st.text_input("Username", help="3-20 characters: letters, numbers, _ or -")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password (min 8 chars, letter & number)", type="password")
    with c2:
        new_role = st.selectbox("Role", ROLES, key="admin_new_role")
        new_approved = st.checkbox("Approve immediately", value=True)
        picked_tournament = st.selectbox(
            "Link to tournament (for Player / Team Captain roles)", tournament_options,
        )

    if st.form_submit_button("Create Account", type="primary", width='stretch'):
        new_username = new_username.strip()
        if not all([new_username, new_email, new_password, new_role]):
            st.warning("All fields are required.")
        elif not auth.is_valid_username(new_username):
            st.warning("Username must be 3-20 characters: letters, numbers, underscore or hyphen only.")
        elif not auth.is_valid_email(new_email):
            st.warning("Please enter a valid email address.")
        elif db.get_user(new_username):
            st.error("Username already exists.")
        elif not auth.is_valid_password(new_password):
            st.warning("Password must be at least 8 characters and include a letter and a number.")
        else:
            linked_id = None
            if picked_tournament != "(none)":
                linked_id = tournaments[tournament_options.index(picked_tournament) - 1]['id']
            db.create_user(
                username=new_username, email=new_email,
                password_hash=auth.hash_password(new_password),
                role=new_role, approved=new_approved,
                linked_tournament_id=linked_id,
            )
            st.success(f"Account '{new_username}' created.")
            st.rerun()
