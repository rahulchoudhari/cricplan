# utils.py
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# --- File Paths ---
USER_DB_FILE = Path("users.json")

def get_tourney_data_file():
    # Uses username and tournament name to create a unique file for each tournament.
    username = st.session_state.get('username')
    tname = st.session_state.get('tournament_name', 'Default Tournament')
    if username:
        safe_tname = ''.join(c for c in tname if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        return Path(f"tournament_data_{username}_{safe_tname}.json")
    return None # Return None if no user is logged in

# --- Data Handling ---
def load_data(file_path):
    if file_path and file_path.exists():
        with open(file_path, "r") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def save_data(data, file_path):
    if file_path:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

def save_tourney_data():
    tourney_data = {
        'tournament_name': st.session_state.tournament_name, 'teams': st.session_state.teams,
        'grounds': st.session_state.grounds, 'umpires': st.session_state.umpires,
        'groups': st.session_state.groups, 'waiver_link': st.session_state.waiver_link,
        'schedule': [{**m, 'time': m['time'].strftime('%H:%M:%S')} for m in st.session_state.schedule],
        'league_results': st.session_state.league_results,
        'knockout_matches': st.session_state.knockout_matches,
        'start_time': st.session_state.start_time.strftime('%H:%M:%S'),
        'checklist_data': st.session_state.get('checklist_data', []) # Save checklist data
    }
    tourney_file = get_tourney_data_file()
    save_data(tourney_data, tourney_file)

# --- State Initialization ---
def initialize_state_base():
    if 'app_init' not in st.session_state:
        st.session_state.user_db = load_data(USER_DB_FILE)
        st.session_state.user_logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.app_init = True

def load_tournament_state():
    tourney_file = get_tourney_data_file()
    tourney_data = load_data(tourney_file)
    st.session_state.tournament_name = tourney_data.get('tournament_name', "New Tournament")
    st.session_state.teams = tourney_data.get('teams', [])
    st.session_state.grounds = tourney_data.get('grounds', [])
    st.session_state.umpires = tourney_data.get('umpires', [])
    st.session_state.groups = tourney_data.get('groups', {})
    st.session_state.league_results = tourney_data.get('league_results', {})
    st.session_state.waiver_link = tourney_data.get('waiver_link', "")
    st.session_state.start_time = datetime.strptime(tourney_data.get('start_time', '08:00:00'), '%H:%M:%S').time()
    
    # Handle checklist data with st.data_editor format
    st.session_state.checklist_data = tourney_data.get('checklist_data', [])
    
    # Deserialize complex objects
    schedule_data = tourney_data.get('schedule', [])
    deserialized_schedule = []
    for match in schedule_data:
        match['time'] = datetime.strptime(match['time'], '%H:%M:%S').time()
        deserialized_schedule.append(match)
    st.session_state.schedule = deserialized_schedule
    
    # Default structure for knockouts if not present
    knockout_matches = tourney_data.get('knockout_matches', {})
    if not knockout_matches:
        knockout_matches = {
            m_id: {'teams':['',''],'winner':None,'ground':None,'umpire':None}
            for m_id in ['PQ1','PQ2','PQ3','PQ4','PQ5','PQ6','Q1','Q2','Q3','Q4','SF1','SF2','Final']
        }
    st.session_state.knockout_matches = knockout_matches
    
# --- Helper Functions ---
def get_ranked_teams():
    if not st.session_state.league_results: return []
    df = pd.DataFrame([{'Team': team, **data} for team, data in st.session_state.league_results.items()])
    return df.sort_values(by=['Points', 'NRR'], ascending=[False, False])['Team'].tolist()

def is_organizer():
    return st.session_state.get('role') in ["Admin", "Tournament Organizer"]

# --- League Schedule Generator ---
from datetime import timedelta

def generate_intelligent_schedule(groups, start_time):
    """
    Generates a round-robin schedule for each group.
    Each match is assigned a ground and umpire (team-as-umpire system).
    Matches are scheduled sequentially starting from start_time.
    """
    # Get available grounds and umpires from session state
    grounds = st.session_state.get('grounds', ['Ground 1'])
    umpires = []
    schedule = []
    match_duration = timedelta(minutes=60)  # 1 hour per match (customize as needed)
    current_time = (datetime.combine(datetime.today(), start_time))

    for group_name, teams in groups.items():
        n = len(teams)
        # Round-robin: each team plays every other team once
        for i in range(n):
            for j in range(i+1, n):
                team1, team2 = teams[i], teams[j]
                # Assign ground in round-robin fashion
                ground = grounds[(len(schedule)) % len(grounds)]
                # Assign umpire: pick a team not playing in this match
                umpire_candidates = [t for t in teams if t != team1 and t != team2]
                umpire = umpire_candidates[0] if umpire_candidates else 'TBD'
                match = {
                    'teams': [team1, team2],
                    'group': group_name,
                    'ground': ground,
                    'umpire': umpire,
                    'time': current_time.time(),
                }
                schedule.append(match)
                # Increment time for next match
                current_time += match_duration
    return schedule