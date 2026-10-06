"""PDF inspection engine to extract text coordinates, typography metadata, and hyperlinks."""

from typing import Any, Dict, List, Optional
import fitz  # PyMuPDF


def inspect_resume_text(
    pdf_bytes: bytes, search_text: str, page_number: Optional[int] = None
) -> List[Dict[str, Any]]:
  """Searches for occurrences of search_text in the PDF and returns exact bounding

  boxes, line baselines, and typography details (font name, size, flags, color).
  """
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")
  matches = []

  pages_to_scan = (
      [page_number]
      if page_number is not None and 0 <= page_number < len(doc)
      else range(len(doc))
  )

  for p_num in pages_to_scan:
    page = doc[p_num]
    # Extract structural layout dictionary
    page_dict = page.get_text("dict")

    for block in page_dict.get("blocks", []):
      if "lines" not in block:
        continue

      for line in block["lines"]:
        for span in line["spans"]:
          span_text = span.get("text", "")

          if search_text.lower() in span_text.lower():
            # Extract color (integer or tuple)
            raw_color = span.get("color", 0)

            # Font flags: 2^0=superscript, 2^1=italic, 2^2=serifed, 2^3=monospaced, 2^4=bold
            flags = span.get("flags", 0)
            is_bold = bool(flags & 2**4)
            is_italic = bool(flags & 2**1)

            matches.append({
                "page": p_num,
                "found_text": span_text,
                "bbox": [round(coord, 2) for coord in span.get("bbox", [])],
                "origin": [round(coord, 2) for coord in span.get("origin", [])],
                "font": span.get("font", "Helvetica"),
                "size": round(span.get("size", 10.0), 2),
                "is_bold": is_bold,
                "is_italic": is_italic,
                "color": raw_color,
                "flags": flags,
            })

  doc.close()
  return matches


def inspect_resume_links(
    pdf_bytes: bytes, page_number: Optional[int] = None
) -> List[Dict[str, Any]]:
  """Scans clickable link annotations across the PDF to locate their bounding

  boxes and destination URIs (LinkedIn, GitHub, email, portfolio).
  """
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")
  extracted_links = []

  pages_to_scan = (
      [page_number]
      if page_number is not None and 0 <= page_number < len(doc)
      else range(len(doc))
  )

  for p_num in pages_to_scan:
    page = doc[p_num]
    links = page.get_links()

    for link in links:
      if link.get("kind") == fitz.LINK_URI:
        rect = link.get("from")
        extracted_links.append({
            "page": p_num,
            "uri": link.get("uri", ""),
            "bbox": [
                round(rect.x0, 2),
                round(rect.y0, 2),
                round(rect.x1, 2),
                round(rect.y1, 2),
            ],
        })

  doc.close()
  return extracted_links


def get_resume_overview(pdf_bytes: bytes) -> Dict[str, Any]:
  """Provides quick summary metadata of the resume for the agent."""
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")
  overview = {
      "total_pages": len(doc),
      "pages_text_sample": {},
  }

  for i in range(len(doc)):
    # Grab first 400 characters of each page for fast agent context
    overview["pages_text_sample"][f"page_{i+1}"] = doc[i].get_text("text")[
        :400
    ]

  doc.close()
  return overview