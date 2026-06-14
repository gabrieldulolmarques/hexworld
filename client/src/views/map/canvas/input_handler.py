from PyQt6.QtCore import Qt

from models.geometry import Coord
from views.map.canvas.pick_helper import PickHelper
from views.map.canvas.path_handler import PathHandler

class InputHandler:
    def __init__(self, canvas, pick: PickHelper) -> None:
        self._canvas = canvas
        self._pick = pick
        self._path_handler = PathHandler(canvas)

    # ------------------------------------------------------------------ events

    def wheel(self, event) -> None:
        from views.map.canvas.map_canvas import (
            _HEX_SIZE_MAX,
            _HEX_SIZE_MIN,
            _ZOOM_STEP,
        )

        delta = event.angleDelta().y()
        step = _ZOOM_STEP if delta > 0 else -_ZOOM_STEP
        self._canvas._hex_size = max(
            _HEX_SIZE_MIN, min(_HEX_SIZE_MAX, self._canvas._hex_size + step)
        )
        self._canvas.update()
        self._canvas._emit_viewport_changed()
        event.accept()

    def mouse_press(self, event) -> bool:
        pos = event.position()
        x, y = pos.x(), pos.y()

        if event.button() == Qt.MouseButton.LeftButton:
            if self._canvas._pan_mode:
                self._canvas._pan_anchor = (x, y, self._canvas._offset[0], self._canvas._offset[1])
                self._canvas.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True

            if self._canvas._path_mode and self._canvas._path_submode == "path":
                hit = self._pick.pick_hex(x, y)
                if hit is None:
                    return True
                self._path_handler.handle_hex_click(hit)
                self._canvas._hover = hit
                self._canvas.update()
                return True

            if self._canvas._path_mode and self._canvas._path_submode == "edge":
                edge = self._pick.pick_edge(x, y)
                if edge is None:
                    return True
                coord, edge_index = edge
                self._canvas._hover = coord
                self._canvas._hover_edge = edge
                self._canvas.edge_painted.emit(
                    coord[0], coord[1], edge_index, self._canvas._path_color
                )
                self._canvas.update()
                return True

            if self._canvas._brush_mode:
                self._canvas._brush_active = True
                self._canvas._brush_seen_targets.clear()
                self._apply_brush_at(x, y)
                return True

            desc_hit = (
                self._pick.pick_description_at_point(x, y)
                if self._canvas._erase_mode
                else None
            )
            path_hit = (
                self._pick.pick_path_id_at_point(x, y) if self._canvas._erase_mode else None
            )
            edge_hit = (
                self._pick.pick_painted_edge(x, y) if self._canvas._erase_mode else None
            )
            hit = self._pick.pick_hex(x, y)

            if self._canvas._erase_mode and desc_hit is not None:
                self._canvas._hover = desc_hit
                self._canvas._hover_path_id = None
                self._canvas._hover_edge = None
                self._canvas._hover_component = "description"
                self._canvas.update()
                self._canvas.hex_clicked.emit(desc_hit[0], desc_hit[1])
                return True
            if self._canvas._erase_mode and path_hit is not None:
                hit = hit or self._pick.canvas_to_hex(x, y)
                self._canvas._hover = hit
                self._canvas._hover_path_id = path_hit
                self._canvas._hover_component = "path"
                self._canvas.update()
                self._canvas.hex_clicked.emit(hit[0], hit[1])
                return True
            if self._canvas._erase_mode and edge_hit is not None:
                coord, _edge_index = edge_hit
                self._canvas._hover = coord
                self._canvas._hover_edge = edge_hit
                self._canvas._hover_component = "edge"
                self._canvas.update()
                self._canvas.hex_clicked.emit(coord[0], coord[1])
                return True
            if hit is None:
                if self._canvas._selected is not None:
                    self._canvas._selected = None
                    self._canvas.update()
                    self._canvas.hex_deselected.emit()
                return True
            if not self._canvas._pick_any_hex:
                if self._canvas._selected == hit:
                    self._canvas._selected = None
                    self._canvas.update()
                    self._canvas.hex_deselected.emit()
                    return True
                self._canvas._selected = hit
            self._canvas.update()
            self._canvas.hex_clicked.emit(hit[0], hit[1])
            return True

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._canvas._pan_anchor = (x, y, self._canvas._offset[0], self._canvas._offset[1])
            self._canvas.setCursor(Qt.CursorShape.SizeAllCursor)
            return True
        return False

    def mouse_move(self, event) -> None:
        pos = event.position()
        x, y = pos.x(), pos.y()

        if self._canvas._pan_anchor is not None:
            x0, y0, ox, oy = self._canvas._pan_anchor
            self._canvas._offset[0] = ox + (x - x0)
            self._canvas._offset[1] = oy + (y - y0)
            self._canvas._emit_viewport_changed()
            self._canvas.update()
            return

        if self._canvas._pan_mode:
            return

        hit = self._pick.pick_hex(x, y)
        needs_update = False
        if self._canvas._path_mode and self._canvas._path_submode == "edge":
            edge = self._pick.pick_edge(x, y)
            if edge is not None:
                hit = edge[0]
            if edge != self._canvas._hover_edge:
                self._canvas._hover_edge = edge
                needs_update = True

        if self._canvas._hover != hit:
            self._canvas._hover = hit
            needs_update = True

        if self._canvas._erase_mode:
            desc_hit = self._pick.pick_description_at_point(x, y)
            path_id = None
            edge = None
            if desc_hit is not None:
                comp = "description"
                hit = desc_hit
                if self._canvas._hover != hit:
                    self._canvas._hover = hit
                    needs_update = True
            else:
                path_id = self._pick.pick_path_id_at_point(x, y)
            if desc_hit is None and path_id is not None:
                comp = "path"
                if hit is None:
                    hit = self._pick.canvas_to_hex(x, y)
                    self._canvas._hover = hit
                    needs_update = True
            elif desc_hit is None:
                edge = self._pick.pick_painted_edge(x, y)
                if edge is not None:
                    comp = "edge"
                    hit = edge[0]
                    if self._canvas._hover != hit:
                        self._canvas._hover = hit
                        needs_update = True
                else:
                    comp = (
                        self._pick.pick_erase_component(x, y, *hit)
                        if hit is not None
                        else None
                    )
            if path_id != self._canvas._hover_path_id:
                self._canvas._hover_path_id = path_id
                needs_update = True
            if edge != self._canvas._hover_edge:
                self._canvas._hover_edge = edge
                needs_update = True
            if comp != self._canvas._hover_component:
                self._canvas._hover_component = comp
                needs_update = True

        if needs_update:
            self._canvas.update()
            if hit is not None and not self._canvas._erase_mode:
                self._canvas.hex_hovered.emit(hit[0], hit[1])
        if self._canvas._brush_active:
            self._apply_brush_at(x, y)

    def mouse_release(self, event) -> bool:
        if event.button() == Qt.MouseButton.LeftButton and self._canvas._brush_active:
            self._canvas._brush_active = False
            self._canvas._brush_seen_targets.clear()
            return True
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._canvas._pan_anchor is not None
        ):
            self._canvas._pan_anchor = None
            if self._canvas._pan_mode:
                self._canvas.setCursor(Qt.CursorShape.OpenHandCursor)
            elif self._canvas._path_mode:
                self._canvas.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self._canvas.unsetCursor()
            return True
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._canvas._pan_anchor = None
            if self._canvas._path_mode:
                self._canvas.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self._canvas.unsetCursor()
            return True
        return False

    def leave(self) -> None:
        self._canvas._brush_active = False
        self._canvas._brush_seen_targets.clear()
        if (
            self._canvas._hover is not None
            or self._canvas._hover_edge is not None
            or self._canvas._hover_path_id
        ):
            self._canvas._hover = None
            self._canvas._hover_component = None
            self._canvas._hover_path_id = None
            self._canvas._hover_edge = None
            self._canvas.update()

    def key_press(self, event) -> bool:
        if not self._canvas._current_path:
            return False
        if event.key() == Qt.Key.Key_Escape:
            self._canvas.cancel_current_path()
            event.accept()
            return True
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._canvas.finish_current_path()
            event.accept()
            return True
        if event.key() == Qt.Key.Key_Backspace:
            self._canvas.undo_current_path_point()
            event.accept()
            return True
        return False

    def can_continue_path_at(self, coord: Coord) -> bool:
        return self._path_handler.can_continue_at(coord)

    # --------------------------------------------------------- brush / erase

    def _apply_brush_at(self, cx: float, cy: float) -> None:
        if self._canvas._erase_mode:
            target = self._erase_target_at(cx, cy)
        else:
            coord = self._pick.pick_hex(cx, cy)
            target = (coord, ("paint", coord)) if coord is not None else None
            if coord is not None and self._canvas._hover != coord:
                self._canvas._hover = coord
                self._canvas.update()
        if target is None:
            return
        coord, target_key = target
        if target_key in self._canvas._brush_seen_targets:
            return
        self._canvas._brush_seen_targets.add(target_key)
        self._canvas.hex_clicked.emit(coord[0], coord[1])

    def _erase_target_at(self, cx: float, cy: float) -> tuple[Coord, tuple] | None:
        result = self._pick.find_erase_target(cx, cy)
        if result is None:
            self._set_erase_hover(None, None)
            return None
        coord, target_key = result
        if target_key is None:
            self._set_erase_hover(coord, None)
            return None
        comp = target_key[0]
        if comp == "path":
            self._set_erase_hover(coord, comp, path_id=target_key[1])
        elif comp == "edge":
            self._set_erase_hover(coord, comp, edge=(target_key[1], target_key[2]))
        else:
            self._set_erase_hover(coord, comp)
        return coord, target_key

    def _set_erase_hover(
        self,
        coord: Coord | None,
        component: str | None,
        *,
        path_id: str | None = None,
        edge: tuple[Coord, int] | None = None,
    ) -> None:
        changed = (
            self._canvas._hover != coord
            or self._canvas._hover_component != component
            or self._canvas._hover_path_id != path_id
            or self._canvas._hover_edge != edge
        )
        self._canvas._hover = coord
        self._canvas._hover_component = component
        self._canvas._hover_path_id = path_id
        self._canvas._hover_edge = edge
        if changed:
            self._canvas.update()
