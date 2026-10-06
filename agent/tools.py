"""Tool schemas and operational wrappers for the Groq PDF Agent."""

from typing import Any, Dict, List, Tuple
from core.inspector import inspect_resume_links, inspect_resume_text
from core.mutator import replace_text_in_resume, update_hyperlink_uri_only

# Tool specifications conforming to OpenAI / Groq tool-calling format
RESUME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_resume_text",
            "description": (
                "Search the resume PDF for a target text string. Returns bounding box "
                "coordinates, page number, font name, size, bold/italic flags, and color."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "search_text": {
                        "type": "string",
                        "description": "The exact word, phrase, or number to find in the resume.",
                    },
                    "page_number": {
                        "type": "integer",
                        "description": "Optional 0-indexed page number to restrict the search.",
                    },
                },
                "required": ["search_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_resume_links",
            "description": (
                "Scans the resume for clickable hyperlink annotations (URIs like LinkedIn, "
                "GitHub, email, or personal portfolio) and their bounding boxes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_number": {
                        "type": "integer",
                        "description": "Optional 0-indexed page number to restrict search.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_resume_text",
            "description": (
                "Redacts the original text bounding box and re-stamps new text using the exact "
                "matched typography (font, size, weight, color). Can also attach a new clickable URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_number": {"type": "integer", "description": "0-indexed page number."},
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Bounding box [x0, y0, x1, y1] retrieved from inspect_resume_text.",
                    },
                    "original_text": {"type": "string", "description": "Original text being replaced."},
                    "new_text": {"type": "string", "description": "New replacement text to stamp."},
                    "font_name": {"type": "string", "description": "Font name from inspect_resume_text."},
                    "font_size": {"type": "number", "description": "Font size from inspect_resume_text."},
                    "is_bold": {"type": "boolean", "description": "Bold flag from inspection."},
                    "is_italic": {"type": "boolean", "description": "Italic flag from inspection."},
                    "raw_color": {"type": "integer", "description": "Color integer from inspection."},
                    "new_url": {
                        "type": "string",
                        "description": "Optional new clickable hyperlink URL (e.g., https://github.com/user).",
                    },
                },
                "required": [
                    "page_number",
                    "bbox",
                    "original_text",
                    "new_text",
                    "font_name",
                    "font_size",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_link_destination_only",
            "description": (
                "Updates the clickable URL destination of an existing link without modifying "
                "the visible text on the resume."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_number": {"type": "integer", "description": "0-indexed page number."},
                    "old_url": {"type": "string", "description": "Part or full original destination URL."},
                    "new_url": {"type": "string", "description": "Complete new destination URL."},
                },
                "required": ["page_number", "old_url", "new_url"],
            },
        },
    },
]


def execute_tool_call(
    tool_name: str, arguments: Dict[str, Any], current_pdf_bytes: bytes
) -> Tuple[Any, bytes]:
    """
    Executes a requested tool call against the active PDF bytes.
    Returns: (tool_output_result, possibly_updated_pdf_bytes)
    """
    updated_bytes = current_pdf_bytes

    if tool_name == "inspect_resume_text":
        result = inspect_resume_text(
            pdf_bytes=current_pdf_bytes,
            search_text=arguments.get("search_text", ""),
            page_number=arguments.get("page_number"),
        )
        return result, updated_bytes

    elif tool_name == "inspect_resume_links":
        result = inspect_resume_links(
            pdf_bytes=current_pdf_bytes,
            page_number=arguments.get("page_number"),
        )
        return result, updated_bytes

    elif tool_name == "replace_resume_text":
        updated_bytes = replace_text_in_resume(
            pdf_bytes=current_pdf_bytes,
            page_number=arguments["page_number"],
            bbox=arguments["bbox"],
            original_text=arguments["original_text"],
            new_text=arguments["new_text"],
            font_name=arguments["font_name"],
            font_size=arguments["font_size"],
            is_bold=arguments.get("is_bold", False),
            is_italic=arguments.get("is_italic", False),
            raw_color=arguments.get("raw_color", 0),
            new_url=arguments.get("new_url"),
        )
        return {"status": "success", "message": f"Replaced with '{arguments['new_text']}'"}, updated_bytes

    elif tool_name == "update_link_destination_only":
        updated_bytes = update_hyperlink_uri_only(
            pdf_bytes=current_pdf_bytes,
            page_number=arguments["page_number"],
            old_url=arguments["old_url"],
            new_url=arguments["new_url"],
        )
        return {"status": "success", "message": f"Updated link target to '{arguments['new_url']}'"}, updated_bytes

    return {"error": f"Unknown tool: {tool_name}"}, updated_bytes