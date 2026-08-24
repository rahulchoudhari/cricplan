# pages/7_📝_Tournament_Waiver.py
import streamlit as st

import sidebar
import ui
from utils import save_tourney_data, is_organizer

ui.inject_global_css()
sidebar.render()
ui.guard_login()

ui.page_header("Tournament Waiver", "Share the waiver form participants must complete.", "📝")

PREVIOUS_YEAR_WAIVER_LINK = "https://forms.gle/2ppu8vXRqP8D75Zb7"

if is_organizer():
    def _update_waiver_link():
        st.session_state.waiver_link = st.session_state.waiver_link_input
        save_tourney_data()

    st.info("As an organizer, you can set the public link for the waiver form.")
    st.text_input("Set Waiver Form Link", value=st.session_state.waiver_link, key="waiver_link_input", on_change=_update_waiver_link)
    st.caption(
        f"Don't have this year's form ready yet? [Last year's waiver form]({PREVIOUS_YEAR_WAIVER_LINK}) "
        "can be used as a reference, or copied and updated, until the new one is set."
    )
    st.markdown("---")

if st.session_state.waiver_link:
    st.markdown(f"### [Click Here to Access the Waiver Form]({st.session_state.waiver_link})")
    st.caption("All participants are required to fill out the waiver form before their first match.")
else:
    ui.empty_state("The tournament organizer has not set a waiver link yet.")
