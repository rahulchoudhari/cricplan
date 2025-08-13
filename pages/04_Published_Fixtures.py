import streamlit as st
import json
import os
import time

# --- Session check: block page if not logged in ---
if 'user_logged_in' not in st.session_state or not st.session_state['user_logged_in']:
    st.warning('You must be logged in to access this page.')
    st.stop()

st.set_page_config(page_title="Published Fixtures")
st.title("Published Fixtures")

DATA_FILE = "tournament_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    if "schedule" not in data:
        data["schedule"] = {}
    return data

data = load_data()

st.markdown("## 📅 Tournament Fixtures")
if not data["schedule"] or all(len(matches) == 0 for matches in data["schedule"].values()):
    st.info("No fixtures have been scheduled yet. Please create the schedule first.")
else:
    for group_idx, (group, matches) in enumerate(sorted(data["schedule"].items())):
        if not matches:
            continue
        st.markdown(f"### Group {group}  ")
        # Presentable table with all columns
        display_table = []
        for m in matches:
            home = m.get("Home", m.get("Team 1", ""))
            challenger = m.get("Challenger", m.get("Team 2", ""))
            row = {
                "Match #": m.get("Match #", None),
                "Home": home,
                "Challenger": challenger,
                "Umpire": m.get("Umpire", ""),
                "Ground": m.get("Ground", f"Ground {group_idx+1}"),
                "Start Time": m.get("Start Time", "")
            }
            display_table.append(row)
        # Add match numbers if not present
        for idx, row in enumerate(display_table):
            row["Match #"] = idx+1
        st.table(display_table)
