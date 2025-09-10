# pages/2_🏏_Manage_Resources.py
import streamlit as st
from utils import save_tourney_data, is_organizer

if not st.session_state.get('user_logged_in') or not is_organizer():
    st.warning("This page is for organizers only.", icon="🔒")
    st.stop()
    
st.title("🏏 Manage Resources"); st.info("Add Grounds and Umpires for the Knockout Stage.")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Grounds")
    with st.form("add_ground", clear_on_submit=True):
        name = st.text_input("Ground Name"); submitted = st.form_submit_button("Add")
        if submitted and name and name not in st.session_state.grounds:
            st.session_state.grounds.append(name); save_tourney_data(); st.rerun()
    if st.session_state.grounds:
        for g in st.session_state.grounds:
            if st.button(f"Delete '{g}'", key=f"del_g_{g}"):
                st.session_state.grounds.remove(g); save_tourney_data(); st.rerun()
with c2:
    st.subheader("Umpires")
    with st.form("add_umpire", clear_on_submit=True):
        name = st.text_input("Umpire Name"); submitted = st.form_submit_button("Add")
        if submitted and name and name not in st.session_state.umpires:
            st.session_state.umpires.append(name); save_tourney_data(); st.rerun()
    if st.session_state.umpires:
        for u in st.session_state.umpires:
            if st.button(f"Delete '{u}'", key=f"del_u_{u}"):
                st.session_state.umpires.remove(u); save_tourney_data(); st.rerun()