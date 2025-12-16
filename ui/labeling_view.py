"""
ModelSmith - Labeling View
UI for dataset labeling and annotation.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QFrame,
    QLineEdit, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components.widgets import StatCard, DataTable, SectionHeader, EmptyState


class LabelingView(QWidget):
    """Main view for dataset labeling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_dataset = None
        self.dataset_service = None
        self.labeling_service = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left - Dataset selector
        left = QFrame()
        left.setStyleSheet("background-color: #252526; border-right: 1px solid #3c3c3c;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        
        left_layout.addWidget(QLabel("Select Dataset"))
        self.dataset_combo = QComboBox()
        self.dataset_combo.currentIndexChanged.connect(self._on_dataset_changed)
        left_layout.addWidget(self.dataset_combo)
        
        # Stats
        self.progress_card = StatCard("Progress", "0%")
        self.labeled_card = StatCard("Labeled", "0")
        self.unlabeled_card = StatCard("Unlabeled", "0")
        left_layout.addWidget(self.progress_card)
        left_layout.addWidget(self.labeled_card)
        left_layout.addWidget(self.unlabeled_card)
        
        left_layout.addStretch()
        
        # Export button
        export_btn = QPushButton("Export Annotations")
        export_btn.clicked.connect(self._export_annotations)
        left_layout.addWidget(export_btn)
        
        splitter.addWidget(left)
        
        # Right - Labeling area
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        
        self.empty_state = EmptyState("No Dataset Selected", "Select a dataset to start labeling")
        right_layout.addWidget(self.empty_state)
        
        self.label_container = QWidget()
        self.label_container.hide()
        label_layout = QVBoxLayout(self.label_container)
        
        # Label input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Label:"))
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Enter label")
        input_layout.addWidget(self.label_input)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_label)
        input_layout.addWidget(apply_btn)
        label_layout.addLayout(input_layout)
        
        # Data table with labels
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        label_layout.addWidget(self.data_table)
        
        right_layout.addWidget(self.label_container)
        splitter.addWidget(right)
        splitter.setSizes([250, 750])
    
    def set_services(self, dataset_service, labeling_service):
        self.dataset_service = dataset_service
        self.labeling_service = labeling_service
        self._refresh_datasets()
    
    def _refresh_datasets(self):
        if not self.dataset_service: return
        self.dataset_combo.clear()
        self.dataset_combo.addItem("Select dataset...", None)
        for ds in self.dataset_service.get_all_datasets():
            self.dataset_combo.addItem(ds.name, ds.id)
    
    def _on_dataset_changed(self, index):
        ds_id = self.dataset_combo.currentData()
        if not ds_id:
            self.empty_state.show()
            self.label_container.hide()
            return
        
        self.current_dataset = self.dataset_service.get_dataset(ds_id)
        self.empty_state.hide()
        self.label_container.show()
        self._load_data()
        self._update_stats()
    
    def _load_data(self):
        if not self.current_dataset: return
        df = self.dataset_service.load_data(self.current_dataset, limit=500)
        
        # Add label column
        cols = list(df.columns) + ['__label__']
        self.data_table.setColumnCount(len(cols))
        self.data_table.setHorizontalHeaderLabels(cols)
        self.data_table.setRowCount(len(df))
        
        # Get existing annotations
        annotations = {a.item_index: a.label for a in self.labeling_service.get_annotations(self.current_dataset.id)}
        
        for row_idx, row in df.iterrows():
            for col_idx, val in enumerate(row):
                self.data_table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))
            # Add label
            label = annotations.get(row_idx, "")
            self.data_table.setItem(row_idx, len(df.columns), QTableWidgetItem(label))
    
    def _update_stats(self):
        if not self.current_dataset: return
        stats = self.labeling_service.get_label_statistics(self.current_dataset.id)
        self.progress_card.set_value(f"{stats.get('progress_percent', 0):.1f}%")
        self.labeled_card.set_value(str(stats.get('labeled_items', 0)))
        self.unlabeled_card.set_value(str(stats.get('unlabeled_items', 0)))
    
    def _apply_label(self):
        if not self.current_dataset: return
        label = self.label_input.text().strip()
        if not label: return
        
        selected = self.data_table.selectionModel().selectedRows()
        for idx in selected:
            row = idx.row()
            # Check if annotation exists
            existing = self.labeling_service.get_annotation_by_index(self.current_dataset.id, row)
            if existing:
                self.labeling_service.update_label(existing.id, label=label)
            else:
                self.labeling_service.add_label(self.current_dataset.id, row, label)
            
            # Update table
            self.data_table.item(row, self.data_table.columnCount()-1).setText(label)
        
        self._update_stats()
        self.label_input.clear()
    
    def _export_annotations(self):
        if not self.current_dataset: return
        path, _ = QFileDialog.getSaveFileName(self, "Export Annotations", "", "JSON (*.json);;CSV (*.csv)")
        if path:
            fmt = 'csv' if path.endswith('.csv') else 'json'
            self.labeling_service.export_annotations(self.current_dataset.id, path, fmt)
            QMessageBox.information(self, "Success", f"Exported to {path}")
