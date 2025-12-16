"""
ModelSmith - Model Registry View
UI for managing registered models.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QFileDialog, QTableWidget, QMessageBox, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components.widgets import StatCard, DataTable, SectionHeader, EmptyState
from database.models import Model


class RegisterModelDialog(QDialog):
    """Dialog for registering a new model."""
    
    def __init__(self, experiments: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register Model")
        self.setMinimumWidth(500)
        self.setStyleSheet("background-color: #252526;")
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        form.addRow("Name:", self.name_input)
        
        self.experiment_combo = QComboBox()
        for exp in experiments:
            self.experiment_combo.addItem(f"{exp.name}", exp.id)
        form.addRow("Experiment:", self.experiment_combo)
        
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        file_layout.addWidget(self.file_path_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        file_layout.addWidget(browse_btn)
        form.addRow("Model File:", file_layout)
        
        self.framework_input = QComboBox()
        self.framework_input.addItems(['sklearn', 'pytorch', 'tensorflow', 'other'])
        form.addRow("Framework:", self.framework_input)
        
        self.version_input = QLineEdit("1.0.0")
        form.addRow("Version:", self.version_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        form.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        QPushButton("Cancel", clicked=self.reject).setParent(self)
        btn_layout.addWidget(QPushButton("Cancel", clicked=self.reject))
        btn_layout.addWidget(QPushButton("Register", clicked=self.accept))
        layout.addLayout(btn_layout)
    
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Model File")
        if path: self.file_path_input.setText(path)
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'experiment_id': self.experiment_combo.currentData(),
            'file_path': self.file_path_input.text(),
            'framework': self.framework_input.currentText(),
            'version': self.version_input.text(),
            'notes': self.notes_input.toPlainText()
        }


class ModelRegistryView(QWidget):
    """Main view for model registry."""
    
    model_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_model = None
        self.model_service = None
        self.experiment_service = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel
        left = QFrame()
        left.setStyleSheet("background-color: #252526; border-right: 1px solid #3c3c3c;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        
        header = SectionHeader("Models", "Register")
        header.action_clicked.connect(self._register_model)
        left_layout.addWidget(header)
        
        self.model_list = DataTable(["Name", "Framework", "Version"])
        self.model_list.row_selected.connect(self._on_model_selected)
        left_layout.addWidget(self.model_list)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setProperty("danger", True)
        delete_btn.clicked.connect(self._delete_model)
        left_layout.addWidget(delete_btn)
        
        splitter.addWidget(left)
        
        # Right panel
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        
        self.empty_state = EmptyState("No Model Selected", "Select or register a model", "Register")
        self.empty_state.action_clicked.connect(self._register_model)
        right_layout.addWidget(self.empty_state)
        
        self.detail_container = QWidget()
        self.detail_container.hide()
        detail_layout = QVBoxLayout(self.detail_container)
        
        self.model_name_label = QLabel()
        self.model_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        detail_layout.addWidget(self.model_name_label)
        
        cards = QHBoxLayout()
        self.framework_card = StatCard("Framework", "-")
        self.version_card = StatCard("Version", "-")
        self.size_card = StatCard("Size", "-")
        cards.addWidget(self.framework_card)
        cards.addWidget(self.version_card)
        cards.addWidget(self.size_card)
        detail_layout.addLayout(cards)
        
        self.file_path_label = QLabel()
        self.file_path_label.setStyleSheet("color: #888;")
        detail_layout.addWidget(self.file_path_label)
        
        self.metrics_table = DataTable(["Metric", "Value"])
        detail_layout.addWidget(self.metrics_table)
        
        right_layout.addWidget(self.detail_container)
        splitter.addWidget(right)
        splitter.setSizes([350, 650])
    
    def set_services(self, model_service, experiment_service):
        self.model_service = model_service
        self.experiment_service = experiment_service
    
    def refresh_model_list(self):
        if not self.model_service: return
        models = self.model_service.get_all_models()
        self.model_list.set_data([[m.name, m.framework, m.version] for m in models])
        self._model_ids = [m.id for m in models]
    
    def _register_model(self):
        if not self.experiment_service: return
        exps = self.experiment_service.get_all_experiments()
        if not exps:
            QMessageBox.warning(self, "Error", "Create an experiment first")
            return
        dlg = RegisterModelDialog(exps, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            self.model_service.register_model(**d)
            self.refresh_model_list()
    
    def _on_model_selected(self, row):
        if row < len(self._model_ids):
            self._show_details(self._model_ids[row])
    
    def _show_details(self, model_id):
        m = self.model_service.get_model(model_id)
        if not m: return
        self.current_model = m
        self.empty_state.hide()
        self.detail_container.show()
        self.model_name_label.setText(m.name)
        self.framework_card.set_value(m.framework or "-")
        self.version_card.set_value(m.version)
        self.size_card.set_value(f"{m.file_size/1024:.1f} KB")
        self.file_path_label.setText(m.file_path)
        self.metrics_table.set_data([[k, f"{v:.4f}"] for k, v in m.metrics.items()])
    
    def _delete_model(self):
        if not self.current_model: return
        if QMessageBox.question(self, "Delete", f"Delete {self.current_model.name}?") == QMessageBox.StandardButton.Yes:
            self.model_service.delete_model(self.current_model.id)
            self.current_model = None
            self.detail_container.hide()
            self.empty_state.show()
            self.refresh_model_list()
