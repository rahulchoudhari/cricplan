import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="🏥 Tournament Medical Waiver Form")
st.title("🏥 Tournament Medical Waiver Form")

WAIVER_FILE = "waiver_link.json"

def get_waiver_link():
    if Path(WAIVER_FILE).exists():
        with open(WAIVER_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("waiver_link", "")
            except Exception:
                return ""
    return ""

def set_waiver_link(link):
    with open(WAIVER_FILE, "w") as f:
        json.dump({"waiver_link": link}, f)

waiver_link = get_waiver_link()

if not waiver_link:
    st.markdown("""
### Tournament Medical Waiver Form Template

No waiver form link has been set yet. Please use the following template to create your own Google Form for the tournament waiver:

**[Click here to view the Medical Waiver Form Template](https://forms.gle/ona51AaxP4nzeYDN8)**

Once your Google Form is ready, paste the link below and click 'Save Waiver Link'.
""")

    with st.form("set_waiver_link_form"):
        new_link = st.text_input("Medical Waiver Form Link", value=waiver_link, placeholder="Paste Google Form or waiver link here")
        submitted = st.form_submit_button("Save Waiver Link")
        if submitted:
            set_waiver_link(new_link)
            st.success("Waiver link saved!")
            waiver_link = new_link
            st.rerun()
else:
    st.markdown("""
Tournament organizers: You can update the Medical Waiver Form link below. This will be shown to all participants.
""")
    with st.form("set_waiver_link_form"):
        new_link = st.text_input("Medical Waiver Form Link", value=waiver_link, placeholder="Paste Google Form or waiver link here")
        submitted = st.form_submit_button("Save Waiver Link")
        if submitted:
            set_waiver_link(new_link)
            st.success("Waiver link saved!")
            waiver_link = new_link
            st.rerun()
    st.markdown("---")
    st.markdown(f"**[Click here to fill out the Medical Waiver Form]({waiver_link})**", unsafe_allow_html=True)
    st.markdown("""
If you have already submitted the form, no further action is required. For any questions or issues, please contact the tournament organizers.
""")
