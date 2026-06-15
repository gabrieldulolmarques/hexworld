from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QTextBrowser, QVBoxLayout

from models.inspector_format import format_editor_meta
from styles.colors import GREEN_PRIMARY

_DESC_MIN_HEIGHT = 180

_INSPECTOR_MARKDOWN_CSS = f"""
body, p, div, span, li, td, th, em, i {{
    color: #ffffff;
    font-size: 15px;
    line-height: 1.45;
}}
body {{ margin: 0; }}
p {{ margin: 6px 0; }}
h1, h2, h3 {{ color: #ffffff; margin: 12px 0 6px; font-weight: 600; }}
h1 {{ font-size: 1.35em; }}
h2 {{ font-size: 1.2em; }}
h3 {{ font-size: 1.05em; }}
ul, ol {{ margin: 6px 0; padding-left: 1.4em; }}
li {{ margin: 3px 0; }}
code, pre {{ color: #ffffff; background: #27272a; }}
code {{ padding: 1px 5px; border-radius: 4px; font-size: 0.92em; }}
pre {{ padding: 10px; border-radius: 6px; overflow-x: auto; }}
blockquote {{
    border-left: 3px solid {GREEN_PRIMARY};
    margin: 8px 0;
    padding: 4px 12px;
    color: #e4e4e7;
}}
a {{ color: #bbf7d0; text-decoration: none; }}
strong, b {{ color: #ffffff; font-weight: 600; }}
"""

def _editor_meta(component: dict | None) -> str:
    if not component:
        return ""
    return format_editor_meta(
        author=component.get("author", ""),
        created_at=component.get("created_at", ""),
        updated_at=component.get("updated_at", ""),
    )

def build_description_card(text: str, server_description: dict | None = None) -> QFrame:
    meta = _editor_meta(server_description)
    card = QFrame()
    card.setObjectName("inspectorDescSection")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(8)

    title_lbl = QLabel("DESCRIPTION")
    title_lbl.setObjectName("fieldLabel")
    lay.addWidget(title_lbl)

    browser = QTextBrowser()
    browser.setObjectName("inspectorDescBrowser")
    browser.setOpenLinks(False)
    browser.setReadOnly(True)
    browser.setMinimumHeight(_DESC_MIN_HEIGHT)
    browser.setSizePolicy(
        QSizePolicy.Policy.Preferred,
        QSizePolicy.Policy.Preferred,
    )
    palette = browser.palette()
    palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
    browser.setPalette(palette)
    browser.document().setDefaultStyleSheet(_INSPECTOR_MARKDOWN_CSS)
    browser.setMarkdown(text)
    lay.addWidget(browser)

    if meta:
        meta_lbl = QLabel(meta)
        meta_lbl.setObjectName("inspectorDescMeta")
        meta_lbl.setWordWrap(True)
        lay.addWidget(meta_lbl)

    return card
