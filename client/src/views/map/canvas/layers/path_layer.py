from models.geometry import Coord, hex_to_pixel
from models.map.local_map_state import LocalMapState
from models.path_style import PathStyle, paint_pixel_segments, path_style
from styles.colors import RED_PRIMARY
from views.map.canvas.layers.paint_context import PaintContext

def segments_from_waypoints(waypoints: list[Coord]) -> list[tuple[Coord, Coord]]:
    return [
        (start, end) for start, end in zip(waypoints, waypoints[1:]) if start != end
    ]

def path_waypoints(path: dict) -> list[Coord]:
    return [(int(waypoint[0]), int(waypoint[1])) for waypoint in path.get("waypoints", [])]

def path_segments(path: dict) -> list[tuple[str, Coord, Coord]]:
    path_id = path.get("id", "")
    return [
        (path_id, start, end)
        for start, end in segments_from_waypoints(path_waypoints(path))
    ]

def _path_state(paths: list[dict]) -> LocalMapState:
    state = LocalMapState()
    state.set_paths(paths)
    return state

class PathLayer:
    def paint(self, ctx: PaintContext) -> None:
        state = _path_state(ctx.paths)

        for color, segments in state.path_segments_by_color().items():
            self._paint_segments(ctx, segments, color)

        if (
            ctx.include_transient
            and ctx.erase_mode
            and ctx.hover_component == "path"
            and ctx.hover_path_id
        ):
            hover_segments = state.path_segments_for_id(ctx.hover_path_id)
            if hover_segments:
                self._paint_segments(
                    ctx,
                    hover_segments,
                    RED_PRIMARY,
                    highlight=True,
                )

        if (
            ctx.include_transient
            and ctx.path_mode
            and ctx.path_submode == "path"
            and len(ctx.path_preview) >= 2
        ):
            self._paint_segments(
                ctx,
                segments_from_waypoints(ctx.path_preview),
                ctx.path_color,
                preview=True,
            )

    @staticmethod
    def _paint_segments(
        ctx: PaintContext,
        segments: list[tuple[Coord, Coord]],
        color: str,
        *,
        preview: bool = False,
        highlight: bool = False,
    ) -> None:
        pixel_segments = [
            (
                hex_to_pixel(start[0], start[1], ctx.hex_size),
                hex_to_pixel(end[0], end[1], ctx.hex_size),
            )
            for start, end in segments
        ]
        paint_pixel_segments(
            ctx.painter,
            ctx.origin,
            pixel_segments,
            ctx.hex_size,
            PathStyle(color=color) if highlight else path_style(color),
            preview=preview,
            highlight=highlight,
        )
