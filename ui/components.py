"""UI components for PDF rendering, preview, and page navigation."""

import fitz  # PyMuPDF
import streamlit as st
from ui.state import undo_last_edit


def render_pdf_page_as_image(pdf_bytes: bytes, page_number: int = 0, dpi: int = 150):
    """Renders a specific PDF page from memory into PNG image bytes."""
    if not pdf_bytes:
        return None, 0

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)

    if total_pages == 0:
        doc.close()
        return None, 0

    if page_number >= total_pages or page_number < 0:
        page_number = 0

    page = doc[page_number]
    # Render with 150 DPI for crisp reading in browser
    pix = page.get_pixmap(dpi=dpi)
    img_bytes = pix.tobytes("png")
    doc.close()

    return img_bytes, total_pages


def render_navigation_bar(total_pages: int):
    """Renders page selection and undo controls."""
    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])

    with col2:
        selected_page = st.number_input(
            f"Page Navigation (Total: {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.current_page + 1,
            step=1,
        )
        st.session_state.current_page = selected_page - 1

    with col4:
        st.write("")
        st.write("")  # Vertical spacing for vertical alignment with input
        can_undo = len(st.session_state.history) > 0
        if st.button("↩ Undo Edit", disabled=not can_undo, use_container_width=True):
            if undo_last_edit():
                st.toast("Reverted last change!", icon="↩")
                st.rerun()


def render_comparison_view():
    """Displays original and edited resume side-by-side."""
    if not st.session_state.original_pdf_bytes:
        st.info("Upload a resume PDF from the sidebar to start editing.")
        return

    # Render images for the active page
    orig_img, total_pages = render_pdf_page_as_image(
        st.session_state.original_pdf_bytes, st.session_state.current_page
    )
    edit_img, _ = render_pdf_page_as_image(
        st.session_state.edited_pdf_bytes, st.session_state.current_page
    )

    if total_pages > 1:
        render_navigation_bar(total_pages)
        st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📄 Original Resume")
        if orig_img:
            st.image(orig_img, use_container_width=True)

    with col_right:
        st.subheader("✏️ Edited Resume")
        if edit_img:
            st.image(edit_img, use_container_width=True)

            # Export download button
            out_filename = f"edited_{st.session_state.file_name}"
            st.download_button(
                label=f"💾 Download {out_filename}",
                data=st.session_state.edited_pdf_bytes,
                file_name=out_filename,
                mime="application/pdf",
                use_container_width=True,
            )