import streamlit as st
from utils import save_tourney_data, is_organizer, generate_intelligent_schedule

if not st.session_state.get('user_logged_in'): st.warning("Please log in to view schedules.", icon="🔒"); st.stop()

st.title("🗓️ League Schedule"); 
if is_organizer(): st.info("This uses the automated Team-as-Umpire system for the league. Knockout matches are handled on their own page.")
if not st.session_state.groups: st.warning("Groups must be created before a schedule can be generated."); st.stop()
    
if is_organizer():
    st.time_input("League Start Time", key="start_time", on_change=save_tourney_data)
    c1, c2 = st.columns(2);
    if c1.button("Generate", type="primary", use_container_width=True): 
        st.session_state.schedule = generate_intelligent_schedule(st.session_state.groups, st.session_state.start_time); save_tourney_data(); st.rerun()
    if c2.button("Clear Schedule", use_container_width=True): 
        st.session_state.schedule = []; save_tourney_data(); st.rerun()
st.markdown("---")
if st.session_state.schedule:
    league_grounds = sorted(list(set(m['ground'] for m in st.session_state.schedule)))
    gs = {g:[] for g in league_grounds}
    for m in st.session_state.schedule: gs.get(m['ground'], []).append(m)
    cols=st.columns(len(league_grounds) if league_grounds else 1)
    for i, g in enumerate(league_grounds):
        with cols[i]:
            st.subheader(f"📍 {g}")
            for m in sorted(gs[g], key=lambda x:x['time']):
                with st.container(border=True):
                    st.markdown(f"**{m['teams'][0]} vs {m['teams'][1]}**")
                    st.caption(f"Time: {m['time'].strftime('%I:%M %p')} | Umpire: {m['umpire']}")
else: st.info("No league schedule has been generated yet.")