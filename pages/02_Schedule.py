import streamlit as st
import json
import os
import time

# --- Session check: block page if not logged in ---
if 'user_logged_in' not in st.session_state or not st.session_state['user_logged_in']:
    st.warning('You must be logged in to access this page.')
    st.stop()

st.set_page_config(page_title="Schedule")
st.title("Schedule")

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
    if "schedule" not in data:
        data["schedule"] = {}
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# --- Generate and Display Schedule ---
st.markdown("### Group Stage Schedule")
if not data["teams"] or all(len(teams) < 2 for teams in data["teams"].values()):
    st.info("Not enough teams in groups to generate schedule. Add at least 2 teams per group.")
else:
    for group_idx, (group, teams) in enumerate(sorted(data["teams"].items())):
        if len(teams) < 2:
            continue
        ground_name = f"Ground {group_idx+1}"
        st.markdown(f"#### Group {group} ({ground_name})")
        # Generate round-robin matches for this group
        matches = []
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                matches.append({
                    "Team 1": teams[i],
                    "Team 2": teams[j],
                })
        # Load or initialize umpire assignments
        group_schedule = data["schedule"].get(group, [])
        if not group_schedule or len(group_schedule) != len(matches):
            # Initialize schedule with auto-selected umpire
            group_schedule = []
            for m in matches:
                non_playing_teams = [t for t in teams if t not in [m["Team 1"], m["Team 2"]]]
                auto_umpire = non_playing_teams[0] if non_playing_teams else ""
                group_schedule.append({"Team 1": m["Team 1"], "Team 2": m["Team 2"], "Umpire": auto_umpire})
            data["schedule"][group] = group_schedule
            save_data(data)
        # Calculate match start times (1 match at a time per ground)
        from datetime import datetime, timedelta
        start_time = datetime.strptime("07:30", "%H:%M")
        match_duration = timedelta(minutes=45)
        display_table = []
        for idx, m in enumerate(group_schedule):
            match_start = (start_time + idx * match_duration).strftime("%I:%M %p")
            row = {
                "Match #": idx+1,
                "Home": m["Team 1"],
                "Challenger": m["Team 2"],
                "Umpire": m["Umpire"],
                "Ground": m.get("Ground", ground_name),
                "Start Time": m.get("Start Time", match_start)
            }
            display_table.append(row)
        st.table(display_table)
        # Ask if user wants to make changes
        if st.checkbox(f"Do you want to make changes in schedule for Group {group}?", key=f"edit_{group}"):
            st.write("**Assign Umpires, Ground, and Start Time:**")
            updated = False
            # Get all teams in the tournament (across all groups)
            all_teams = set()
            for tlist in data["teams"].values():
                all_teams.update(tlist)
            for idx, match in enumerate(group_schedule):
                non_playing_teams = [t for t in all_teams if t not in [match["Team 1"], match["Team 2"]]]
                umpire = match.get("Umpire", "")
                ground = match.get("Ground", ground_name)
                start_time_val = match.get("Start Time", (start_time + idx * match_duration).strftime("%I:%M %p"))
                # If umpire is not set or not valid, auto-select from group, else from all teams
                if not umpire or umpire not in non_playing_teams:
                    group_neutrals = [t for t in teams if t not in [match["Team 1"], match["Team 2"]]]
                    if group_neutrals:
                        umpire = group_neutrals[0]
                    elif non_playing_teams:
                        umpire = sorted(non_playing_teams)[0]
                    else:
                        umpire = ""
                    group_schedule[idx]["Umpire"] = umpire
                    updated = True
                new_umpire = st.selectbox(
                    f"Umpire for {match['Team 1']} (Home) vs {match['Team 2']} (Challenger)",
                    options=["-- Select --"] + sorted(non_playing_teams),
                    index=(sorted(non_playing_teams).index(umpire)+1) if umpire in non_playing_teams else 0,
                    key=f"umpire_{group}_{idx}"
                )
                new_ground = st.text_input(
                    f"Ground for {match['Team 1']} (Home) vs {match['Team 2']} (Challenger)",
                    value=ground,
                    key=f"ground_{group}_{idx}"
                )
                new_start_time = st.text_input(
                    f"Start Time for {match['Team 1']} (Home) vs {match['Team 2']} (Challenger) (e.g. 07:30 AM)",
                    value=start_time_val,
                    key=f"starttime_{group}_{idx}"
                )
                if new_umpire != "-- Select --" and new_umpire != umpire:
                    group_schedule[idx]["Umpire"] = new_umpire
                    updated = True
                if new_ground != ground:
                    group_schedule[idx]["Ground"] = new_ground
                    updated = True
                if new_start_time != start_time_val:
                    group_schedule[idx]["Start Time"] = new_start_time
                    updated = True
            # Save schedule if any field was updated
            if updated:
                data["schedule"][group] = group_schedule
                save_data(data)
                st.success(f"Schedule updated for Group {group}.")
            # Show updated table again
            display_table = []
            for idx, m in enumerate(group_schedule):
                match_start = (start_time + idx * match_duration).strftime("%I:%M %p")
                row = {
                    "Match #": idx+1,
                    "Home": m["Team 1"],
                    "Challenger": m["Team 2"],
                    "Umpire": m["Umpire"],
                    "Ground": m.get("Ground", ground_name),
                    "Start Time": m.get("Start Time", match_start)
                }
                display_table.append(row)
            st.table(display_table)
    # Save schedule if not already present
    if data["schedule"] != {}:
        save_data(data)
