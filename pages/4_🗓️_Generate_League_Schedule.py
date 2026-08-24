# pages/4_🗓️_Generate_League_Schedule.py
import pandas as pd
import streamlit as st

import sidebar
import ui
from utils import save_tourney_data, is_organizer, generate_intelligent_schedule

ui.inject_global_css()
sidebar.render()
ui.guard_login()

ui.page_header("League Schedule", "Automated team-as-umpire round-robin scheduling.", "🗓️")
if is_organizer():
    st.caption(
        "Matches are grouped into rounds where no team repeats, so different grounds can share the same "
        "start time. Umpires are assigned neutrally from any team not playing at that moment — opening "
        "matches at the League Start Time are marked Umpire: TBD, since no team is free yet. "
        "Knockout matches are handled on their own page."
    )

if not st.session_state.groups:
    ui.empty_state("Groups must be created before a schedule can be generated.")
    st.stop()

if is_organizer():
    def _update_start_time():
        st.session_state.start_time = st.session_state.start_time_input
        save_tourney_data()

    st.time_input("League Start Time", value=st.session_state.start_time, key="start_time_input", on_change=_update_start_time)
    if not st.session_state.grounds:
        st.warning("Add at least one ground on the Manage Resources page before generating a schedule.")
    c1, c2 = st.columns(2)
    if c1.button("Generate", type="primary", use_container_width=True, disabled=not st.session_state.grounds):
        st.session_state.schedule = generate_intelligent_schedule(st.session_state.groups, st.session_state.start_time)
        save_tourney_data()
        st.rerun()
    if c2.button("Clear Schedule", use_container_width=True):
        st.session_state.schedule = []
        save_tourney_data()
        st.rerun()
    st.markdown("---")

if not st.session_state.schedule:
    ui.empty_state("No league schedule has been generated yet.")
    st.stop()

if is_organizer():
    st.subheader("Edit Matches")
    st.caption("Adjust time, ground, teams, or umpire for any match — edits save automatically.")

    schedule = st.session_state.schedule
    df = pd.DataFrame([
        {
            "Group": m["group"],
            "Team 1": m["teams"][0],
            "Team 2": m["teams"][1],
            "Ground": m["ground"],
            "Umpire": m["umpire"],
            "Time": m["time"],
        }
        for m in schedule
    ])

    team_options = st.session_state.teams
    umpire_options = st.session_state.teams + ["TBD"]

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Group": st.column_config.TextColumn("Group", disabled=True),
            "Team 1": st.column_config.SelectboxColumn("Team 1", options=team_options, required=True),
            "Team 2": st.column_config.SelectboxColumn("Team 2", options=team_options, required=True),
            "Ground": st.column_config.SelectboxColumn("Ground", options=st.session_state.grounds, required=True),
            "Umpire": st.column_config.SelectboxColumn("Umpire", options=umpire_options, required=True),
            "Time": st.column_config.TimeColumn("Time", format="hh:mm a", step=300, required=True),
        },
        key="schedule_editor",
    )

    if not edited_df.equals(df):
        same_team_rows = edited_df[edited_df["Team 1"] == edited_df["Team 2"]]
        if not same_team_rows.empty:
            st.error("A team can't play itself — fix the highlighted row(s) before this saves (Team 1 = Team 2).")
        else:
            st.session_state.schedule = [
                {
                    "teams": [row["Team 1"], row["Team 2"]],
                    "group": row["Group"],
                    "ground": row["Ground"],
                    "umpire": row["Umpire"],
                    "time": row["Time"],
                }
                for _, row in edited_df.iterrows()
            ]
            save_tourney_data()
            st.toast("Schedule updated!")
            st.rerun()
    st.markdown("---")

league_grounds = sorted(list(set(m['ground'] for m in st.session_state.schedule)))
gs = {g: [] for g in league_grounds}
for m in st.session_state.schedule:
    gs.get(m['ground'], []).append(m)
cols = st.columns(len(league_grounds) if league_grounds else 1)
for i, g in enumerate(league_grounds):
    with cols[i]:
        st.subheader(f"📍 {g}")
        for m in sorted(gs[g], key=lambda x: x['time']):
            with st.container(border=True):
                st.markdown(f"**{m['teams'][0]} vs {m['teams'][1]}**")
                st.caption(f"Time: {m['time'].strftime('%I:%M %p')} | Umpire: {m['umpire']}")
