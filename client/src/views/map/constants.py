"""Constants shared across map-editor sub-widgets."""

PANEL_MARGIN = 12
SIDE_PANEL_W = 400   # inspector + palette + road panel share this width

TOOL_SELECT      = "select"
TOOL_STRUCTURE   = "structure"
TOOL_ROAD        = "road"
TOOL_DESCRIPTION = "description"
TOOL_ERASE       = "erase"
TOOL_PAN         = "pan"

# Members bar (bottom-left): scroll from N users; cap growth at tool strip
MEMBERS_SCROLL_THRESHOLD = 5
MEMBERS_VISIBLE_ROWS = 4
MEMBERS_ROW_H = 28
MEMBERS_ROW_GAP = 6
MEMBERS_PANEL_GAP = 8   # min space between members card top and tool strip bottom
MEMBERS_BAR_MAX_W = 400   # cap horizontal growth (align with side panels)
