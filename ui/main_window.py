"""
ModelSmith - Main Window
The main application window with navigation and dockable panels.
"""

import os
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QMessageBox, QStatusBar, QMenuBar,
    QMenu, QFileDialog, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QFont

from database.db_manager import DatabaseManager
from services.dataset_service import DatasetService
from services.experiment_service import ExperimentService
from services.model_service import ModelService
from services.labeling_service import LabelingService
from services.visualization_service import VisualizationService

from ui.dataset_view import DatasetView
from ui.experiment_view import ExperimentView
from ui.model_registry_view import ModelRegistryView
from ui.labeling_view import LabelingView
from ui.visualization_view import VisualizationView


class SidebarButton(QPushButton):
    """Styled navigation button for sidebar."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                text-align: left;
                color: #888888;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2d2d30;
                color: #cccccc;
            }
            QPushButton:checked {
                background-color: #094771;
                color: white;
            }
        """)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ModelSmith - AI Dataset & Model Manager")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Initialize services
        self._init_services()
        
        # Set up UI
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        
        # Load initial data
        self._refresh_all()
    
    def _init_services(self):
        """Initialize database and services."""
        self.db = DatabaseManager()
        self.dataset_service = DatasetService(self.db)
        self.experiment_service = ExperimentService(self.db)
        self.model_service = ModelService(self.db)
        self.labeling_service = LabelingService(self.db)
        self.viz_service = VisualizationService(dark_mode=True)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Create views
        self._create_views()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("background-color: #007acc; color: white;")
    
    def _create_sidebar(self) -> QWidget:
        """Create the navigation sidebar."""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-right: 1px solid #3c3c3c;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)
        
        # Logo/Title
        title = QLabel("ModelSmith")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; padding: 8px;")
        layout.addWidget(title)
        
        tagline = QLabel("Tame your data. Track your models.")
        tagline.setStyleSheet("font-size: 11px; color: #666666; padding: 0 8px 16px;")
        tagline.setWordWrap(True)
        layout.addWidget(tagline)
        
        # Navigation buttons
        self.nav_buttons = []
        
        nav_items = [
            ("📁  Datasets", 0),
            ("🏷️  Labeling", 1),
            ("🧪  Experiments", 2),
            ("📦  Models", 3),
            ("📊  Analytics", 4),
        ]
        
        for text, index in nav_items:
            btn = SidebarButton(text)
            btn.clicked.connect(lambda checked, i=index: self._navigate_to(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Version info
        version = QLabel("v1.0.0 • Offline")
        version.setStyleSheet("color: #555555; font-size: 11px; padding: 8px;")
        layout.addWidget(version)
        
        # Set first button as active
        self.nav_buttons[0].setChecked(True)
        
        return sidebar
    
    def _create_views(self):
        """Create and add all views to the stack."""
        # Dataset view
        self.dataset_view = DatasetView()
        self.dataset_view.set_services(self.dataset_service, self.viz_service)
        self.content_stack.addWidget(self.dataset_view)
        
        # Labeling view
        self.labeling_view = LabelingView()
        self.labeling_view.set_services(self.dataset_service, self.labeling_service)
        self.content_stack.addWidget(self.labeling_view)
        
        # Experiment view
        self.experiment_view = ExperimentView()
        self.experiment_view.set_services(self.experiment_service, self.dataset_service, self.viz_service)
        self.content_stack.addWidget(self.experiment_view)
        
        # Model registry view
        self.model_view = ModelRegistryView()
        self.model_view.set_services(self.model_service, self.experiment_service)
        self.content_stack.addWidget(self.model_view)
        
        # Visualization view
        self.viz_view = VisualizationView()
        self.viz_view.set_services(self.dataset_service, self.experiment_service, self.viz_service)
        self.content_stack.addWidget(self.viz_view)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        import_action = QAction("Import Dataset...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._import_dataset)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        datasets_action = QAction("Datasets", self)
        datasets_action.setShortcut(QKeySequence("Ctrl+1"))
        datasets_action.triggered.connect(lambda: self._navigate_to(0))
        view_menu.addAction(datasets_action)
        
        labeling_action = QAction("Labeling", self)
        labeling_action.setShortcut(QKeySequence("Ctrl+2"))
        labeling_action.triggered.connect(lambda: self._navigate_to(1))
        view_menu.addAction(labeling_action)
        
        experiments_action = QAction("Experiments", self)
        experiments_action.setShortcut(QKeySequence("Ctrl+3"))
        experiments_action.triggered.connect(lambda: self._navigate_to(2))
        view_menu.addAction(experiments_action)
        
        models_action = QAction("Models", self)
        models_action.setShortcut(QKeySequence("Ctrl+4"))
        models_action.triggered.connect(lambda: self._navigate_to(3))
        view_menu.addAction(models_action)
        
        analytics_action = QAction("Analytics", self)
        analytics_action.setShortcut(QKeySequence("Ctrl+5"))
        analytics_action.triggered.connect(lambda: self._navigate_to(4))
        view_menu.addAction(analytics_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About ModelSmith", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        pass  # Shortcuts defined in menu actions
    
    def _navigate_to(self, index: int):
        """Navigate to a specific view."""
        self.content_stack.setCurrentIndex(index)
        
        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        # Refresh the view
        self._refresh_current_view(index)
    
    def _refresh_current_view(self, index: int):
        """Refresh data for the current view."""
        if index == 0:
            self.dataset_view.refresh_dataset_list()
        elif index == 1:
            self.labeling_view._refresh_datasets()
        elif index == 2:
            self.experiment_view.refresh_experiment_list()
        elif index == 3:
            self.model_view.refresh_model_list()
        elif index == 4:
            self.viz_view._refresh_datasets()
    
    def _refresh_all(self):
        """Refresh all views."""
        self.dataset_view.refresh_dataset_list()
        self.experiment_view.refresh_experiment_list()
        self.model_view.refresh_model_list()
    
    def _import_dataset(self):
        """Import a dataset via file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Dataset",
            "",
            "Data Files (*.csv *.json *.jsonl);;All Files (*)"
        )
        
        if file_path:
            try:
                dataset = self.dataset_service.import_dataset(file_path)
                self._navigate_to(0)
                self.dataset_view.refresh_dataset_list()
                self.statusBar().showMessage(f"Imported: {dataset.name}")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About ModelSmith",
            "<h2>ModelSmith</h2>"
            "<p><b>AI Dataset & Model Management Tool</b></p>"
            "<p>Tame your data. Track your models. Stay sane.</p>"
            "<hr>"
            "<p>Version 1.0.0</p>"
            "<p>Built with Python + PyQt6</p>"
            "<p>© 2024 - Open Source</p>"
        )
