# sidebar.py
"""Shared account sidebar (login/register/logout), rendered on every page."""
import streamlit as st

import auth
import db
import ui
from utils import initialize_state_base, load_tournament_state, is_organizer


def render() -> None:
    initialize_state_base()
    db.init_db()

    with st.sidebar:
        logo = ui.logo_data_uri()
        if logo:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">
                    <img src="{logo}" style="width:40px;height:40px;border-radius:50%;">
                    <span style="font-weight:800;font-size:1.05rem;">Cricket Scheduler Pro</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🏆 Cricket Scheduler Pro")

        if not st.session_state.user_logged_in:
            login_tab, register_tab = st.tabs(["Login", "Register"])

            with login_tab:
                with st.form("login_form"):
                    login_username = st.text_input("Username")
                    login_password = st.text_input("Password", type="password")
                    if st.form_submit_button("Login", use_container_width=True, type="primary"):
                        user = db.get_user(login_username.strip())
                        if user and auth.verify_password(login_password, user['password_hash']):
                            if not user.get('approved'):
                                st.warning("Your account is pending organizer approval.")
                            else:
                                st.session_state.user_logged_in = True
                                st.session_state.username = user['username']
                                st.session_state.role = user['role']
                                st.session_state.linked_owner = user.get('linked_owner')
                                st.session_state.linked_tournament = user.get('linked_tournament')
                                load_tournament_state()
                                st.rerun()
                        else:
                            st.error("Invalid username or password.")

            with register_tab:
                tournaments = db.list_tournaments()
                reg_role = st.selectbox("Role", ["Player", "Team Captain", "Tournament Organizer", "Admin"], key="reg_role")
                reg_tournament_choice = None
                needs_tournament = reg_role in ("Player", "Team Captain")
                if needs_tournament:
                    if tournaments:
                        options = [f"{tname} — by {owner}" for owner, tname in tournaments]
                        picked = st.selectbox("Which tournament are you joining?", options, key="reg_tournament")
                        reg_tournament_choice = tournaments[options.index(picked)]
                    else:
                        st.info("No tournaments exist yet. Ask your organizer to set one up first, then register.")

                with st.form("register_form"):
                    reg_username = st.text_input("Username", help="3-20 characters: letters, numbers, _ or -")
                    reg_email = st.text_input("Email")
                    reg_password = st.text_input("Password (min 8 chars, letter & number)", type="password")

                    if st.form_submit_button("Register", use_container_width=True, type="primary"):
                        reg_username = reg_username.strip()
                        if not all([reg_username, reg_email, reg_password, reg_role]):
                            st.warning("All fields are required.")
                        elif not auth.is_valid_username(reg_username):
                            st.warning("Username must be 3-20 characters: letters, numbers, underscore or hyphen only.")
                        elif not auth.is_valid_email(reg_email):
                            st.warning("Please enter a valid email address.")
                        elif db.get_user(reg_username):
                            st.error("Username already exists.")
                        elif not auth.is_valid_password(reg_password):
                            st.warning("Password must be at least 8 characters and include a letter and a number.")
                        elif needs_tournament and not reg_tournament_choice:
                            st.warning("Select a tournament to join, or ask your organizer to create one first.")
                        else:
                            is_bootstrap = db.count_users() == 0
                            approved = is_bootstrap or reg_role == "Player"
                            linked_owner, linked_tournament = (reg_tournament_choice if reg_tournament_choice else (None, None))
                            db.create_user(
                                username=reg_username, email=reg_email,
                                password_hash=auth.hash_password(reg_password),
                                role=reg_role, approved=approved,
                                linked_owner=linked_owner, linked_tournament=linked_tournament,
                            )
                            if is_bootstrap:
                                st.success("You're the first user — your account is approved automatically. Please log in.")
                            elif approved:
                                st.success("Registration successful! Please log in.")
                            else:
                                st.success("Registration submitted. An organizer must approve your account before you can log in.")

        else:  # Logged-in view
            st.markdown(f"**{ui.esc(st.session_state.username)}**", unsafe_allow_html=True)
            st.markdown(ui.role_badge(st.session_state.role), unsafe_allow_html=True)
            st.markdown("")

            if is_organizer():
                pending_users = db.list_pending_users()
                if pending_users:
                    with st.expander(f"Pending approvals ({len(pending_users)})"):
                        for u in pending_users:
                            st.caption(f"{u['username']} · {u['role']}")
                            if st.button(f"Approve '{u['username']}'", key=f"approve_{u['username']}", use_container_width=True):
                                db.approve_user(u['username'])
                                st.rerun()

            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                st.session_state.clear()
                initialize_state_base()
                st.rerun()
