"""PDF mutation engine: in-place redaction, matched font re-stamping, and hyperlink updating."""

from typing import Optional
import fitz  # PyMuPDF
from core.typography import (
    calculate_adjusted_font_size,
    normalize_color,
    resolve_pdf_font,
)


def replace_text_in_resume(
    pdf_bytes: bytes,
    page_number: int,
    bbox: list,
    original_text: str,
    new_text: str,
    font_name: str,
    font_size: float,
    is_bold: bool = False,
    is_italic: bool = False,
    raw_color: int = 0,
    new_url: Optional[str] = None,
) -> bytes:
  """Redacts old text box, stamps new text with matched typography,

  and optionally creates/updates the clickable hyperlink annotation.
  """
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")

  if page_number < 0 or page_number >= len(doc):
    doc.close()
    return pdf_bytes

  page = doc[page_number]
  rect = fitz.Rect(bbox)

  # 1. Cleanly redact the original bounding area
  page.add_redact_annot(rect, fill=(1, 1, 1))
  page.apply_redactions()

  # 2. Resolve typography & styling
  resolved_font = resolve_pdf_font(font_name, is_bold, is_italic)
  adjusted_size = calculate_adjusted_font_size(
      bbox, original_text, new_text, font_size
  )
  text_color = normalize_color(raw_color)

  # 3. Calculate baseline point (slightly above bottom of bbox for vertical alignment)
  # In PDF coordinate space, y increases downward.
  baseline_y = rect.y1 - (rect.height * 0.15)
  stamp_origin = fitz.Point(rect.x0, baseline_y)

  # 4. Stamp replacement text with matched styling
  page.insert_text(
      stamp_origin,
      new_text,
      fontname=resolved_font,
      fontsize=adjusted_size,
      color=text_color,
  )

  # 5. Handle Interactive Hyperlink Annotation (if URL provided or previously existing)
  if new_url:
    # Delete any existing link annotation overlapping the old rectangle
    existing_links = page.get_links()
    for link in existing_links:
      link_rect = link.get("from")
      if link_rect and rect.intersects(link_rect):
        page.delete_link(link)

    # Estimate new bounding box width for link hit area based on new text length
    char_width_approx = adjusted_size * 0.52
    new_width = max(rect.width, len(new_text) * char_width_approx)
    new_link_rect = fitz.Rect(rect.x0, rect.y0, rect.x0 + new_width, rect.y1)

    # Insert fresh URI link annotation
    page.insert_link({
        "kind": fitz.LINK_URI,
        "from": new_link_rect,
        "uri": new_url,
    })

  # Export updated PDF bytes
  output_bytes = doc.tobytes(garbage=4, deflate=True)
  doc.close()
  return output_bytes


def update_hyperlink_uri_only(
    pdf_bytes: bytes, page_number: int, old_url: str, new_url: str
) -> bytes:
  """Updates only the underlying destination URI of a link without touching the visible text."""
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")

  if page_number < 0 or page_number >= len(doc):
    doc.close()
    return pdf_bytes

  page = doc[page_number]
  links = page.get_links()

  for link in links:
    if (
        link.get("kind") == fitz.LINK_URI
        and old_url.lower() in link.get("uri", "").lower()
    ):
      link_rect = link.get("from")
      page.delete_link(link)
      page.insert_link({
          "kind": fitz.LINK_URI,
          "from": link_rect,
          "uri": new_url,
      })

  output_bytes = doc.tobytes(garbage=4, deflate=True)
  doc.close()
  return output_bytes