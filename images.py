# images.py
"""Upload handling for sponsor logos and tournament flyers.

Images are normalized to PNG and downscaled, then stored as base64 text in
the database (see db.py) rather than saved to disk — Streamlit Community
Cloud's filesystem doesn't persist across restarts, so anything that needs
to survive has to go through the same DB-backed path as everything else.
"""
import base64
import io

from PIL import Image

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class UploadTooLarge(ValueError):
    pass


def process_upload(uploaded_file, max_dim: int = 700) -> str:
    """Return a base64-encoded PNG data string for an st.file_uploader result."""
    raw = uploaded_file.getvalue()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise UploadTooLarge(f"Image is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.")

    img = Image.open(io.BytesIO(raw))
    img = img.convert("RGBA") if img.mode not in ("RGB", "RGBA") else img
    img.thumbnail((max_dim, max_dim))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def data_uri(base64_png: str) -> str:
    return f"data:image/png;base64,{base64_png}"
