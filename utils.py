# utils.py
import streamlit as st
from datetime import datetime, timedelta

import pandas as pd

import db

# --- Tournament context ---------------------------------------------------

def get_active_tournament_id():
    """An organizer/admin can own several tournaments, and a Manager can be
    assigned to several more (by an owner, never self-selected) — for both,
    `active_tournament_id` is whichever one they're currently working on,
    switchable on Tournament Setup. Team Captains/Players are linked to the
    single tournament they joined at signup. A visitor who isn't logged in
    views whichever tournament they picked from the sidebar's public
    browser (see sidebar.py)."""
    role = st.session_state.get('role')
    if role in ("Admin", "Tournament Organizer", "Manager"):
        return st.session_state.get('active_tournament_id')
    if role in ("Team Captain", "Player"):
        return st.session_state.get('linked_tournament_id')
    return st.session_state.get('public_tournament_id')


def can_manage_tournament():
    """Broader than is_organizer(): also lets a Manager operate on the
    tournament they're currently switched to (schedule, teams, resources,
    results, knockout, checklist, waiver, sponsors/flyer) — but never
    account approvals, tournament create/rename/delete, or Manager
    assignment itself, which stay Admin/Organizer-only."""
    return st.session_state.get('role') in ("Admin", "Tournament Organizer", "Manager")


def save_tourney_data():
    tid = get_active_tournament_id()
    if not tid:
        return
    tourney_data = {
        'tournament_name': st.session_state.tournament_name, 'teams': st.session_state.teams,
        'grounds': st.session_state.grounds, 'umpires': st.session_state.umpires,
        'groups': st.session_state.groups, 'waiver_link': st.session_state.waiver_link,
        'schedule': [{**m, 'time': m['time'].strftime('%H:%M:%S')} for m in st.session_state.schedule],
        'league_results': st.session_state.league_results,
        'knockout_matches': st.session_state.knockout_matches,
        'start_time': st.session_state.start_time.strftime('%H:%M:%S'),
        'checklist_data': st.session_state.get('checklist_data', []),
        'flyer_image': st.session_state.get('flyer_image'),
    }
    db.save_tournament_data(tid, tourney_data)


# --- State initialization --------------------------------------------------

def initialize_state_base():
    if 'app_init' not in st.session_state:
        st.session_state.user_logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.linked_tournament_id = None
        st.session_state.active_tournament_id = None
        st.session_state.public_tournament_id = None
        st.session_state.app_init = True
        # Seeds teams/groups/schedule/etc to safe empty defaults even
        # before any tournament is picked, so pages that read them
        # directly (not via .get()) don't crash for a brand-new visitor.
        load_tournament_state()


def load_tournament_state():
    tid = get_active_tournament_id()
    tourney_data = db.load_tournament_data(tid) if tid else {}

    st.session_state.tournament_name = tourney_data.get('tournament_name', "New Tournament")
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


# The Tournament Name / Waiver Link / League Start Time widgets keep their
# own value client-side once mounted. Popping their session_state key isn't
# enough to reset them: on the next rerun the frontend just re-reports its
# last cached value as if the user had typed it, which fires their
# on_change callback and writes the stale value straight back into the
# freshly-reset data. Call this after resetting tournament data from
# outside the widget's own on_change (e.g. after deleting a tournament) —
# it bumps a generation counter so those widgets get a brand new key and
# genuinely remount instead of reattaching stale client state.
def clear_tournament_widget_cache():
    st.session_state['tourney_widget_gen'] = st.session_state.get('tourney_widget_gen', 0) + 1


def tourney_widget_key(base: str) -> str:
    return f"{base}_{st.session_state.get('tourney_widget_gen', 0)}"


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
    Generates a round-robin schedule using the circle method, so matches
    within the same round involve no repeated team and can be played at the
    same start time across different grounds.

    Groups are interleaved round-by-round (every group's round 1 is packed
    together before any group's round 2 begins) rather than scheduled one
    group at a time — a group only produces a couple of matches per round,
    which would leave most grounds idle for the group's entire run if
    groups went fully sequential. Interleaving spreads round 1 of every
    group across ALL available grounds first, so a tournament with as many
    grounds as groups can run nearly every group in parallel. A combined
    round that has more matches than available grounds spills its extra
    matches into the next time slot before the following round begins.
    Umpires are assigned afterward by _assign_neutral_umpires, once every
    match's time is known.
    """
    grounds = st.session_state.get('grounds') or ['Ground 1']
    num_grounds = len(grounds)
    schedule = []
    match_duration = timedelta(minutes=60)
    base_time = datetime.combine(datetime.today(), start_time)
    slot = 0

    group_rounds = {name: _round_robin_rounds(teams) for name, teams in groups.items()}
    max_rounds = max((len(rounds) for rounds in group_rounds.values()), default=0)

    for round_idx in range(max_rounds):
        combined = [
            (group_name, pair)
            for group_name, rounds in group_rounds.items()
            if round_idx < len(rounds)
            for pair in rounds[round_idx]
        ]
        for i, (group_name, (team1, team2)) in enumerate(combined):
            ground = grounds[i % num_grounds]
            match_time = (base_time + (slot + i // num_grounds) * match_duration).time()
            schedule.append({
                'teams': [team1, team2],
                'group': group_name,
                'ground': ground,
                'umpire': None,
                'time': match_time,
            })
        slot += -(-len(combined) // num_grounds)  # ceil(matches / grounds)

    _assign_neutral_umpires(schedule)
    return schedule
