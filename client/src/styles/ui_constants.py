"""Design tokens shared across HexWorld UI (buttons, labels, layout)."""

# Toolbar / navigation actions (home top bar, map open/close, form primary)
BTN_TOOLBAR_W = 120
BTN_TOOLBAR_H = 46

# Secondary actions on cards and form cancel rows
BTN_COMPACT_W = 100
BTN_COMPACT_H = 40

# QSS object names (must match _base.qss)
BTN_PRIMARY = "primary"
BTN_SECONDARY = "secondary"
BTN_GHOST = "ghost"
BTN_GHOST_COMPACT = "ghostCompact"
BTN_DANGER = "danger"
BTN_DANGER_COMPACT = "dangerCompact"
BTN_ACCENT = "accent"               # 120×46 — Close Map (members bar)
BTN_ACCENT_COMPACT = "accentCompact"  # 100×40 — share page, etc.
BTN_MAP_CARD_OPEN = "mapCardOpen"
BTN_MAP_CARD_GHOST = "mapCardGhost"
BTN_MAP_CARD_DANGER = "mapCardDanger"

# Map ↔ home navigation (paired labels, like Create Map / Join Map)
LABEL_OPEN_MAP = "Open Map"
LABEL_CLOSE_MAP = "Close Map"

# Form / auth card width (login, register, create, join, share)
CARD_WIDTH = 360

# Map list card width (home grid; 3 columns wide)
MAP_CARD_WIDTH = 360
MAP_CARD_MARGIN_H = 16
MAP_CARD_ACTION_GAP = 6

# Form card inner margins (auth, home create/join/share)
CARD_MARGINS = (32, 22, 32, 28)
CARD_SPACING = 10
