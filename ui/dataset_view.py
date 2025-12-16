"""
ModelSmith - Dataset View
UI for browsing, importing, and analyzing datasets.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QTextEdit, QMessageBox, QFrame,
    QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components.widgets import (
    StatCard, DataTable, SectionHeader, EmptyState, ChartContainer
)
from database.models import Dataset


class DatasetView(QWidget):
    """Main view for dataset management."""
    
    dataset_selected = pyqtSignal(str)  # Emits dataset ID
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_dataset: Optional[Dataset] = None
        self.dataset_service = None
        self.viz_service = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Dataset list
        left_panel = self._create_dataset_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Dataset details
        right_panel = self._create_detail_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 700])
    
    def _create_dataset_list_panel(self) -> QWidget:
        """Create the dataset list panel."""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #252526; border-right: 1px solid #3c3c3c; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with import button
        header = SectionHeader("Datasets", "Import")
        header.action_clicked.connect(self._import_dataset)
        layout.addWidget(header)
        
        # Dataset list
        self.dataset_list = DataTable(["Name", "Type", "Rows"])
        self.dataset_list.row_selected.connect(self._on_dataset_selected)
        layout.addWidget(self.dataset_list)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_dataset)
        btn_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("danger", True)
        delete_btn.clicked.connect(self._delete_dataset)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def _create_detail_panel(self) -> QWidget:
        """Create the dataset detail panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Empty state (shown when no dataset selected)
        self.empty_state = EmptyState(
            "No Dataset Selected",
            "Select a dataset from the list or import a new one.",
            "Import Dataset"
        )
        self.empty_state.action_clicked.connect(self._import_dataset)
        layout.addWidget(self.empty_state)
        
        # Detail container (hidden initially)
        self.detail_container = QWidget()
        self.detail_container.hide()
        detail_layout = QVBoxLayout(self.detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(16)
        
        # Dataset info header
        self.dataset_name_label = QLabel("Dataset Name")
        self.dataset_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        detail_layout.addWidget(self.dataset_name_label)
        
        self.dataset_path_label = QLabel("Path")
        self.dataset_path_label.setStyleSheet("color: #888888; font-size: 12px;")
        detail_layout.addWidget(self.dataset_path_label)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        self.rows_card = StatCard("Rows", "0")
        self.cols_card = StatCard("Columns", "0")
        self.size_card = StatCard("Size", "0 KB")
        self.type_card = StatCard("Type", "-")
        stats_layout.addWidget(self.rows_card)
        stats_layout.addWidget(self.cols_card)
        stats_layout.addWidget(self.size_card)
        stats_layout.addWidget(self.type_card)
        detail_layout.addLayout(stats_layout)
        
        # Tabs for different views
        self.tabs = QTabWidget()
        detail_layout.addWidget(self.tabs)
        
        # Schema tab
        self.schema_tab = self._create_schema_tab()
        self.tabs.addTab(self.schema_tab, "Schema")
        
        # Preview tab
        self.preview_tab = self._create_preview_tab()
        self.tabs.addTab(self.preview_tab, "Preview")
        
        # Statistics tab
        self.stats_tab = self._create_stats_tab()
        self.tabs.addTab(self.stats_tab, "Statistics")
        
        # Distribution tab
        self.dist_tab = self._create_distribution_tab()
        self.tabs.addTab(self.dist_tab, "Distribution")
        
        layout.addWidget(self.detail_container)
        
        return panel
    
    def _create_schema_tab(self) -> QWidget:
        """Create schema preview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.schema_table = DataTable(["Column", "Type"])
        layout.addWidget(self.schema_table)
        
        return tab
    
    def _create_preview_tab(self) -> QWidget:
        """Create data preview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table)
        
        return tab
    
    def _create_stats_tab(self) -> QWidget:
        """Create statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Missing values section
        missing_header = QLabel("Missing Values")
        missing_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(missing_header)
        
        self.missing_table = DataTable(["Column", "Count", "Percentage"])
        self.missing_table.setMaximumHeight(200)
        layout.addWidget(self.missing_table)
        
        # Column statistics
        stats_header = QLabel("Column Statistics")
        stats_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(stats_header)
        
        self.column_stats_table = DataTable(["Column", "Mean", "Std", "Min", "Max"])
        layout.addWidget(self.column_stats_table)
        
        return tab
    
    def _create_distribution_tab(self) -> QWidget:
        """Create distribution chart tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.dist_chart = ChartContainer("Class Distribution")
        layout.addWidget(self.dist_chart)
        
        return tab
    
    def set_services(self, dataset_service, viz_service):
        """Set the service instances."""
        self.dataset_service = dataset_service
        self.viz_service = viz_service
    
    def refresh_dataset_list(self):
        """Refresh the dataset list."""
        if not self.dataset_service:
            return
        
        datasets = self.dataset_service.get_all_datasets()
        data = [
            [d.name, d.type.upper(), str(d.row_count)]
            for d in datasets
        ]
        self.dataset_list.set_data(data)
        
        # Store dataset IDs for selection
        self._dataset_ids = [d.id for d in datasets]
    
    def _import_dataset(self):
        """Handle dataset import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Dataset",
            "",
            "Data Files (*.csv *.json *.jsonl);;CSV Files (*.csv);;JSON Files (*.json *.jsonl);;All Files (*)"
        )
        
        if file_path and self.dataset_service:
            try:
                dataset = self.dataset_service.import_dataset(file_path)
                self.refresh_dataset_list()
                QMessageBox.information(self, "Success", f"Dataset '{dataset.name}' imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import dataset: {str(e)}")
    
    def _on_dataset_selected(self, row: int):
        """Handle dataset selection."""
        if hasattr(self, '_dataset_ids') and row < len(self._dataset_ids):
            dataset_id = self._dataset_ids[row]
            self._show_dataset_details(dataset_id)
            self.dataset_selected.emit(dataset_id)
    
    def _show_dataset_details(self, dataset_id: str):
        """Show details for selected dataset."""
        if not self.dataset_service:
            return
        
        dataset = self.dataset_service.get_dataset(dataset_id)
        if not dataset:
            return
        
        self.current_dataset = dataset
        
        # Show detail container, hide empty state
        self.empty_state.hide()
        self.detail_container.show()
        
        # Update basic info
        self.dataset_name_label.setText(dataset.name)
        self.dataset_path_label.setText(dataset.path)
        
        # Update stats
        self.rows_card.set_value(f"{dataset.row_count:,}")
        self.cols_card.set_value(str(dataset.column_count))
        self.size_card.set_value(self._format_size(dataset.file_size))
        self.type_card.set_value(dataset.type.upper())
        
        # Update schema
        schema_data = [[col, dtype] for col, dtype in dataset.schema.items()]
        self.schema_table.set_data(schema_data)
        
        # Load preview data
        self._load_preview_data(dataset)
        
        # Load statistics
        self._load_statistics(dataset)
        
        # Load distribution chart
        self._load_distribution(dataset)
    
    def _load_preview_data(self, dataset: Dataset):
        """Load data preview."""
        try:
            df = self.dataset_service.load_data(dataset, limit=100)
            
            self.preview_table.setColumnCount(len(df.columns))
            self.preview_table.setRowCount(len(df))
            self.preview_table.setHorizontalHeaderLabels(df.columns.tolist())
            
            for row_idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.preview_table.setItem(row_idx, col_idx, item)
        except Exception as e:
            print(f"Error loading preview: {e}")
    
    def _load_statistics(self, dataset: Dataset):
        """Load dataset statistics."""
        try:
            stats = self.dataset_service.get_statistics(dataset)
            
            # Missing values
            missing_data = []
            for col, info in stats.get('missing_values', {}).items():
                missing_data.append([col, str(info['count']), f"{info['percentage']:.1f}%"])
            self.missing_table.set_data(missing_data)
            
            # Column stats
            col_stats_data = []
            for col, info in stats.get('column_stats', {}).items():
                if 'mean' in info:
                    col_stats_data.append([
                        col,
                        f"{info['mean']:.2f}" if info['mean'] else "-",
                        f"{info['std']:.2f}" if info['std'] else "-",
                        f"{info['min']:.2f}" if info['min'] else "-",
                        f"{info['max']:.2f}" if info['max'] else "-"
                    ])
            self.column_stats_table.set_data(col_stats_data)
        except Exception as e:
            print(f"Error loading statistics: {e}")
    
    def _load_distribution(self, dataset: Dataset):
        """Load distribution chart."""
        try:
            if self.viz_service:
                distribution = self.dataset_service.get_class_distribution(dataset)
                if distribution:
                    fig = self.viz_service.plot_class_distribution(distribution)
                    chart_bytes = self.viz_service.figure_to_bytes(fig)
                    self.dist_chart.set_chart(chart_bytes)
        except Exception as e:
            print(f"Error loading distribution: {e}")
    
    def _refresh_dataset(self):
        """Refresh dataset analysis and increment version."""
        if not self.current_dataset:
            QMessageBox.warning(self, "No Selection", "Please select a dataset to refresh.")
            return
        
        try:
            updated = self.dataset_service.refresh_dataset(self.current_dataset.id)
            self._show_dataset_details(updated.id)
            self.refresh_dataset_list()
            QMessageBox.information(
                self, 
                "Success", 
                f"Dataset refreshed! Version updated to v{updated.version}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh dataset: {str(e)}")
    
    def _delete_dataset(self):
        """Delete selected dataset."""
        if not self.current_dataset:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_dataset.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.dataset_service.delete_dataset(self.current_dataset.id)
            self.current_dataset = None
            self.detail_container.hide()
            self.empty_state.show()
            self.refresh_dataset_list()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
