# Home.py
import streamlit as st
import hashlib
from pathlib import Path
from utils import initialize_state_base, load_data, save_data, load_tournament_state, is_organizer
import re

st.set_page_config(page_title="Cricket Scheduler Pro", page_icon="🏆", layout="wide")
initialize_state_base() # Initializes user DB and login status

# --- Sidebar: User Management & Navigation ---
with st.sidebar:
    st.title("User Account")

    # --- Login/Registration Forms ---
    if not st.session_state.user_logged_in:
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            with st.form("login_form"):
                login_username = st.text_input("Username"); login_password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    user = st.session_state.user_db.get(login_username)
                    if user and user['password_hash'] == hashlib.sha256(login_password.encode()).hexdigest():
                        if not user.get('approved', False):
                            st.warning("Account pending approval.")
                        else:
                            st.session_state.user_logged_in = True
                            st.session_state.username = login_username
                            st.session_state.role = user['role']
                            load_tournament_state() # Load this user's data
                            st.rerun()
                    else:
                        st.error("Invalid username or password.")
        with register_tab:
            with st.form("register_form"):
                reg_username=st.text_input("Username"); reg_email=st.text_input("Email")
                reg_password=st.text_input("Password (min 8 chars, letter & num)", type="password")
                reg_role=st.selectbox("Role", ["Player", "Team Captain", "Tournament Organizer", "Admin"])
                if st.form_submit_button("Register", use_container_width=True):
                    if not all([reg_username, reg_email, reg_password, reg_role]): st.warning("All fields required.")
                    elif reg_username in st.session_state.user_db: st.error("Username already exists.")
                    elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', reg_password): st.warning("Password too weak.")
                    else:
                        st.session_state.user_db[reg_username] = {
                            'email': reg_email, 'role': reg_role, 
                            'approved': reg_role in ["Admin", "Tournament Organizer"],
                            'password_hash': hashlib.sha256(reg_password.encode()).hexdigest()
                        }
                        save_data(st.session_state.user_db, Path("users.json"))
                        st.success("Registration successful! Please login.")
    else: # Logged-in view
        st.markdown(f"Welcome, **{st.session_state.username}**!"); st.caption(f"Role: {st.session_state.role}")
        pending_users = [u for u, d in st.session_state.user_db.items() if not d.get('approved')]
        if is_organizer() and pending_users:
            with st.expander("Pending User Approvals"):
                for user in pending_users:
                    if st.button(f"Approve '{user}'", key=f"approve_{user}"):
                        st.session_state.user_db[user]['approved'] = True
                        save_data(st.session_state.user_db, Path("users.json"))
                        st.rerun()
        if st.button("Logout", use_container_width=True):
            for key in st.session_state.keys():
                if key != 'app_init' and key != 'user_db':
                    del st.session_state[key]
            initialize_state_base()
            st.rerun()

# --- Main Page Content ---
st.title(f"🏆 {st.session_state.get('tournament_name', 'Cricket Scheduler Pro')} 🏆")
st.markdown("---")

if st.session_state.user_logged_in:
    st.header("Welcome to your Tournament Dashboard")
    st.info("Use the navigation panel on the left to manage your tournament.")
    
    # Display a summary if tournament is set up
    if st.session_state.get('teams'):
        c1, c2, c3 = st.columns(3)
        c1.metric("Teams Registered", len(st.session_state.get('teams', [])))
        c2.metric("Groups Created", len(st.session_state.get('groups', {})))
        c3.metric("League Matches", len(st.session_state.get('schedule', [])))
else:
    st.header("All-in-one platform to manage your cricket tournament")
    st.markdown("Please **login** or **register** using the panel on the left to begin.")