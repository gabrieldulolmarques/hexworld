"""Constants shared across map-editor sub-widgets."""

PANEL_MARGIN = 12
SIDE_PANEL_W = 400   # inspector + palette + road panel share this width

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
