"""Format hex inspector labels from canvas / server payloads."""
from __future__ import annotations

from datetime import datetime

from models.asset_registry import REGISTRY

# Flat-top axial edge indices (geometry._AXIAL_DIRECTIONS order).
_EDGE_LABELS = ("E", "SE", "SW", "W", "NW", "NE")


def structure_display(stem: str) -> tuple[str, str]:
    """Return (title, biome subtitle) for a structure.type stem."""
    info = REGISTRY.tile(stem)
    if info:
        biome = info.biome.replace("_", " ").title()
        return info.label, biome
    title = stem.replace("_", " ").title()
    return title, ""


def inner_edge_summary(edges_mask: int) -> tuple[int, str]:
    """Return (count, comma-separated direction labels) for a 6-bit mask."""
    dirs = [label for i, label in enumerate(_EDGE_LABELS) if edges_mask & (1 << i)]
    return len(dirs), ", ".join(dirs) if dirs else "—"


def format_timestamp(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return raw


def format_date_friendly(raw: str) -> str:
    """Human-readable date for inspector summaries."""
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y · %H:%M")
    except ValueError:
        return raw


def format_tile_record_lines(created_at: str, updated_at: str) -> list[str]:
    """Short, friendly copy for the server tile timeline."""
    created = format_date_friendly(created_at)
    updated = format_date_friendly(updated_at)
    if created and updated and created != updated:
        return [f"First saved {created}", f"Last updated {updated}"]
    if updated:
        return [f"Saved {updated}"]
    if created:
        return [f"Saved {created}"]
    return []


def format_component_meta(
    *,
    author: str = "",
    created_at: str = "",
    updated_at: str = "",
) -> str:
    """Single-line footer: author plus created/updated when present."""
    parts: list[str] = []
    if author:
        parts.append(f"by {author}")
    created = format_timestamp(created_at)
    updated = format_timestamp(updated_at)
    if created:
        parts.append(f"created {created}")
    if updated and updated != created:
        parts.append(f"updated {updated}")
    return " · ".join(parts)


def format_editor_meta(
    *,
    author: str = "",
    created_at: str = "",
    updated_at: str = "",
) -> str:
    """Inspector-friendly: ``user1 · last edited 24 May 2026 · 19:12``."""
    parts: list[str] = []
    if author:
        parts.append(author)
    created = format_date_friendly(created_at)
    updated = format_date_friendly(updated_at)
    if updated and created and updated != created:
        parts.append(f"last edited {updated}")
    elif updated:
        parts.append(f"saved {updated}")
    elif created:
        parts.append(f"saved {created}")
    return " · ".join(parts)
