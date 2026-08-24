# pages/5_📊_League_Results.py
import pandas as pd
import streamlit as st

import sidebar
import ui
from utils import save_tourney_data, is_organizer, get_ranked_teams, get_active_tournament_id

ui.inject_global_css()
sidebar.render()

ui.page_header("League Results", "Enter results and track live standings.", "📊")
if not st.session_state.user_logged_in and st.session_state.get('tournament_name'):
    st.caption(f"Viewing: **{ui.esc(st.session_state.tournament_name)}** — switch tournaments from the sidebar.", unsafe_allow_html=True)

if not st.session_state.teams:
    ui.empty_state(
        "No teams registered yet." if get_active_tournament_id()
        else "No tournaments have been set up yet — pick one from the sidebar once one exists."
    )
    st.stop()

c1, c2 = st.columns([1, 2])
with c1:
    if is_organizer():
        st.subheader("Add/Update Results")
        teams_without_res = [t for t in st.session_state.teams if t not in st.session_state.league_results]
        if not teams_without_res:
            st.success("All results entered.")
        else:
            with st.form("res_form"):
                team = st.selectbox("Select Team", options=teams_without_res)
                pts = st.number_input("Points", min_value=0, step=1)
                nrr = st.number_input("NRR", min_value=-10.0, max_value=10.0, value=0.0, step=0.001, format="%.3f")
                if st.form_submit_button("Save", type="primary", width='stretch'):
                    st.session_state.league_results[team] = {'Points': pts, 'NRR': nrr}
                    save_tourney_data()
                    st.rerun()
with c2:
    st.subheader("Official Standings")
    ranked_teams = get_ranked_teams()
    if not ranked_teams:
        ui.empty_state("No results yet.")
    else:
        df = pd.DataFrame([{'Team': t, **st.session_state.league_results[t]} for t in ranked_teams])
        df.index = range(1, len(df) + 1)
        st.dataframe(df, width='stretch')
        if is_organizer():
            team_to_edit = st.selectbox("Select team to edit/delete result", ["", *ranked_teams])
            if team_to_edit and st.button(f"Delete result for {team_to_edit}", width='stretch'):
                del st.session_state.league_results[team_to_edit]
                save_tourney_data()
                st.rerun()
