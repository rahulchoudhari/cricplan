# pages/6_🏅_Knock_Out_Fixture.py
import streamlit as st

import sidebar
import ui
from utils import save_tourney_data, is_organizer, get_active_tournament_id

ui.inject_global_css()
sidebar.render()

ui.page_header("Knock Out Fixture", "Set up the bracket, assign officials, and record winners.", "🏅")
if not st.session_state.user_logged_in and st.session_state.get('tournament_name'):
    st.caption(f"Viewing: **{ui.esc(st.session_state.tournament_name)}** — switch tournaments from the sidebar.", unsafe_allow_html=True)

if not st.session_state.teams:
    ui.empty_state(
        "No teams registered yet." if get_active_tournament_id()
        else "No tournaments have been set up yet — pick one from the sidebar once one exists."
    )
    st.stop()

STAGES = [
    ("Pre-Quarterfinals", ['PQ1', 'PQ2', 'PQ3', 'PQ4', 'PQ5', 'PQ6']),
    ("Quarterfinals", ['Q1', 'Q2', 'Q3', 'Q4']),
    ("Semifinals", ['SF1', 'SF2']),
    ("Final", ['Final']),
]

team_options = ["TBD"] + st.session_state.teams
ground_options = st.session_state.get('grounds') or ["TBD"]
umpire_options = st.session_state.get('umpires') or ["TBD"]

for stage_name, match_ids in STAGES:
    st.subheader(stage_name)
    cols = st.columns(len(match_ids))
    for col, m_id in zip(cols, match_ids):
        match = st.session_state.knockout_matches.get(m_id, {'teams': ['', ''], 'winner': None, 'ground': None, 'umpire': None})
        with col:
            with st.container(border=True):
                st.caption(m_id)
                if is_organizer():
                    t1 = st.selectbox("Team 1", team_options,
                                       index=team_options.index(match['teams'][0]) if match['teams'][0] in team_options else 0,
                                       key=f"{m_id}_t1")
                    t2 = st.selectbox("Team 2", team_options,
                                       index=team_options.index(match['teams'][1]) if match['teams'][1] in team_options else 0,
                                       key=f"{m_id}_t2")
                    ground = st.selectbox("Ground", ground_options,
                                           index=ground_options.index(match['ground']) if match.get('ground') in ground_options else 0,
                                           key=f"{m_id}_ground")
                    umpire = st.selectbox("Umpire", umpire_options,
                                           index=umpire_options.index(match['umpire']) if match.get('umpire') in umpire_options else 0,
                                           key=f"{m_id}_umpire")
                    winner_options = ["TBD"] + [t for t in (t1, t2) if t != "TBD"]
                    winner = st.selectbox("Winner", winner_options,
                                           index=winner_options.index(match['winner']) if match.get('winner') in winner_options else 0,
                                           key=f"{m_id}_winner")
                    if st.button("Save", key=f"{m_id}_save", width='stretch'):
                        st.session_state.knockout_matches[m_id] = {
                            'teams': [t1, t2],
                            'ground': ground if ground != "TBD" else None,
                            'umpire': umpire if umpire != "TBD" else None,
                            'winner': winner if winner != "TBD" else None,
                        }
                        save_tourney_data()
                        st.rerun()
                else:
                    st.markdown(f"**{match['teams'][0] or 'TBD'}** vs **{match['teams'][1] or 'TBD'}**")
                    st.caption(f"📍 {match.get('ground') or 'TBD'} · 🧑‍⚖️ {match.get('umpire') or 'TBD'}")
                    if match.get('winner'):
                        st.success(f"🏆 {match['winner']}")
