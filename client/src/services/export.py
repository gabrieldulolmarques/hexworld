from pathlib import Path

from PyQt6.QtGui import QImage

def default_filename(map_name: str) -> str:
    name = map_name.strip() or "hexworld-map"
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in name)
    safe = "-".join(part for part in safe.split("-") if part)
    return f"{safe or 'hexworld-map'}.png"

def normalize_path(path: Path) -> Path:
    if path.suffix.lower() == ".png":
        return path
    if path.suffix:
        return Path(f"{path}.png")
    return path.with_suffix(".png")

def save_image(image: QImage, path: Path) -> bool:
    if image.isNull():
        return False
    return image.save(str(path), "PNG")
