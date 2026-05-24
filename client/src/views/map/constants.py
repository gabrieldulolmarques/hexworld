"""Constants shared across map-editor sub-widgets."""

PANEL_MARGIN = 12
PANEL_MIN_H = 200   # floor for side-panel max height (viewport − margins)
SIDE_PANEL_W = 400   # inspector + palette + road panel share this width
RIGHT_COLUMN_GAP = 12   # space between right tool panels and minimap
MINIMAP_H = 220

TOOL_SELECT      = "select"
TOOL_STRUCTURE   = "structure"
TOOL_ROAD        = "road"
TOOL_DESCRIPTION = "description"
TOOL_ERASE       = "erase"
TOOL_PAN         = "pan"

# Members bar: scroll from N users; cap growth inside the left overlay column
MEMBERS_SCROLL_THRESHOLD = 5
MEMBERS_VISIBLE_ROWS = 4
MEMBERS_ROW_H = 26
MEMBERS_ROW_GAP = 5
MEMBERS_BAR_MAX_W = 400   # cap horizontal growth (align with side panels)


def side_panel_max_height(viewport_h: int) -> int:
    """Shared vertical cap for floating side panels (inspector, palette, road)."""
    return max(PANEL_MIN_H, viewport_h - 2 * PANEL_MARGIN)
