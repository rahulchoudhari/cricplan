import streamlit as st
import time
from pathlib import Path
import json

# --- Session check: block page if not logged in ---
if 'user_logged_in' not in st.session_state or not st.session_state['user_logged_in']:
    st.warning('You must be logged in to access this page.')
    st.stop()

DATA_FILE = "tournament_data.json"

DEFAULT_CHECKLISTS = {
    "Pre step": [
        {"Task": "Ground date 📆", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "flyer out", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Get Sponsor", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Google waiver forms", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Google team registration form", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Google lunch form", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Trophy order", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Match day logistic", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Tennis ball order", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Lunch confirmation", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Breakfast confirmation", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Identify misc item and order from amazon", "Task Owner": "", "Backup Owner": "", "Status": False}
    ],
    "Logistic match day": [
        {"Task": "water", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Banana", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Gatorade", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Printout", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Cooler", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Canopy", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Speaker", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Table", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Extension cord", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Banner", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Back drop", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Zip tie", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Glue tape", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Pen", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Ice", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Team stumps", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Reminder to vendors", "Task Owner": "", "Backup Owner": "", "Status": False}
    ],
    "Match day": [
        {"Task": "handover balls after confirming waiver", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Match preparation", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Lunch", "Task Owner": "", "Backup Owner": "", "Status": False}
    ],
    "Post match": [
        {"Task": "Cleanup dugout", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Return banner", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Return item if required", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Lost found claim", "Task Owner": "", "Backup Owner": "", "Status": False},
        {"Task": "Take your stuff", "Task Owner": "", "Backup Owner": "", "Status": False}
    ]
}

def migrate_checklists(data):
    # Migrate old format (list of strings or mixed) to new format (list of dicts)
    for section, default_items in DEFAULT_CHECKLISTS.items():
        items = data.get("checklists_items", {}).get(section, None)
        if items is not None:
            new_items = []
            for item in items:
                if isinstance(item, dict):
                    # Ensure all required keys exist
                    new_items.append({
                        "Task": item.get("Task", ""),
                        "Task Owner": item.get("Task Owner", ""),
                        "Backup Owner": item.get("Backup Owner", ""),
                        "Status": item.get("Status", False)
                    })
                elif isinstance(item, str):
                    new_items.append({
                        "Task": item,
                        "Task Owner": "",
                        "Backup Owner": "",
                        "Status": False
                    })
            data["checklists_items"][section] = new_items
    return data

def load_data():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    # Use saved checklists if present, else default
    checklists_items = data.get("checklists_items", DEFAULT_CHECKLISTS.copy())
    # Migrate if needed
    data["checklists_items"] = checklists_items
    data = migrate_checklists(data)
    # Ensure all sections exist and are lists
    for section, default_items in DEFAULT_CHECKLISTS.items():
        if section not in data["checklists_items"] or not isinstance(data["checklists_items"][section], list):
            data["checklists_items"][section] = default_items.copy()
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

st.set_page_config(page_title="📝 Match Checklists")
st.title("📝 Tournament Planning Checklists")

if st.button("Reset to Default Checklist", type="primary"):
    data = {"checklists_items": DEFAULT_CHECKLISTS.copy()}
    save_data(data)
    st.rerun()

data = load_data()

for section, items in data["checklists_items"].items():
    with st.expander(section, expanded=True):
        st.markdown("<style>th, td {padding: 0.25em 0.5em;}</style>", unsafe_allow_html=True)
        # Table header
        cols = st.columns([3, 2, 2, 1, 1])
        cols[0].markdown("**Task**")
        cols[1].markdown("**Task Owner**")
        cols[2].markdown("**Backup Owner**")
        cols[3].markdown("**Status**")
        cols[4].markdown("**Delete**")
        to_delete = []
        for i, item in enumerate(items):
            cols = st.columns([3, 2, 2, 1, 1])
            with cols[0]:
                task = st.text_input("", value=item["Task"], key=f"task_{section}_{i}")
            with cols[1]:
                owner = st.text_input("", value=item["Task Owner"], key=f"owner_{section}_{i}")
            with cols[2]:
                backup = st.text_input("", value=item["Backup Owner"], key=f"backup_{section}_{i}")
            with cols[3]:
                status = st.checkbox("", value=item["Status"], key=f"status_{section}_{i}")
            with cols[4]:
                if st.button("🗑️", key=f"delete_{section}_{i}"):
                    to_delete.append(i)
            # Update in-memory data
            data["checklists_items"][section][i]["Task"] = task
            data["checklists_items"][section][i]["Task Owner"] = owner
            data["checklists_items"][section][i]["Backup Owner"] = backup
            data["checklists_items"][section][i]["Status"] = status
        # Remove deleted items after loop
        for idx in sorted(to_delete, reverse=True):
            del data["checklists_items"][section][idx]
        # Add new item at end of section
        st.markdown("")
        st.markdown("**Add new item**")
        add_cols = st.columns([3, 2, 2, 1])
        new_task = add_cols[0].text_input(f"New Task for {section}", "", key=f"new_task_{section}")
        new_owner = add_cols[1].text_input(f"Task Owner for {section}", "", key=f"new_owner_{section}")
        new_backup = add_cols[2].text_input(f"Backup Owner for {section}", "", key=f"new_backup_{section}")
        if add_cols[3].button(f"Add", key=f"btn_add_{section}"):
            if new_task.strip():
                data["checklists_items"][section].append({
                    "Task": new_task.strip(),
                    "Task Owner": new_owner.strip(),
                    "Backup Owner": new_backup.strip(),
                    "Status": False
                })
                save_data(data)
                st.rerun()

save_data(data)
