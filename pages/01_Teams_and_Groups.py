import streamlit as st
import json
import os
import time

# --- Session check: block page if not logged in ---
if 'user_logged_in' not in st.session_state or not st.session_state['user_logged_in']:
    st.warning('You must be logged in to access this page.')
    st.stop()

st.set_page_config(page_title="Teams and Groups")
st.title("Teams and Groups")

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
    if "teams" not in data:
        data["teams"] = {}
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# --- UI for Adding Teams to Groups ---
st.subheader("Add Team(s) to Group")
group = st.selectbox("Select Group", [chr(i) for i in range(65, 91)])  # Groups A-Z
team_names = st.text_input("Team Name(s) (comma separated)")

# Get all existing team names (across all groups)
existing_teams = set()
for teams in data["teams"].values():
    existing_teams.update(teams)

if st.button("Add Team(s)"):
    # Split and clean team names
    new_teams = [t.strip() for t in team_names.split(",") if t.strip()]
    errors = []
    added = []
    group_teams = data["teams"].get(group, [])
    for team_name in new_teams:
        if not team_name:
            continue
        elif team_name in existing_teams or team_name in added:
            errors.append(f"'{team_name}' is not unique.")
        elif len(group_teams) + len(added) >= 4:
            errors.append(f"Group {group} can have max 4 teams. Only some teams were added.")
            break
        else:
            added.append(team_name)
    if added:
        group_teams.extend(added)
        data["teams"][group] = group_teams
        save_data(data)
        st.success(f"Added to Group {group}: {', '.join(added)}")
        st.rerun()
    if errors:
        for err in errors:
            st.error(err)

# --- Display Groups and Teams ---
st.markdown("### Groups and Teams")
if data["teams"]:
    for group, teams in sorted(data["teams"].items()):
        st.markdown(f"**Group {group}:**")
        if teams:
            st.table({"Team #": list(range(1, len(teams)+1)), "Team Name": teams})
        else:
            st.info("No teams yet.")
    if st.button("Clear All Teams", type="primary"):
        data["teams"] = {}
        save_data(data)
        st.success("All teams/groups have been cleared.")
        st.rerun()
else:
    st.info("No teams added yet. Use the form above to add teams to groups.")
    if st.button("Create Sample Data to See How App Works", type="primary"):
        # Inject sample data: 6 groups, 4 teams each
        sample_groups = ['A', 'B', 'C', 'D', 'E', 'F']
        sample_teams = {g: [f"{g}{i+1}" for i in range(4)] for g in sample_groups}
        data["teams"] = sample_teams
        save_data(data)
        st.success("Sample data created! Reloading...")
        st.rerun()

# --- Historical Data Section ---
if "historical_teams" in data and data["historical_teams"]:
    with st.expander("Show Historical Teams/Groups Data"):
        for year, teams_by_group in sorted(data["historical_teams"].items(), reverse=True):
            st.markdown(f"#### Year: {year}")
            for group, teams in sorted(teams_by_group.items()):
                st.markdown(f"- **Group {group}:** {', '.join(teams) if teams else 'No teams'}")
else:
    st.caption("No historical teams/groups data found.")

