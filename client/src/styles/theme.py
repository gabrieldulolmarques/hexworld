STYLESHEET = """
QWidget {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 14px;
    color: #1f2937;
    background-color: #f9fafb;
}

QLabel#title {
    font-size: 22px;
    font-weight: 600;
    color: #111827;
}

QLabel#status {
    color: #6b7280;
    font-size: 12px;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #93c5fd;
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
}

QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2563eb;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #9ca3af;
}

QPushButton#secondary {
    background-color: transparent;
    color: #3b82f6;
    border: 1px solid #d1d5db;
}

QPushButton#secondary:hover {
    background-color: #eff6ff;
    border-color: #3b82f6;
}

QPushButton#secondary:disabled {
    background-color: transparent;
    color: #9ca3af;
    border-color: #e5e7eb;
}
"""
