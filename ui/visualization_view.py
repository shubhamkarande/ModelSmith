"""
ModelSmith - Visualization View
UI for data visualization and analytics.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTabWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from ui.components.widgets import ChartContainer, SectionHeader


class VisualizationView(QWidget):
    """Main view for visualizations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataset_service = None
        self.experiment_service = None
        self.viz_service = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = SectionHeader("Visualizations")
        layout.addWidget(header)
        
        # Controls
        controls = QHBoxLayout()
        
        controls.addWidget(QLabel("Dataset:"))
        self.dataset_combo = QComboBox()
        self.dataset_combo.currentIndexChanged.connect(self._on_dataset_changed)
        controls.addWidget(self.dataset_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_charts)
        controls.addWidget(refresh_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Tabs for different charts
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Distribution tab
        dist_tab = QWidget()
        dist_layout = QVBoxLayout(dist_tab)
        self.dist_chart = ChartContainer("Class Distribution")
        dist_layout.addWidget(self.dist_chart)
        tabs.addTab(dist_tab, "Distribution")
        
        # Missing values tab
        missing_tab = QWidget()
        missing_layout = QVBoxLayout(missing_tab)
        self.missing_chart = ChartContainer("Missing Values")
        missing_layout.addWidget(self.missing_chart)
        tabs.addTab(missing_tab, "Missing Values")
        
        # Experiment comparison tab
        exp_tab = QWidget()
        exp_layout = QVBoxLayout(exp_tab)
        self.exp_chart = ChartContainer("Experiment Metrics Comparison")
        exp_layout.addWidget(self.exp_chart)
        tabs.addTab(exp_tab, "Experiments")
    
    def set_services(self, dataset_service, experiment_service, viz_service):
        self.dataset_service = dataset_service
        self.experiment_service = experiment_service
        self.viz_service = viz_service
        self._refresh_datasets()
    
    def _refresh_datasets(self):
        if not self.dataset_service: return
        self.dataset_combo.clear()
        self.dataset_combo.addItem("Select dataset...", None)
        for ds in self.dataset_service.get_all_datasets():
            self.dataset_combo.addItem(ds.name, ds.id)
    
    def _on_dataset_changed(self, index):
        self._refresh_charts()
    
    def _refresh_charts(self):
        ds_id = self.dataset_combo.currentData()
        if not ds_id or not self.viz_service: return
        
        dataset = self.dataset_service.get_dataset(ds_id)
        if not dataset: return
        
        # Distribution chart
        dist = self.dataset_service.get_class_distribution(dataset)
        if dist:
            fig = self.viz_service.plot_class_distribution(dist, f"{dataset.name} Distribution")
            self.dist_chart.set_chart(self.viz_service.figure_to_bytes(fig))
        
        # Missing values chart
        stats = self.dataset_service.get_statistics(dataset)
        missing = stats.get('missing_values', {})
        if missing:
            fig = self.viz_service.plot_missing_values(missing, f"{dataset.name} Missing Values")
            self.missing_chart.set_chart(self.viz_service.figure_to_bytes(fig))
        
        # Experiment comparison
        experiments = self.experiment_service.get_experiments_by_dataset(ds_id)
        if len(experiments) >= 2:
            exp_data = [{'name': e.name, 'metrics': e.metrics} for e in experiments[:5]]
            metrics = list(set(m for e in exp_data for m in e['metrics'].keys()))[:4]
            if metrics:
                fig = self.viz_service.plot_metrics_comparison(exp_data, metrics)
                self.exp_chart.set_chart(self.viz_service.figure_to_bytes(fig))
