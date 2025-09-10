import streamlit as st
from utils import save_tourney_data, is_organizer, get_ranked_teams
import pandas as pd

if not st.session_state.get('user_logged_in'): st.warning("Please log in to manage results.", icon="🔒"); st.stop()

st.title("📊 League Results"); 
if not st.session_state.teams: st.warning("Add teams first."); st.stop()
c1, c2 = st.columns([1,2]); 
with c1:
    if is_organizer():
        st.subheader("Add/Update Results")
        teams_without_res = [t for t in st.session_state.teams if t not in st.session_state.league_results]
        if not teams_without_res: st.success("All results entered.")
        else:
            with st.form("res_form"):
                team=st.selectbox("Select Team", options=teams_without_res); pts=st.number_input("Points", 0, step=1); nrr=st.number_input("NRR", -10.0, 10.0, 0.0, "%.3f", step=0.001)
                if st.form_submit_button("Save", use_container_width=True): st.session_state.league_results[team] = {'Points':pts, 'NRR':nrr}; save_tourney_data(); st.rerun()
with c2:
    st.subheader("Official Standings"); ranked_teams = get_ranked_teams()
    if not ranked_teams: st.info("No results yet.")
    else:
        df = pd.DataFrame([{'Team': t, **st.session_state.league_results[t]} for t in ranked_teams]); df.index = range(1, len(df) + 1)
        st.dataframe(df, use_container_width=True)
        if is_organizer():
            team_to_edit = st.selectbox("Select team to edit/delete result", ["", *ranked_teams])
            if team_to_edit and st.button(f"Delete result for {team_to_edit}", use_container_width=True):
                del st.session_state.league_results[team_to_edit]
                save_tourney_data()
                st.rerun()
