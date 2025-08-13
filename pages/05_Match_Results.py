import streamlit as st
import json
import os
import pandas as pd
import time

# --- Session check: block page if not logged in ---
if 'user_logged_in' not in st.session_state or not st.session_state['user_logged_in']:
    st.warning('You must be logged in to access this page.')
    st.stop()

DATA_FILE = "tournament_data.json"
RESULTS_KEY = "results"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    if RESULTS_KEY not in data:
        data[RESULTS_KEY] = []
    data.setdefault("teams", {})
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

st.set_page_config(page_title="🏆 Match Results")
st.title("🏆 Match Results")

data = load_data()

# --- Sample Data Generation if no results ---
def generate_sample_results(data):
    # Use teams from data, or create 6 groups x 4 teams if none
    if not data.get("teams"):
        sample_groups = ['A', 'B', 'C', 'D', 'E', 'F']
        data["teams"] = {g: [f"{g}{i+1}" for i in range(4)] for g in sample_groups}
    import random
    results = []
    for teams in data["teams"].values():
        for t in teams:
            points = random.randint(0, 3)
            nrr = round(random.uniform(-6.0, 6.0), 3)
            results.append({"Team Name": t, "Points": points, "NRR": nrr})
    data[RESULTS_KEY] = results
    save_data(data)
    return data

# If no results, prompt to generate sample data
def is_empty_results(data):
    return not data.get(RESULTS_KEY)

if is_empty_results(data):
    st.info("No match results found. You can generate sample data to see how the app works.")
    if st.button("Generate Sample Results", type="primary"):
        data = generate_sample_results(data)
        st.success("Sample results generated!")
        st.rerun()

# Collect all unique team names from all groups (preserve order and duplicates)
all_teams = []
seen = set()
for teams in data.get("teams", {}).values():
    for t in teams:
        t_clean = t.strip()
        if t_clean and t_clean.lower() not in seen:
            all_teams.append(t_clean)
            seen.add(t_clean.lower())

# Only show teams without results in the add form
existing_result_teams = {r["Team Name"].strip().lower() for r in data[RESULTS_KEY]}
available_teams = [t for t in all_teams if t.strip().lower() not in existing_result_teams]

with st.form("add_result_form"):
    st.subheader("Add Result")
    team_name = st.selectbox(
        "Team Name",
        available_teams,
        index=0 if available_teams else None,
        key="team_name_select"
    ) if available_teams else st.text_input("Team Name")
    points = st.number_input("Points", min_value=0, step=1, key="add_points")
    nrr = st.number_input("Net Run Rate (NRR)", format="%.3f", step=0.001, key="add_nrr")
    submitted = st.form_submit_button("Add Result")

    if submitted and team_name and str(team_name).strip():
        data[RESULTS_KEY].append({"Team Name": str(team_name).strip(), "Points": points, "NRR": nrr})
        save_data(data)
        st.success(f"Result saved for {team_name}")
        st.rerun()

# Display results as editable table
# Ensure all teams are shown in the table, even if no result yet
results_dict = {r["Team Name"].strip(): r for r in data[RESULTS_KEY]}
table_rows = []
for team in all_teams:
    entry = results_dict.get(team.strip(), {"Team Name": team.strip(), "Points": 0, "NRR": 0.0})
    # Ensure keys exist for every row
    entry = {
        "Team Name": entry.get("Team Name", team.strip()),
        "Points": entry.get("Points", 0),
        "NRR": entry.get("NRR", 0.0)
    }
    table_rows.append(entry)
df = pd.DataFrame(table_rows)
# Ensure columns exist and fill missing values
if 'Points' not in df.columns:
    df['Points'] = 0
else:
    df['Points'] = df['Points'].fillna(0)
if 'NRR' not in df.columns:
    df['NRR'] = 0.0
else:
    df['NRR'] = df['NRR'].fillna(0.0)
df = df.sort_values(["Points", "NRR"], ascending=[False, False]).reset_index(drop=True)
df.index = df.index + 1  # Sequence from 1
st.markdown("### Results Table (Click to Edit)")
for idx, row in df.iterrows():
    with st.expander(f"{row['Team Name']}"):
        points = st.number_input(f"Points for {row['Team Name']}", min_value=0, step=1, value=int(row['Points']), key=f"edit_points_{row['Team Name']}")
        nrr = st.number_input(f"NRR for {row['Team Name']}", format="%.3f", step=0.001, value=float(row['NRR']), key=f"edit_nrr_{row['Team Name']}")
        if st.button(f"Update {row['Team Name']}", key=f"update_{row['Team Name']}"):
            # Update in data
            found = False
            for result in data[RESULTS_KEY]:
                if result["Team Name"].lower() == row["Team Name"].lower():
                    result["Points"] = points
                    result["NRR"] = nrr
                    found = True
                    break
            if not found:
                data[RESULTS_KEY].append({"Team Name": row["Team Name"], "Points": points, "NRR": nrr})
            save_data(data)
            st.success(f"Updated result for {row['Team Name']}")
            st.rerun()
st.dataframe(df)
