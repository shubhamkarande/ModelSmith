"""
ModelSmith - Experiment View
UI for tracking and comparing ML experiments.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QTextEdit, QMessageBox, QFrame, QDialog,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout,
    QScrollArea, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components.widgets import (
    StatCard, DataTable, SectionHeader, EmptyState,
    ChartContainer, StatusIndicator, TagsWidget
)
from database.models import Experiment


class NewExperimentDialog(QDialog):
    """Dialog for creating a new experiment."""
    
    def __init__(self, datasets: list, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("New Experiment")
        self.setMinimumWidth(450)
        self.setStyleSheet("background-color: #252526;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter experiment name")
        form.addRow("Name:", self.name_input)
        
        # Dataset
        self.dataset_combo = QComboBox()
        for ds in datasets:
            self.dataset_combo.addItem(ds.name, ds.id)
        form.addRow("Dataset:", self.dataset_combo)
        
        # Model type
        self.model_type_input = QLineEdit()
        self.model_type_input.setPlaceholderText("e.g., RandomForest, LogisticRegression")
        form.addRow("Model Type:", self.model_type_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Optional description")
        form.addRow("Description:", self.description_input)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
    
    def get_data(self) -> dict:
        """Get the form data."""
        return {
            'name': self.name_input.text(),
            'dataset_id': self.dataset_combo.currentData(),
            'model_type': self.model_type_input.text(),
            'description': self.description_input.toPlainText()
        }


class LogMetricsDialog(QDialog):
    """Dialog for logging metrics to an experiment."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Log Metrics")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #252526;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Common metrics
        form = QFormLayout()
        form.setSpacing(12)
        
        self.accuracy_input = QDoubleSpinBox()
        self.accuracy_input.setRange(0, 1)
        self.accuracy_input.setDecimals(4)
        self.accuracy_input.setSingleStep(0.01)
        form.addRow("Accuracy:", self.accuracy_input)
        
        self.precision_input = QDoubleSpinBox()
        self.precision_input.setRange(0, 1)
        self.precision_input.setDecimals(4)
        self.precision_input.setSingleStep(0.01)
        form.addRow("Precision:", self.precision_input)
        
        self.recall_input = QDoubleSpinBox()
        self.recall_input.setRange(0, 1)
        self.recall_input.setDecimals(4)
        self.recall_input.setSingleStep(0.01)
        form.addRow("Recall:", self.recall_input)
        
        self.f1_input = QDoubleSpinBox()
        self.f1_input.setRange(0, 1)
        self.f1_input.setDecimals(4)
        self.f1_input.setSingleStep(0.01)
        form.addRow("F1 Score:", self.f1_input)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Metrics")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def get_metrics(self) -> dict:
        """Get the metrics data."""
        metrics = {}
        if self.accuracy_input.value() > 0:
            metrics['accuracy'] = self.accuracy_input.value()
        if self.precision_input.value() > 0:
            metrics['precision'] = self.precision_input.value()
        if self.recall_input.value() > 0:
            metrics['recall'] = self.recall_input.value()
        if self.f1_input.value() > 0:
            metrics['f1_score'] = self.f1_input.value()
        return metrics


