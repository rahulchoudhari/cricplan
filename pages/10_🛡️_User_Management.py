# pages/10_🛡️_User_Management.py
import streamlit as st

import auth
import db
import sidebar
import ui

ui.inject_global_css()
sidebar.render()
ui.guard_login()

if st.session_state.get('role') != "Admin":
    st.warning("This page is for Admins only.", icon="🔒")
    st.stop()

ui.page_header("User Management", "Create, approve, change roles for, or remove user accounts.", "🛡️")

ROLES = ["Player", "Team Captain", "Tournament Organizer", "Admin"]
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
            if u.get('linked_owner'):
                st.caption(f"Joined: {u['linked_tournament']} (by {u['linked_owner']})")
        with c2:
            new_role = st.selectbox(
                "Role", ROLES, index=ROLES.index(u['role']) if u['role'] in ROLES else 0,
                key=f"role_{u['username']}", label_visibility="collapsed", disabled=is_self,
            )
            if not is_self and new_role != u['role']:
                if st.button("Save role", key=f"save_role_{u['username']}", use_container_width=True):
                    db.update_user_role(u['username'], new_role)
                    st.rerun()
        with c3:
            if u['approved']:
                st.markdown('<span class="cric-pill-approved">Approved</span>', unsafe_allow_html=True)
                if not is_self and st.button("Revoke", key=f"revoke_{u['username']}", use_container_width=True):
                    db.set_user_approved(u['username'], False)
                    st.rerun()
            else:
                st.markdown('<span class="cric-pill-pending">Pending</span>', unsafe_allow_html=True)
                if st.button("Approve", key=f"approve_{u['username']}", use_container_width=True, type="primary"):
                    db.set_user_approved(u['username'], True)
                    st.rerun()
        with c4:
            if is_self:
                st.caption("You")
            elif st.button("🗑️ Delete", key=f"delete_{u['username']}", use_container_width=True):
                db.delete_user(u['username'])
                st.rerun()

st.markdown("---")
st.subheader("Create a new account")
st.caption("Use this to set up an account directly, skipping self-registration and approval.")

tournaments = db.list_tournaments()
tournament_options = ["(none)"] + [f"{tname} — by {owner}" for owner, tname in tournaments]

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

    if st.form_submit_button("Create Account", type="primary", use_container_width=True):
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
            linked_owner = linked_tournament = None
            if picked_tournament != "(none)":
                idx = tournament_options.index(picked_tournament) - 1
                linked_owner, linked_tournament = tournaments[idx]
            db.create_user(
                username=new_username, email=new_email,
                password_hash=auth.hash_password(new_password),
                role=new_role, approved=new_approved,
                linked_owner=linked_owner, linked_tournament=linked_tournament,
            )
            st.success(f"Account '{new_username}' created.")
            st.rerun()
