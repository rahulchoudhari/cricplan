# pages/8_✅_Preparation_Checklist.py
import streamlit as st
import pandas as pd
from utils import save_tourney_data, is_organizer

if not st.session_state.get('user_logged_in') or not is_organizer():
    st.warning("This page is for organizers only.", icon="🔒")
    st.stop()
    
st.title("✅ Preparation Checklist")
st.info("Use this interactive table to track all tournament tasks. Your edits are saved automatically.")

# Default tasks if the checklist is empty
default_tasks = [
    {"Section": "Pre-Tournament", "Task": "Ground booking confirmed", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Flyer/Announcement sent", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Trophy order placed", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Water and Gatorade purchased", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Balls purchased", "Owner": "", "Done": False},
    {"Section": "Match Day", "Task": "Printouts ready (schedule, etc.)", "Owner": "", "Done": False},
    {"Section": "Match Day", "Task": "Confirm lunch with vendor", "Owner": "", "Done": False},
    {"Section": "Post-Tournament", "Task": "Ground cleanup organized", "Owner": "", "Done": False},
]

# Initialize with default tasks if checklist is empty
if not st.session_state.checklist_data:
    st.session_state.checklist_data = default_tasks

df = pd.DataFrame(st.session_state.checklist_data)

# Use st.data_editor for a modern, spreadsheet-like UI
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Section": st.column_config.SelectboxColumn(
            "Section",
            options=["Pre-Tournament", "Logistics", "Match Day", "Post-Tournament"],
            required=True,
        ),
        "Task": st.column_config.TextColumn("Task", required=True),
        "Owner": st.column_config.TextColumn("Owner"),
        "Done": st.column_config.CheckboxColumn("Done", default=False)
    },
    key="checklist_editor"
)

# When the user makes an edit, the whole app reruns. We save the new state.
if edited_df.to_dict('records') != st.session_state.checklist_data:
    st.session_state.checklist_data = edited_df.to_dict('records')
    save_tourney_data()
    st.toast("Checklist updated!")
    
# --- Progress Bar ---
st.markdown("---")
st.subheader("Overall Progress")
total_tasks = len(st.session_state.checklist_data)
completed_tasks = sum(1 for task in st.session_state.checklist_data if task.get('Done'))

if total_tasks > 0:
    progress = completed_tasks / total_tasks
    st.progress(progress, f"{completed_tasks} / {total_tasks} Tasks Completed")
    if progress == 1.0:
        st.success("🎉 All tasks are complete! Great job! 🎉")
        st.balloons()
else:
    st.info("Add some tasks to the checklist to see your progress.")