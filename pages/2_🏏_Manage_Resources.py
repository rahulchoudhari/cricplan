# pages/2_🏏_Manage_Resources.py
import streamlit as st

import db
import images
import sidebar
import ui
from utils import save_tourney_data, get_active_tournament_id

ui.inject_global_css()
sidebar.render()
ui.guard_organizer()

ui.page_header("Manage Resources", "Add grounds, umpires, and sponsors for the tournament.", "🏏")

active_id = get_active_tournament_id()
if not active_id:
    ui.empty_state("Create or select a tournament on the Tournament Setup page first.")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    st.subheader("Grounds")
    with st.form("add_ground", clear_on_submit=True):
        name = st.text_input("Ground Name")
        submitted = st.form_submit_button("Add")
        if submitted and name and name not in st.session_state.grounds:
            st.session_state.grounds.append(name)
            save_tourney_data()
            st.rerun()
    if st.session_state.grounds:
        for g in st.session_state.grounds:
            cc1, cc2 = st.columns([0.8, 0.2])
            cc1.write(f"📍 {g}")
            if cc2.button("🗑️", key=f"del_g_{g}"):
                st.session_state.grounds.remove(g)
                save_tourney_data()
                st.rerun()
    else:
        ui.empty_state("No grounds added yet.")

with c2:
    st.subheader("Umpires")
    with st.form("add_umpire", clear_on_submit=True):
        name = st.text_input("Umpire Name")
        submitted = st.form_submit_button("Add")
        if submitted and name and name not in st.session_state.umpires:
            st.session_state.umpires.append(name)
            save_tourney_data()
            st.rerun()
    if st.session_state.umpires:
        for u in st.session_state.umpires:
            cc1, cc2 = st.columns([0.8, 0.2])
            cc1.write(f"🧑‍⚖️ {u}")
            if cc2.button("🗑️", key=f"del_u_{u}"):
                st.session_state.umpires.remove(u)
                save_tourney_data()
                st.rerun()
    else:
        ui.empty_state("No umpires added yet.")

st.markdown("---")
st.subheader("🤝 Sponsors")
st.caption("Shown as a scrolling logo strip on your tournament's home page.")

sponsors = db.get_sponsors(active_id)

if sponsors:
    cols = st.columns(4)
    for i, s in enumerate(sponsors):
        with cols[i % 4]:
            if s.get('image_data'):
                st.image(f"data:image/png;base64,{s['image_data']}", width=120)
            else:
                st.markdown(f"**{ui.esc(s['sponsor_name'])}**", unsafe_allow_html=True)
            st.caption(s['sponsor_name'])
            if st.button("🗑️ Remove", key=f"del_sponsor_{s['id']}", width='stretch'):
                db.delete_sponsor(s['id'])
                st.rerun()
else:
    ui.empty_state("No sponsors added yet.")

with st.form("add_sponsor", clear_on_submit=True):
    st.markdown("**Add a sponsor**")
    sp_name = st.text_input("Sponsor Name")
    sp_link = st.text_input("Website Link (optional)")
    sp_logo = st.file_uploader("Sponsor Logo (optional)", type=["png", "jpg", "jpeg", "webp"])
    if st.form_submit_button("Add Sponsor"):
        if not sp_name.strip():
            st.warning("Sponsor name is required.")
        else:
            try:
                image_data = images.process_upload(sp_logo, max_dim=400) if sp_logo is not None else None
                db.add_sponsor(active_id, sp_name.strip(), image_data, sp_link.strip() or None)
                st.rerun()
            except images.UploadTooLarge as e:
                st.error(str(e))
