"""Visible, non-executing representations for the new context previews."""

import unicodedata


def preview_text(text):
    """Keep readable Unicode/newlines, escaping backslashes and hidden controls.

    This is a display representation only, not input sanitization or a
    guarantee that source claims or model instructions are safe.
    """
    parts = []
    for character in text:
        if character == "\\":
            parts.append("\\\\")
        elif character != "\n" and unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}:
            value = ord(character)
            parts.append(f"\\u{value:04x}" if value <= 0xFFFF else f"\\U{value:08x}")
        else:
            parts.append(character)
    return "".join(parts)
