# pages/8_✅_Preparation_Checklist.py
import streamlit as st
import pandas as pd

import sidebar
import ui
from utils import save_tourney_data

ui.inject_global_css()
sidebar.render()
ui.guard_organizer()

ui.page_header("Preparation Checklist", "Use this interactive table to track all tournament tasks.", "✅")
st.caption("Your edits are saved automatically.")

SECTION_ORDER = ["Pre-Tournament", "Logistics", "Match Day", "Post-Tournament"]

# Default tasks if the checklist is empty
default_tasks = [
    # Pre-Tournament
    {"Section": "Pre-Tournament", "Task": "Ground date 📆", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Flyer out", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Get sponsor", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Google waiver form", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Google team registration form", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Google lunch form", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Trophy order", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Match day logistics", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Tennis ball order", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Lunch confirmation", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Breakfast confirmation", "Owner": "", "Done": False},
    {"Section": "Pre-Tournament", "Task": "Identify misc items and order from Amazon", "Owner": "", "Done": False},
    # Logistics (match day)
    {"Section": "Logistics", "Task": "Water", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Banana", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Gatorade", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Printouts", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Cooler", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Canopy", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Speaker", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Table", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Extension cord", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Banner", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Backdrop", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Zip ties", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Glue tape", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Pens", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Ice", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Team stumps", "Owner": "", "Done": False},
    {"Section": "Logistics", "Task": "Reminder to vendors", "Owner": "", "Done": False},
    # Match Day
    {"Section": "Match Day", "Task": "Handover balls after confirming waiver", "Owner": "", "Done": False},
    {"Section": "Match Day", "Task": "Match preparation", "Owner": "", "Done": False},
    {"Section": "Match Day", "Task": "Lunch", "Owner": "", "Done": False},
    # Post-Tournament
    {"Section": "Post-Tournament", "Task": "Cleanup dugout", "Owner": "", "Done": False},
    {"Section": "Post-Tournament", "Task": "Return banner", "Owner": "", "Done": False},
    {"Section": "Post-Tournament", "Task": "Return items if required", "Owner": "", "Done": False},
    {"Section": "Post-Tournament", "Task": "Lost & found claims", "Owner": "", "Done": False},
    {"Section": "Post-Tournament", "Task": "Take your stuff", "Owner": "", "Done": False},
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
            options=SECTION_ORDER,
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

# --- Visual checklist: completed tasks highlighted in green ---
st.markdown("---")
st.subheader("Checklist Overview")
ui.checklist_by_section(st.session_state.checklist_data, SECTION_ORDER)

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