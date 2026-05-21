"""Smoke test visual do MapView — roda sem servidor."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow
from styles.theme import STYLESHEET
from views.map_view import MapView

_FAKE_MAP = {
    "id":           "map-001",
    "name":         "Middle Earth",
    "role":         "editor",
    "member_count": 3,
    "created_at":   "2026-05-20 10:00:00",
}

_FAKE_TILES = {
    (0,  0): {},
    (1,  0): {"structure": {"type": "castle"}},
    (0,  1): {"structure": {"type": "village"}, "description": {"text": "A small village"}},
    (-1, 1): {"road": {"color": "#5ea500"}},
    (1, -1): {"structure": {"type": "fortress"}, "road": {"color": "#ef4444"}},
    (-1, 0): {"structure": {"type": "ruins"}},
    (0, -1): {"structure": {"type": "port"}},
    (2,  0): {},
    (2, -1): {"structure": {"type": "tower"}},
    (-2, 1): {},
    (0,  2): {"road": {"color": "#3b82f6"}, "description": {"text": "crossroads"}},
}


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    view = MapView()
    view.set_map(_FAKE_MAP)
    view.set_tiles(_FAKE_TILES)
    view.set_online_users([
        {"username": "alice", "role": "owner"},
        {"username": "bob",   "role": "editor"},
        {"username": "carol", "role": "viewer"},
    ])
    view.hex_selected.connect(lambda q, r: print(f"selected ({q}, {r})"))
    view.tool_changed.connect(lambda t: print(f"tool: {t}"))
    view.structure_selected.connect(lambda s: print(f"structure: {s}"))
    view.road_color_selected.connect(lambda c: print(f"road color: {c}"))
    view.request_back.connect(lambda: print("← back"))
    view.zoom_in_requested.connect(lambda: print("zoom in"))
    view.zoom_out_requested.connect(lambda: print("zoom out"))
    view.undo_requested.connect(lambda: print("undo"))
    view.redo_requested.connect(lambda: print("redo"))
    view.export_requested.connect(lambda: print("export"))

    win = QMainWindow()
    win.setWindowTitle("MapView — smoke test")
    win.resize(1280, 800)
    win.setCentralWidget(view)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
