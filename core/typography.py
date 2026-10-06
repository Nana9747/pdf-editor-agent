"""Typography and styling engine to resolve fonts, weights, and colors for seamless resume editing."""

from typing import Tuple


# Standard 14 PDF Base Fonts supported natively by all PDF readers
STANDARD_PDF_FONTS = {
    # Sans-serif (Calibri, Arial, Helvetica, Trebuchet, Inter)
    "sans": {
        "regular": "helv",
        "bold": "hebo",
        "italic": "heit",
        "bold_italic": "hebi",
    },
    # Serif (Times New Roman, Garamond, Georgia, LaTeX Computer Modern)
    "serif": {
        "regular": "tiro",
        "bold": "tibo",
        "italic": "tiit",
        "bold_italic": "tibi",
    },
    # Monospace (Courier, Consolas, Source Code Pro)
    "mono": {
        "regular": "cour",
        "bold": "cobo",
        "italic": "coit",
        "bold_italic": "cobi",
    },
}


def resolve_pdf_font(font_name: str, is_bold: bool = False, is_italic: bool = False) -> str:
    """
    Maps an extracted PDF font name and style flags to a native standard PDF font.
    Guarantees crisp rendering without font file dependency errors.
    """
    font_lower = font_name.lower()

    # Detect family classification
    if any(k in font_lower for k in ["times", "serif", "cmr", "georgia", "garamond", "roman"]):
        family = "serif"
    elif any(k in font_lower for k in ["courier", "mono", "consolas", "code"]):
        family = "mono"
    else:
        # Default for modern resumes (Calibri, Arial, Helvetica, Roboto, Inter)
        family = "sans"

    # Detect weight and slant from name if flags didn't capture them
    if not is_bold and any(k in font_lower for k in ["bold", "heavy", "black", "cmbx"]):
        is_bold = True
    if not is_italic and any(k in font_lower for k in ["italic", "oblique", "slanted"]):
        is_italic = True

    # Resolve to exact Base-14 symbol
    if is_bold and is_italic:
        return STANDARD_PDF_FONTS[family]["bold_italic"]
    elif is_bold:
        return STANDARD_PDF_FONTS[family]["bold"]
    elif is_italic:
        return STANDARD_PDF_FONTS[family]["italic"]
    else:
        return STANDARD_PDF_FONTS[family]["regular"]


def normalize_color(raw_color: int) -> Tuple[float, float, float]:
    """
    Converts PyMuPDF's 24-bit integer color or RGB representation
    into an (r, g, b) float tuple in the 0.0 - 1.0 range.
    """
    if isinstance(raw_color, (list, tuple)):
        if len(raw_color) == 3:
            return tuple(c / 255.0 if c > 1.0 else float(c) for c in raw_color)
        return (0.0, 0.0, 0.0)

    if isinstance(raw_color, int):
        # Unpack 24-bit RGB integer (0xRRGGBB)
        r = ((raw_color >> 16) & 0xFF) / 255.0
        g = ((raw_color >> 8) & 0xFF) / 255.0
        b = (raw_color & 0xFF) / 255.0
        return (r, g, b)

    return (0.0, 0.0, 0.0)


def calculate_adjusted_font_size(
    original_bbox: list,
    original_text: str,
    new_text: str,
    original_size: float,
) -> float:
    """
    Adjusts font size dynamically if the replacement text is longer than original,
    preventing overflow into adjacent columns or page margins.
    """
    if len(new_text) <= len(original_text) or len(original_text) == 0:
        return original_size

    # Ratio-based gentle scaling with a floor of 80% original size
    length_ratio = len(original_text) / len(new_text)
    adjusted_size = original_size * (0.85 + 0.15 * length_ratio)
    return round(max(adjusted_size, original_size * 0.8), 2)