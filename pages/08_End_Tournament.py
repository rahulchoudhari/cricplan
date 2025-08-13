import streamlit as st
import os
import json
from pathlib import Path

DATA_FILE = "tournament_data.json"
ARCHIVE_DIR = "tournament_archive"

st.set_page_config(page_title="🏁 End Tournament")

st.title("🏁 End Tournament")
st.markdown("Use this page to archive the current tournament and clear all cached data. You can still view past tournaments from the archive.")

# Ensure archive directory exists
Path(ARCHIVE_DIR).mkdir(exist_ok=True)

# Load current data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"teams": {}, "schedule": {}}

# List all archived tournaments
archived_files = sorted(os.listdir(ARCHIVE_DIR), reverse=True)
archived_tournaments = [f for f in archived_files if f.endswith(".json")]

# Archive current tournament
if st.button("End & Archive Current Tournament"):
    if data["teams"] or data["schedule"]:
        archive_name = st.text_input("Enter archive name (e.g. 2025_Summer_Cup):", value="")
        if archive_name:
            archive_path = os.path.join(ARCHIVE_DIR, f"{archive_name}.json")
            with open(archive_path, "w") as f:
                json.dump(data, f, indent=4)
            # Clear current data
            with open(DATA_FILE, "w") as f:
                json.dump({"teams": {}, "schedule": {}}, f, indent=4)
            st.success(f"Tournament archived as {archive_name}. All cached data cleared.")
            st.rerun()
        else:
            st.warning("Please enter an archive name before archiving.")
    else:
        st.warning("No tournament data to archive.")

# View archived tournaments
st.markdown("---")
st.header("View Archived Tournaments")
if archived_tournaments:
    selected_archive = st.selectbox("Select an archived tournament to view", archived_tournaments)
    if selected_archive:
        with open(os.path.join(ARCHIVE_DIR, selected_archive), "r") as f:
            archive_data = json.load(f)
        st.subheader(f"Archive: {selected_archive}")
        st.write("Teams:")
        st.json(archive_data.get("teams", {}))
        st.write("Schedule:")
        st.json(archive_data.get("schedule", {}))
else:
    st.info("No archived tournaments found.")
