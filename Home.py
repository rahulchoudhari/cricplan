import streamlit as st
from pathlib import Path
import json
import hashlib
import os
import pandas as pd
import time

USERS_FILE = "users.json"
DATA_FILE = "tournament_data.json"

# --- Hero Banner ---
st.set_page_config(page_title="🏏 Cricket Planner Login")
st.markdown("""
<div style='background: linear-gradient(90deg, #43cea2 0%, #185a9d 100%); padding:2em 0 1em 0; border-radius: 0 0 24px 24px; text-align:center;'>
    <img src='https://img.icons8.com/color/96/000000/cricket.png' width='96'/>
    <h1 style='color:#fff; margin-bottom:0;'>Cricket Planner</h1>
    <h3 style='color:#e0f7fa; margin-top:0;'>Plan. Play. Win.</h3>
    <p style='color:#e0f2f1; font-size:1.2em;'>The ultimate platform for organizing, managing, and enjoying cricket tournaments.</p>
</div>
""", unsafe_allow_html=True)

# --- Packages Section ---
st.markdown("""
<div style='margin:2em 0 1em 0;'>
    <h2 style='color:#1B5E20; text-align:center;'>Choose Your Package</h2>
    <div style='display:flex; gap:2em; flex-wrap:wrap; justify-content:center;'>
        <div style='flex:1; min-width:220px; max-width:300px; background:#fff; border-radius:8px; border:2px solid #43cea2; padding:1.5em; margin:1em;'>
            <h3 style='color:#1B5E20;'>Basic</h3>
            <p style='font-size:1.1em;'><b>$39.99</b> per tournament</p>
            <ul>
                <li>✔️ Create tournament schedule</li>
            </ul>
        </div>
        <div style='flex:1; min-width:220px; max-width:300px; background:#fff; border-radius:8px; border:2px solid #1976d2; padding:1.5em; margin:1em;'>
            <h3 style='color:#1976d2;'>Basic Plus</h3>
            <p style='font-size:1.1em;'><b>$69.99</b> per tournament</p>
            <ul>
                <li>✔️ All Basic features</li>
                <li>✔️ Print-ready schedule (PDF/Excel)</li>
            </ul>
        </div>
        <div style='flex:1; min-width:220px; max-width:300px; background:#fff; border-radius:8px; border:2px solid #c62828; padding:1.5em; margin:1em;'>
            <h3 style='color:#c62828;'>Premium</h3>
            <p style='font-size:1.1em;'><b>$399</b> per tournament</p>
            <ul>
                <li>✔️ All Basic Plus features</li>
                <li>✔️ End-to-end execution</li>
                <li>✔️ Vendor confirmation</li>
                <li>✔️ Sponsor coordination</li>
                <li>✔️ Banner management</li>
                <li>✔️ Dedicated support</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Features Section ---
st.markdown("""
<div style='margin:2em 0 1em 0;'>
    <h2 style='color:#185a9d; text-align:center;'>Why Choose Cricket Planner?</h2>
    <div style='display:flex; gap:2em; flex-wrap:wrap; justify-content:center;'>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <img src='https://img.icons8.com/color/48/000000/organization.png'/>
            <p>Easy Team & Group Management</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <img src='https://img.icons8.com/color/48/000000/calendar.png'/>
            <p>Automated Scheduling</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <img src='https://img.icons8.com/color/48/000000/checked-checkbox.png'/>
            <p>Match Checklists</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <img src='https://img.icons8.com/color/48/000000/gallery.png'/>
            <p>Photo Gallery & Comments</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <img src='https://img.icons8.com/color/48/000000/lock-2.png'/>
            <p>Role-Based Secure Access</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <img src='https://img.icons8.com/color/48/000000/medical-doctor.png'/>
            <p>Medical Waiver Management</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- How It Works (Workflow) ---
st.markdown("""
<div style='margin:2em 0 1em 0;'>
    <h2 style='color:#388E3C; text-align:center;'>How It Works: Tournament Workflow</h2>
    <div style='display:flex; gap:2em; flex-wrap:wrap; justify-content:center;'>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>1</div>
            <p><b>Register/Login</b><br>Sign up or log in to your account to access all features.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>2</div>
            <p><b>Create Teams & Groups</b><br>Add teams and organize them into groups for the tournament.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>3</div>
            <p><b>Generate Schedule</b><br>Automatically create round-robin or knockout fixtures.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>4</div>
            <p><b>Assign Umpires & Grounds</b><br>Allocate umpires and grounds for each match.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>5</div>
            <p><b>Collect Medical Waivers</b><br>Share and collect medical waiver forms from all teams.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>6</div>
            <p><b>Track Results & Points</b><br>Enter match results, update points, and view standings.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>7</div>
            <p><b>Share Gallery & Highlights</b><br>Upload photos, add comments, and celebrate moments.</p>
        </div>
        <div style='flex:1; min-width:180px; max-width:220px; text-align:center;'>
            <div style='font-size:2em; color:#43cea2;'>8</div>
            <p><b>Publish Fixtures & End Tournament</b><br>Share final fixtures, results, and wrap up the event.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Login/Registration Section ---
if 'user_logged_in' not in st.session_state:
    st.session_state['user_logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'login_time' not in st.session_state:
    st.session_state['login_time'] = None

st.markdown("---")

if not st.session_state['user_logged_in']:
    st.markdown("<div style='max-width:400px; margin:auto; background:#f5f5f5; padding:2em; border-radius:12px; box-shadow:0 2px 8px #e0e0e0;'>", unsafe_allow_html=True)
    st.markdown('## User Registration / Login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    role = st.selectbox('Role', ['Player', 'Team Manager', 'Planner', 'Admin'])
    register = st.checkbox('Register as new user')
    # ...existing code for loading users and login/register logic...
    users = {}
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, "r") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = {}
    if st.button('Register/Login'):
        if username and password and role:
            if register:
                if username in users:
                    st.error('Username already exists.')
                else:
                    users[username] = {
                        'password': hashlib.sha256(password.encode()).hexdigest(),
                        'role': role
                    }
                    with open(USERS_FILE, "w") as f:
                        json.dump(users, f, indent=4)
                    st.success('Registration successful! Please login.')
                    st.rerun()
            else:
                if username in users and users[username]['password'] == hashlib.sha256(password.encode()).hexdigest():
                    st.session_state['user_logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['user_role'] = users[username]['role']
                    st.session_state['login_time'] = time.time()
                    st.success(f'Welcome, {username}! Role: {users[username]["role"]}')
                    st.rerun()
                else:
                    st.error('Invalid username or password.')
        else:
            st.error('Please enter username, password, and select a role.')
    st.markdown('<div style="text-align:right; font-size:0.9em; color:#888;">Forgot password? Contact your admin.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- Session Expiry and Logout ---
if st.session_state['user_logged_in']:
    if st.session_state.get('login_time') and (time.time() - st.session_state['login_time'] > 300):
        st.session_state['user_logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['username'] = None
        st.session_state['login_time'] = None
        st.warning('Session expired. Please login again.')
        st.rerun()
    if st.sidebar.button('Logout'):
        st.session_state['user_logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['username'] = None
        st.session_state['login_time'] = None
        st.success('Logged out successfully.')
        st.rerun()

# --- Dashboard (after login) ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"teams": {}, "schedule": {}}

if st.session_state['user_logged_in']:
    st.title("🏏 Cricket Tournament Planner")
    st.subheader("Welcome to your tournament dashboard")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Teams", sum(len(g) for g in data["teams"].values()))
    with col2:
        st.metric("Total Fixtures", sum(len(f) for f in data["schedule"].values()))

    if st.button("Clear All Fixtures (Reset Schedule)", type="primary"):
        data["schedule"] = {}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        st.success("All fixtures have been cleared.")
        st.rerun()

    st.markdown("---")
    st.markdown(f"""
        <h1 style='color:#1B5E20;'>🏏 Welcome {st.session_state.get('username', '')}!</h1>
        <h3 style='color:#388E3C;'>Go to the Schedule & Tournament App from the sidebar.</h3>
        """, unsafe_allow_html=True)
    if st.sidebar.button('End Tournament'):
        st.switch_page('pages/03_End_Tournament.py')
    st.sidebar.info("For best experience, use the sidebar navigation and do not open pages in a new tab.")