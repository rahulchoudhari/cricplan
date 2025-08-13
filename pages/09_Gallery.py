import streamlit as st
import json
from pathlib import Path
import time

GALLERY_FILE = "gallery.json"

st.set_page_config(page_title="🏏 Tournament Gallery")
st.title("🏏 Tournament Gallery")

# Load gallery data
def load_gallery():
    if Path(GALLERY_FILE).exists():
        with open(GALLERY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_gallery(gallery):
    with open(GALLERY_FILE, "w") as f:
        json.dump(gallery, f, indent=4)

gallery = load_gallery()

st.markdown("""
Share your tournament's success! Upload a team photo, group photo, or action shot and a short description. Your entry will be shown in the gallery for all users to see.
""")

# Add comment to a gallery entry
def add_comment(gallery, idx, commenter, comment):
    if "comments" not in gallery[idx]:
        gallery[idx]["comments"] = []
    gallery[idx]["comments"].append({"commenter": commenter, "comment": comment, "timestamp": time.time()})
    save_gallery(gallery)

st.markdown("---")
st.header("Gallery")

# --- Slideshow of all gallery images at the top ---
all_images = []
for entry in gallery:
    paths = entry.get("image_paths") or ([entry["image_path"]] if "image_path" in entry else [])
    for p in paths:
        if Path(p).exists():
            all_images.append(p)
if all_images:
    st.markdown("<h3 style='text-align:center;'>Gallery Slideshow</h3>", unsafe_allow_html=True)
    slide_key = "main_gallery_slideshow"
    if slide_key not in st.session_state:
        st.session_state[slide_key] = 0
    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        if st.button("⬅️", key="main_prev_img"):
            st.session_state[slide_key] = (st.session_state[slide_key] - 1) % len(all_images)
    with col2:
        st.image(all_images[st.session_state[slide_key]], use_container_width=True)
    with col3:
        if st.button("➡️", key="main_next_img"):
            st.session_state[slide_key] = (st.session_state[slide_key] + 1) % len(all_images)
    st.markdown("---")

# Show gallery entries and comments (if any) at the top
show_gallery = False
if gallery:
    show_gallery = True
    for idx, entry in enumerate(reversed(gallery)):
        real_idx = len(gallery) - 1 - idx  # To update correct index in original list
        st.subheader(entry["team_name"])
        st.write(entry["description"])
        # Slideshow for multiple images
        image_paths = entry.get("image_paths") or ([entry["image_path"]] if "image_path" in entry else [])
        if image_paths:
            if len(image_paths) == 1:
                if Path(image_paths[0]).exists():
                    st.image(image_paths[0], use_container_width=True)
            else:
                img_key = f"slideshow_{real_idx}"
                if img_key not in st.session_state:
                    st.session_state[img_key] = 0
                st.image(image_paths[st.session_state[img_key]], use_container_width=True)
                # Remove auto-advance and rerun for now to avoid breaking forms
        # Show comments
        comments = entry.get("comments", [])
        if comments:
            st.markdown("**Comments:**")
            for c in comments:
                commenter = c.get("commenter", "Anonymous")
                comment = c.get("comment", "")
                ts = time.strftime('%Y-%m-%d %H:%M', time.localtime(c.get("timestamp", 0)))
                st.markdown(f"- *{commenter}* ({ts}): {comment}")
        # Add comment form
        with st.form(f"comment_form_{real_idx}", clear_on_submit=True):
            commenter = st.text_input("Your Name (optional)", key=f"commenter_{real_idx}")
            comment = st.text_area("Add a comment", key=f"comment_{real_idx}")
            submit_comment = st.form_submit_button("Post Comment")
            if submit_comment and comment.strip():
                add_comment(gallery, real_idx, commenter if commenter.strip() else "Anonymous", comment.strip())
                st.success("Comment added!")
                st.rerun()
        st.markdown("---")
if not show_gallery:
    st.info("No gallery entries yet. Be the first to add your tournament photo!")

# Add photo upload form at the bottom (always visible)
st.markdown("---")
st.subheader("Add Your Tournament Photos")
st.markdown("Share your tournament's success! Upload a team photo, group photo, or action shot and a short description. Your entry will be shown in the gallery for all users to see.")
with st.form("add_gallery_entry"):
    team_name = st.text_input("Team/Organizer Name", key="upload_team_name")
    description = st.text_area("Description (e.g., event, year, or special note)", key="upload_description")
    images = st.file_uploader("Upload one or more photos (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="upload_images")
    submitted = st.form_submit_button("Add to Gallery")
    if submitted and team_name and images:
        img_folder = Path("gallery_images")
        img_folder.mkdir(exist_ok=True)
        img_paths = []
        for image in images:
            img_path = img_folder / f"{team_name.replace(' ', '_')}_{image.name}"
            with open(img_path, "wb") as f:
                f.write(image.read())
            img_paths.append(str(img_path))
        gallery.append({
            "team_name": team_name,
            "description": description,
            "image_paths": img_paths
        })
        save_gallery(gallery)
        st.success("Photos added to gallery!")
        st.rerun()