class ExperimentView(QWidget):
    """Main view for experiment tracking."""
    
    experiment_selected = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_experiment: Optional[Experiment] = None
        self.experiment_service = None
        self.dataset_service = None
        self.viz_service = None
        self.selected_for_comparison: List[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Experiment list
        left_panel = self._create_experiment_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Experiment details
        right_panel = self._create_detail_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 650])
    
    def _create_experiment_list_panel(self) -> QWidget:
        """Create the experiment list panel."""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #252526; border-right: 1px solid #3c3c3c; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = SectionHeader("Experiments", "New")
        header.action_clicked.connect(self._new_experiment)
        layout.addWidget(header)
        
        # Experiment list
        self.experiment_list = DataTable(["Name", "Model", "Status"])
        self.experiment_list.row_selected.connect(self._on_experiment_selected)
        self.experiment_list.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.experiment_list)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        compare_btn = QPushButton("Compare Selected")
        compare_btn.clicked.connect(self._compare_experiments)
        btn_layout.addWidget(compare_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("danger", True)
        delete_btn.clicked.connect(self._delete_experiment)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def _create_detail_panel(self) -> QWidget:
        """Create the experiment detail panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Empty state
        self.empty_state = EmptyState(
            "No Experiment Selected",
            "Select an experiment from the list or create a new one.",
            "New Experiment"
        )
        self.empty_state.action_clicked.connect(self._new_experiment)
        layout.addWidget(self.empty_state)
        
        # Detail container
        self.detail_container = QWidget()
        self.detail_container.hide()
        detail_layout = QVBoxLayout(self.detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.exp_name_label = QLabel("Experiment Name")
        self.exp_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.exp_name_label)
        
        header_layout.addStretch()
        
        self.status_indicator = StatusIndicator()
        header_layout.addWidget(self.status_indicator)
        
        detail_layout.addLayout(header_layout)
        
        # Info row
        info_layout = QHBoxLayout()
        
        self.model_type_label = QLabel("Model Type: -")
        self.model_type_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(self.model_type_label)
        
        self.dataset_label = QLabel("Dataset: -")
        self.dataset_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(self.dataset_label)
        
        self.timestamp_label = QLabel("Created: -")
        self.timestamp_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(self.timestamp_label)
        
        info_layout.addStretch()
        
        detail_layout.addLayout(info_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        log_metrics_btn = QPushButton("Log Metrics")
        log_metrics_btn.clicked.connect(self._log_metrics)
        action_layout.addWidget(log_metrics_btn)
        
        complete_btn = QPushButton("Mark Complete")
        complete_btn.clicked.connect(self._complete_experiment)
        action_layout.addWidget(complete_btn)
        
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self._export_report)
        action_layout.addWidget(export_btn)
        
        action_layout.addStretch()
        
        detail_layout.addLayout(action_layout)
        
        # Tabs
        tabs = QTabWidget()
        detail_layout.addWidget(tabs)
        
        # Metrics tab
        metrics_tab = self._create_metrics_tab()
        tabs.addTab(metrics_tab, "Metrics")
        
        # Parameters tab
        params_tab = self._create_params_tab()
        tabs.addTab(params_tab, "Parameters")
        
        # Notes tab
        notes_tab = self._create_notes_tab()
        tabs.addTab(notes_tab, "Notes")
        
        layout.addWidget(self.detail_container)
        
        return panel
    
    def _create_metrics_tab(self) -> QWidget:
        """Create metrics display tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Stats cards for key metrics
        self.metrics_cards_layout = QGridLayout()
        layout.addLayout(self.metrics_cards_layout)
        
        # Metrics table
        self.metrics_table = DataTable(["Metric", "Value"])
        layout.addWidget(self.metrics_table)
        
        return tab
    
    def _create_params_tab(self) -> QWidget:
        """Create parameters display tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.params_table = DataTable(["Parameter", "Value"])
        layout.addWidget(self.params_table)
        
        return tab
    
    def _create_notes_tab(self) -> QWidget:
        """Create notes tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add notes about this experiment...")
        layout.addWidget(self.notes_edit)
        
        save_notes_btn = QPushButton("Save Notes")
        save_notes_btn.clicked.connect(self._save_notes)
        layout.addWidget(save_notes_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return tab
    
    def set_services(self, experiment_service, dataset_service, viz_service):
        """Set the service instances."""
        self.experiment_service = experiment_service
        self.dataset_service = dataset_service
        self.viz_service = viz_service
    
    def refresh_experiment_list(self):
        """Refresh the experiment list."""
        if not self.experiment_service:
            return
        
        experiments = self.experiment_service.get_all_experiments()
        data = [
            [e.name, e.model_type, e.status.capitalize()]
            for e in experiments
        ]
        self.experiment_list.set_data(data)
        
        self._experiment_ids = [e.id for e in experiments]
    
    def _new_experiment(self):
        """Create a new experiment."""
        if not self.experiment_service or not self.dataset_service:
            return
        
        datasets = self.dataset_service.get_all_datasets()
        if not datasets:
            QMessageBox.warning(self, "No Datasets", "Please import a dataset first.")
            return
        
        dialog = NewExperimentDialog(datasets, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                experiment = self.experiment_service.create_experiment(
                    name=data['name'],
                    dataset_id=data['dataset_id'],
                    model_type=data['model_type'],
                    description=data['description']
                )
                self.refresh_experiment_list()
                QMessageBox.information(self, "Success", f"Experiment '{experiment.name}' created!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create experiment: {str(e)}")
    
    def _on_experiment_selected(self, row: int):
        """Handle experiment selection."""
        if hasattr(self, '_experiment_ids') and row < len(self._experiment_ids):
            exp_id = self._experiment_ids[row]
            self._show_experiment_details(exp_id)
            self.experiment_selected.emit(exp_id)
    
    def _show_experiment_details(self, experiment_id: str):
        """Show details for selected experiment."""
        if not self.experiment_service:
            return
        
        experiment = self.experiment_service.get_experiment(experiment_id)
        if not experiment:
            return
        
        self.current_experiment = experiment
        
        self.empty_state.hide()
        self.detail_container.show()
        
        # Update header
        self.exp_name_label.setText(experiment.name)
        self.status_indicator.set_status(experiment.status)
        
        # Update info
        self.model_type_label.setText(f"Model: {experiment.model_type}")
        
        if self.dataset_service:
            dataset = self.dataset_service.get_dataset(experiment.dataset_id)
            self.dataset_label.setText(f"Dataset: {dataset.name if dataset else 'Unknown'}")
        
        self.timestamp_label.setText(f"Created: {experiment.timestamp[:10]}")
        
        # Update metrics
        metrics_data = [[k, f"{v:.4f}" if isinstance(v, float) else str(v)] 
                       for k, v in experiment.metrics.items()]
        self.metrics_table.set_data(metrics_data)
        
        # Update parameters
        params_data = [[k, str(v)] for k, v in experiment.parameters.items()]
        self.params_table.set_data(params_data)
        
        # Update notes
        self.notes_edit.setText(experiment.notes)
    
    def _log_metrics(self):
        """Log metrics for current experiment."""
        if not self.current_experiment:
            return
        
        dialog = LogMetricsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            metrics = dialog.get_metrics()
            if metrics:
                try:
                    self.experiment_service.log_metrics(self.current_experiment.id, metrics)
                    self._show_experiment_details(self.current_experiment.id)
                    QMessageBox.information(self, "Success", "Metrics logged successfully!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to log metrics: {str(e)}")
    
    def _complete_experiment(self):
        """Mark experiment as completed."""
        if not self.current_experiment:
            return
        
        try:
            self.experiment_service.complete_experiment(self.current_experiment.id)
            self._show_experiment_details(self.current_experiment.id)
            self.refresh_experiment_list()
            QMessageBox.information(self, "Success", "Experiment marked as completed!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete experiment: {str(e)}")
    
    def _export_report(self):
        """Export experiment as HTML report."""
        if not self.current_experiment:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        import os
        
        # Default filename
        default_name = f"{self.current_experiment.name.replace(' ', '_')}_report.html"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            default_name,
            "HTML Files (*.html)"
        )
        
        if file_path:
            try:
                self.experiment_service.export_report(self.current_experiment.id, file_path)
                QMessageBox.information(self, "Success", f"Report exported to:\n{file_path}")
                
                # Open in browser
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(file_path)}')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
    
    def _save_notes(self):
        """Save experiment notes."""
        if not self.current_experiment:
            return
        
        notes = self.notes_edit.toPlainText()
        self.current_experiment.notes = notes
        try:
            self.experiment_service.db.update_experiment(self.current_experiment)
            QMessageBox.information(self, "Success", "Notes saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save notes: {str(e)}")
    
    def _compare_experiments(self):
        """Compare selected experiments."""
        selected_rows = self.experiment_list.selectionModel().selectedRows()
        if len(selected_rows) < 2:
            QMessageBox.warning(self, "Select Experiments", "Please select at least 2 experiments to compare.")
            return
        
        exp_ids = [self._experiment_ids[row.row()] for row in selected_rows]
        comparison = self.experiment_service.compare_experiments(exp_ids)
        
        # Show comparison dialog (simplified)
        msg = "Experiment Comparison:\n\n"
        for metric, values in comparison['metrics'].items():
            msg += f"{metric}:\n"
            for exp_id, value in values.items():
                exp = self.experiment_service.get_experiment(exp_id)
                msg += f"  {exp.name}: {value:.4f if isinstance(value, float) else value}\n"
            msg += "\n"
        
        QMessageBox.information(self, "Comparison", msg)
    
    def _delete_experiment(self):
        """Delete selected experiment."""
        if not self.current_experiment:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete experiment '{self.current_experiment.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.experiment_service.delete_experiment(self.current_experiment.id)
            self.current_experiment = None
            self.detail_container.hide()
            self.empty_state.show()
            self.refresh_experiment_list()
