import streamlit as st
from utils import save_tourney_data, is_organizer

if not st.session_state.get('user_logged_in'): st.warning("Please log in to view the waiver.", icon="🔒"); st.stop()
    
st.title("📝 Tournament Waiver")
if is_organizer():
    st.info("As an organizer, you can set the public link for the waiver form.")
    st.text_input("Set Waiver Form Link", key="waiver_link", on_change=save_tourney_data)

st.markdown("---")
if st.session_state.waiver_link:
    st.markdown(f"### [Click Here to Access the Waiver Form]({st.session_state.waiver_link})")
    st.markdown("_All participants are required to fill out the waiver form before their first match._")
else: st.warning("The tournament organizer has not set a waiver link yet.")