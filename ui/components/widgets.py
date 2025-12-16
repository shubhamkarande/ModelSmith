"""
ModelSmith - Reusable UI Components
Custom widgets and components for the application.
"""

from typing import Optional, Dict, Any, List, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QSpacerItem, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont


class StatCard(QFrame):
    """A card widget displaying a statistic with label."""
    
    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        icon: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet("""
            #statCard {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #007acc; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #666666; font-size: 11px;")
            layout.addWidget(subtitle_label)
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self.value_label.setText(value)


class DataTable(QTableWidget):
    """Enhanced table widget for data display."""
    
    row_selected = pyqtSignal(int)
    
    def __init__(
        self,
        columns: List[str],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.columns = columns
        
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Stretch columns
        header = self.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        # Connect selection
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _on_selection_changed(self):
        """Handle row selection."""
        rows = self.selectionModel().selectedRows()
        if rows:
            self.row_selected.emit(rows[0].row())
    
    def set_data(self, data: List[List[Any]]):
        """Set table data from list of rows."""
        self.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                if col_idx < len(self.columns):
                    item = QTableWidgetItem(str(value))
                    self.setItem(row_idx, col_idx, item)
    
    def get_selected_row(self) -> Optional[int]:
        """Get currently selected row index."""
        rows = self.selectionModel().selectedRows()
        return rows[0].row() if rows else None
    
    def clear_data(self):
        """Clear all table data."""
        self.setRowCount(0)


class SidebarButton(QPushButton):
    """A styled button for the sidebar navigation."""
    
    def __init__(
        self,
        text: str,
        icon: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 12px 16px;
                text-align: left;
                color: #cccccc;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2d2d30;
            }
            QPushButton:checked {
                background-color: #094771;
                color: white;
            }
        """)


class SectionHeader(QWidget):
    """A styled section header with title and optional action button."""
    
    action_clicked = pyqtSignal()
    
    def __init__(
        self,
        title: str,
        action_text: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Action button
        if action_text:
            action_btn = QPushButton(action_text)
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            action_btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(action_btn)


class EmptyState(QWidget):
    """Widget displayed when there's no data to show."""
    
    action_clicked = pyqtSignal()
    
    def __init__(
        self,
        title: str,
        description: str,
        action_text: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Icon placeholder
        icon_label = QLabel("📊")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #cccccc;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #888888;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Action button
        if action_text:
            action_btn = QPushButton(action_text)
            action_btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class StatusIndicator(QWidget):
    """A colored status indicator with label."""
    
    STATUS_COLORS = {
        'created': '#888888',
        'running': '#ff9800',
        'completed': '#4caf50',
        'failed': '#f44336'
    }
    
    def __init__(
        self,
        status: str = 'created',
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Dot
        self.dot = QLabel("●")
        layout.addWidget(self.dot)
        
        # Label
        self.label = QLabel(status.capitalize())
        self.label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.label)
        
        self.set_status(status)
    
    def set_status(self, status: str):
        """Update the status."""
        color = self.STATUS_COLORS.get(status, '#888888')
        self.dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.label.setText(status.capitalize())


class ChartContainer(QFrame):
    """A container widget for matplotlib charts."""
    
    def __init__(
        self,
        title: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
            self.layout.addWidget(title_label)
        
        # Chart area
        self.chart_label = QLabel()
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_label.setMinimumSize(400, 300)
        self.layout.addWidget(self.chart_label)
    
    def set_chart(self, image_bytes: bytes):
        """Set the chart image from bytes."""
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        self.chart_label.setPixmap(pixmap.scaled(
            self.chart_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
    
    def clear_chart(self):
        """Clear the chart."""
        self.chart_label.clear()


class LoadingOverlay(QWidget):
    """A loading overlay with spinner and message."""
    
    def __init__(
        self,
        message: str = "Loading...",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)  # Indeterminate
        self.progress.setFixedWidth(200)
        layout.addWidget(self.progress)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("color: white; font-size: 14px;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        self.hide()
    
    def show_loading(self, message: str = "Loading..."):
        """Show the overlay with message."""
        self.message_label.setText(message)
        self.show()
        self.raise_()
    
    def hide_loading(self):
        """Hide the overlay."""
        self.hide()


class TagsWidget(QWidget):
    """Widget for displaying and editing tags."""
    
    tags_changed = pyqtSignal(list)
    
    def __init__(
        self,
        tags: Optional[List[str]] = None,
        editable: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.tags = tags or []
        self.editable = editable
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        
        self._refresh_tags()
    
    def _refresh_tags(self):
        """Refresh the tag display."""
        # Clear existing
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add tags
        for tag in self.tags:
            tag_widget = QLabel(tag)
            tag_widget.setStyleSheet("""
                QLabel {
                    background-color: #094771;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
            self.layout.addWidget(tag_widget)
        
        self.layout.addStretch()
    
    def set_tags(self, tags: List[str]):
        """Set the tags."""
        self.tags = tags
        self._refresh_tags()
    
    def add_tag(self, tag: str):
        """Add a tag."""
        if tag not in self.tags:
            self.tags.append(tag)
            self._refresh_tags()
            self.tags_changed.emit(self.tags)
    
    def remove_tag(self, tag: str):
        """Remove a tag."""
        if tag in self.tags:
            self.tags.remove(tag)
            self._refresh_tags()
            self.tags_changed.emit(self.tags)
