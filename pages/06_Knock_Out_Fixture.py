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
KNOCKOUT_KEY = "knockout_fixtures"
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
    if KNOCKOUT_KEY not in data:
        data[KNOCKOUT_KEY] = []
    if RESULTS_KEY not in data:
        data[RESULTS_KEY] = []
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

st.set_page_config(page_title="🏆 Knock Out Fixture")
st.title("🏆 Knock Out Fixture")

data = load_data()

# Pull team names from Match Results, sorted by Points and NRR (ranking logic)
results = data.get(RESULTS_KEY, [])
if results:
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(["Points", "NRR"], ascending=[False, False]).reset_index(drop=True)
    knockout_teams = df_results["Team Name"].tolist()
else:
    knockout_teams = []

# --- Ranking Table Section ---
st.markdown("### Team Rankings (Points & NRR)")
if results and not df_results.empty:
    df_rank = df_results.copy()
    df_rank.index = df_rank.index + 1  # Start rank from 1
    df_rank = df_rank.rename_axis('Rank').reset_index()
    st.dataframe(df_rank[["Rank", "Team Name", "Points", "NRR"]])
else:
    st.info("No results available to display rankings.")

# --- Auto-generate Knockout Fixtures ---
if results and not df_results.empty and len(df_results) >= 14:
    st.markdown("### Knockout Fixtures (Auto-generated)")
    top14 = df_results.head(14).copy().reset_index(drop=True)
    pre_quarters = [
        (3, 14), (4, 13), (5, 12), (6, 11), (7, 10), (8, 9)
    ]
    preq_matches = []
    for i, (a, b) in enumerate(pre_quarters, 1):
        team1 = top14.iloc[a-1]["Team Name"]
        team2 = top14.iloc[b-1]["Team Name"]
        preq_matches.append({
            "Stage": "Pre-Quarter Final",
            "Match": i,
            "Teams": f"{team1} vs {team2}",
            "Ground": f"Ground {i}"
        })
    # --- Helper to get winners from previous round ---
    def get_stage_winners(result_key, num_matches):
        results = data.get(result_key, {})
        return [results.get(str(i+1), f"Winner PreQ{i+1}") for i in range(num_matches)]

    # Pre-Quarter Results
    # --- Improved knockout result entry: dropdown for each match, only teams in match, no duplicates ---
    def knockout_result_section(stage_name, matches, result_key):
        st.subheader(stage_name)
        knockout_results = data.get(result_key, {})
        if not isinstance(knockout_results, dict):
            knockout_results = {}
        # Show table with winner if available (table first)
        df = pd.DataFrame(matches)
        df['Winner'] = [knockout_results.get(str(m['Match']), "") for m in matches]
        st.dataframe(df[["Match", "Teams", "Ground", "Winner"]])
        # Track already selected winners to prevent duplicate selection
        already_selected = set(knockout_results.values())
        updated_results = {}
        st.markdown(f"#### Update {stage_name} Results")
        for match in matches:
            match_id = str(match['Match'])
            team1, team2 = match['Teams'].split(' vs ')
            options = [t for t in [team1, team2] if t not in already_selected or knockout_results.get(match_id) == t]
            winner = knockout_results.get(match_id, "")
            new_winner = st.selectbox(f"Winner of {match['Teams']} ({match['Ground']})", options=["-- Select --"] + options, index=(options.index(winner)+1) if winner in options else 0, key=f"{stage_name}_{match['Match']}")
            if new_winner != "-- Select --":
                updated_results[match_id] = new_winner
                already_selected.add(new_winner)
            elif winner:
                knockout_results.pop(match_id, None)
        if st.button(f"Save {stage_name} Results"):
            data[result_key] = updated_results
            save_data(data)
            st.success(f"{stage_name} results updated!")

    knockout_result_section("Pre-Quarter Finals", preq_matches, "preq_results")
    # Get PreQ winners for Quarters
    preq_winners = get_stage_winners("preq_results", 6)
    # Quarter Finals: 1,2 + 6 PreQ winners
    qf_matches = []
    qf_teams = [top14.iloc[0]["Team Name"], top14.iloc[1]["Team Name"]] + preq_winners
    for i in range(1,5):
        qf_matches.append({
            "Stage": "Quarter Final",
            "Match": i,
            "Teams": f"{qf_teams[i-1]} vs {qf_teams[-i]}",
            "Ground": f"Ground {i}"
        })
    knockout_result_section("Quarter Finals", qf_matches, "qf_results")
    # Get QF winners for Semis
    def get_qf_winners():
        qf_results = data.get("qf_results", {})
        return [qf_results.get(str(i+1), f"Winner QF{i+1}") for i in range(4)]
    qf_winners = get_qf_winners()
    sf_matches = []
    for i in range(1,3):
        sf_matches.append({
            "Stage": "Semi Final",
            "Match": i,
            "Teams": f"{qf_winners[i-1]} vs {qf_winners[4-i]}",
            "Ground": f"Ground {i}"
        })
    knockout_result_section("Semi Finals", sf_matches, "sf_results")
    # Get SF winners for Final
    def get_sf_winners():
        sf_results = data.get("sf_results", {})
        return [sf_results.get(str(i+1), f"Winner SF{i+1}") for i in range(2)]
    sf_winners = get_sf_winners()
    final_match = [{
        "Stage": "Final",
        "Match": 1,
        "Teams": f"{sf_winners[0]} vs {sf_winners[1]}",
        "Ground": "Ground 1"
    }]
    knockout_result_section("Final", final_match, "final_results")
    # Show balloons if final results are updated
    final_results = data.get("final_results", {})
    # Show balloons only if a real winner is selected and not a placeholder
    if (
        isinstance(final_results, dict)
        and len(final_results) == 1
        and list(final_results.values())[0] not in [f"Winner SF1", f"Winner SF2", "", None]
    ):
        winner = list(final_results.values())[0]
        st.balloons()
        st.success(f"🏆 Congratulations to {winner} for winning the tournament!")
else:
    st.info("Not enough teams/results to auto-generate knockout fixtures. At least 14 teams required.")
