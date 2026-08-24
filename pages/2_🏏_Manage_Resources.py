# pages/2_🏏_Manage_Resources.py
import streamlit as st

import db
import images
import sidebar
import ui
from utils import save_tourney_data, get_tourney_owner_and_name

ui.inject_global_css()
sidebar.render()
ui.guard_organizer()

ui.page_header("Manage Resources", "Add grounds, umpires, and sponsors for the tournament.", "🏏")

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

owner, _ = get_tourney_owner_and_name()
sponsors = db.get_sponsors(owner)

if sponsors:
    cols = st.columns(4)
    for i, s in enumerate(sponsors):
        with cols[i % 4]:
            st.image(f"data:image/png;base64,{s['image_data']}", width=120)
            st.caption(s['sponsor_name'])
            if st.button("🗑️ Remove", key=f"del_sponsor_{s['id']}", use_container_width=True):
                db.delete_sponsor(s['id'])
                st.rerun()
else:
    ui.empty_state("No sponsors added yet.")

with st.form("add_sponsor", clear_on_submit=True):
    st.markdown("**Add a sponsor**")
    sp_name = st.text_input("Sponsor Name")
    sp_link = st.text_input("Website Link (optional)")
    sp_logo = st.file_uploader("Sponsor Logo", type=["png", "jpg", "jpeg", "webp"])
    if st.form_submit_button("Add Sponsor"):
        if not sp_name.strip():
            st.warning("Sponsor name is required.")
        elif sp_logo is None:
            st.warning("Please upload a logo image.")
        else:
            try:
                image_data = images.process_upload(sp_logo, max_dim=400)
                db.add_sponsor(owner, sp_name.strip(), image_data, sp_link.strip() or None)
                st.rerun()
            except images.UploadTooLarge as e:
                st.error(str(e))
