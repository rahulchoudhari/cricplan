# utils.py
import streamlit as st
from datetime import datetime, timedelta

import pandas as pd

import db

# --- Tournament context ---------------------------------------------------

def get_tourney_owner_and_name():
    """Every tournament is namespaced by its organizer's username + a
    tournament name. Organizers/Admins own their own tournament(s); Team
    Captains/Players are linked to the tournament they joined at signup."""
    role = st.session_state.get('role')
    if role in ("Admin", "Tournament Organizer"):
        return st.session_state.get('username'), st.session_state.get('tournament_name', 'Default Tournament')
    return st.session_state.get('linked_owner'), st.session_state.get('linked_tournament')


def save_tourney_data():
    owner, _ = get_tourney_owner_and_name()
    if not owner:
        return
    tname = st.session_state.tournament_name
    tourney_data = {
        'tournament_name': tname, 'teams': st.session_state.teams,
        'grounds': st.session_state.grounds, 'umpires': st.session_state.umpires,
        'groups': st.session_state.groups, 'waiver_link': st.session_state.waiver_link,
        'schedule': [{**m, 'time': m['time'].strftime('%H:%M:%S')} for m in st.session_state.schedule],
        'league_results': st.session_state.league_results,
        'knockout_matches': st.session_state.knockout_matches,
        'start_time': st.session_state.start_time.strftime('%H:%M:%S'),
        'checklist_data': st.session_state.get('checklist_data', []),
        'flyer_image': st.session_state.get('flyer_image'),
    }
    db.save_tournament_data(owner, tname, tourney_data)


# --- State initialization --------------------------------------------------

def initialize_state_base():
    if 'app_init' not in st.session_state:
        st.session_state.user_logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.linked_owner = None
        st.session_state.linked_tournament = None
        st.session_state.app_init = True


def load_tournament_state():
    owner, tname = get_tourney_owner_and_name()
    tourney_data = db.load_tournament_data(owner) if owner else {}
    is_new = not tourney_data

    st.session_state.tournament_name = tourney_data.get('tournament_name', tname or "New Tournament")
    st.session_state.teams = tourney_data.get('teams', [])
    st.session_state.grounds = tourney_data.get('grounds', [])
    st.session_state.umpires = tourney_data.get('umpires', [])
    st.session_state.groups = tourney_data.get('groups', {})
    st.session_state.league_results = tourney_data.get('league_results', {})
    st.session_state.waiver_link = tourney_data.get('waiver_link', "")
    st.session_state.start_time = datetime.strptime(tourney_data.get('start_time', '08:00:00'), '%H:%M:%S').time()

    st.session_state.checklist_data = tourney_data.get('checklist_data', [])
    st.session_state.flyer_image = tourney_data.get('flyer_image')

    schedule_data = tourney_data.get('schedule', [])
    deserialized_schedule = []
    for match in schedule_data:
        match['time'] = datetime.strptime(match['time'], '%H:%M:%S').time()
        deserialized_schedule.append(match)
    st.session_state.schedule = deserialized_schedule

    knockout_matches = tourney_data.get('knockout_matches', {})
    if not knockout_matches:
        knockout_matches = {
            m_id: {'teams': ['', ''], 'winner': None, 'ground': None, 'umpire': None}
            for m_id in ['PQ1', 'PQ2', 'PQ3', 'PQ4', 'PQ5', 'PQ6', 'Q1', 'Q2', 'Q3', 'Q4', 'SF1', 'SF2', 'Final']
        }
    st.session_state.knockout_matches = knockout_matches

    # Persist the freshly-initialized state right away so the tournament
    # shows up for team captains/players to join, even before the
    # organizer has made any changes.
    if is_new and st.session_state.get('role') in ("Admin", "Tournament Organizer"):
        save_tourney_data()


# --- Helper functions --------------------------------------------------

def get_ranked_teams():
    if not st.session_state.league_results:
        return []
    df = pd.DataFrame([{'Team': team, **data} for team, data in st.session_state.league_results.items()])
    return df.sort_values(by=['Points', 'NRR'], ascending=[False, False])['Team'].tolist()


def is_organizer():
    return st.session_state.get('role') in ["Admin", "Tournament Organizer"]


# --- League Schedule Generator ------------------------------------------

def _round_robin_rounds(teams):
    """Circle-method round-robin: returns a list of rounds, each a list of
    (team1, team2) pairs where every team appears at most once per round —
    so a round's matches can be played simultaneously on different grounds
    without double-booking a team. An odd team count gets one bye per round."""
    teams = list(teams)
    if len(teams) % 2 == 1:
        teams.append(None)
    n = len(teams)
    fixed, rotating = teams[0], teams[1:]
    rounds = []
    for _ in range(n - 1):
        round_teams = [fixed] + rotating
        pairs = [
            (round_teams[k], round_teams[n - 1 - k])
            for k in range(n // 2)
            if round_teams[k] is not None and round_teams[n - 1 - k] is not None
        ]
        rounds.append(pairs)
        rotating = [rotating[-1]] + rotating[:-1]
    return rounds


def _assign_neutral_umpires(schedule):
    """Umpires are assigned neutrally: any team not playing at that exact
    time slot (in any group) is eligible — not just a bye team from the same
    group — since a team from a group that hasn't started yet, or has
    already finished, is genuinely free the whole time. The very first time
    slot of the day (League Start Time) is always 'TBD': nobody has played
    yet, so the organizer lines up dedicated umpires for the opening
    matches rather than pulling a competing team off the field."""
    if not schedule:
        return
    all_teams = [m['teams'][0] for m in schedule] + [m['teams'][1] for m in schedule]
    all_teams = list(dict.fromkeys(all_teams))  # de-duplicate, keep order

    by_time = {}
    for m in schedule:
        by_time.setdefault(m['time'], []).append(m)
    league_start = min(by_time)

    for t, matches in by_time.items():
        if t == league_start:
            for m in matches:
                m['umpire'] = 'TBD'
            continue
        playing = {team for m in matches for team in m['teams']}
        free_teams = [team for team in all_teams if team not in playing]
        for i, m in enumerate(matches):
            m['umpire'] = free_teams[i] if i < len(free_teams) else 'TBD'


def generate_intelligent_schedule(groups, start_time):
    """
    Generates a round-robin schedule for each group using the circle method,
    so matches within the same round involve no repeated team and can be
    played at the same start time across different grounds. A round that has
    more matches than available grounds spills its extra matches into the
    next time slot before the following round begins. Umpires are assigned
    afterward by _assign_neutral_umpires, once every match's time is known.
    """
    grounds = st.session_state.get('grounds') or ['Ground 1']
    num_grounds = len(grounds)
    schedule = []
    match_duration = timedelta(minutes=60)
    base_time = datetime.combine(datetime.today(), start_time)
    slot = 0

    for group_name, teams in groups.items():
        for round_pairs in _round_robin_rounds(teams):
            for i, (team1, team2) in enumerate(round_pairs):
                ground = grounds[i % num_grounds]
                match_time = (base_time + (slot + i // num_grounds) * match_duration).time()
                schedule.append({
                    'teams': [team1, team2],
                    'group': group_name,
                    'ground': ground,
                    'umpire': None,
                    'time': match_time,
                })
            slot += -(-len(round_pairs) // num_grounds)  # ceil(matches / grounds)

    _assign_neutral_umpires(schedule)
    return schedule
