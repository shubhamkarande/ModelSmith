"""
ModelSmith - AI Dataset & Model Management Tool
Entry point for the application.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow


def load_stylesheet() -> str:
    """Load the dark theme stylesheet."""
    style_path = Path(__file__).parent / "ui" / "styles" / "dark_theme.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    """Main entry point."""
    # High DPI support
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("ModelSmith")
    app.setOrganizationName("ModelSmith")
    app.setApplicationVersion("1.0.0")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    if not font.exactMatch():
        font = QFont("Ubuntu", 10)
    if not font.exactMatch():
        font = QFont("Roboto", 10)
    app.setFont(font)
    
    # Load stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
