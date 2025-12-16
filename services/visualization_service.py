"""
ModelSmith - Visualization Service
Handles chart generation and data visualization.
"""

import io
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from database.models import Experiment


class VisualizationService:
    """Service for generating data visualizations."""
    
    # Dark theme colors
    COLORS = {
        'background': '#1e1e1e',
        'surface': '#252526',
        'primary': '#007acc',
        'secondary': '#3c3c3c',
        'text': '#cccccc',
        'text_secondary': '#888888',
        'accent': '#0e639c',
        'success': '#4caf50',
        'warning': '#ff9800',
        'error': '#f44336',
        'chart_colors': [
            '#007acc', '#4caf50', '#ff9800', '#e91e63', 
            '#9c27b0', '#00bcd4', '#8bc34a', '#ff5722',
            '#673ab7', '#2196f3', '#cddc39', '#795548'
        ]
    }
    
    def __init__(self, dark_mode: bool = True):
        self.dark_mode = dark_mode
        self._setup_style()
    
    def _setup_style(self):
        """Set up matplotlib style for dark mode."""
        if self.dark_mode:
            plt.style.use('dark_background')
            plt.rcParams.update({
                'figure.facecolor': self.COLORS['background'],
                'axes.facecolor': self.COLORS['surface'],
                'axes.edgecolor': self.COLORS['secondary'],
                'axes.labelcolor': self.COLORS['text'],
                'text.color': self.COLORS['text'],
                'xtick.color': self.COLORS['text_secondary'],
                'ytick.color': self.COLORS['text_secondary'],
                'grid.color': self.COLORS['secondary'],
                'legend.facecolor': self.COLORS['surface'],
                'legend.edgecolor': self.COLORS['secondary'],
                'font.size': 10,
                'axes.titlesize': 12,
                'axes.labelsize': 10
            })
    
    def create_figure(self, figsize: Tuple[int, int] = (8, 6)) -> Figure:
        """Create a new figure with proper styling."""
        fig = Figure(figsize=figsize, dpi=100)
        fig.set_facecolor(self.COLORS['background'])
        return fig
    
    def figure_to_bytes(self, fig: Figure, format: str = 'png') -> bytes:
        """Convert figure to bytes for display."""
        canvas = FigureCanvasAgg(fig)
        buf = io.BytesIO()
        canvas.print_figure(buf, format=format, 
                           facecolor=fig.get_facecolor(),
                           bbox_inches='tight')
        buf.seek(0)
        return buf.read()
    
    def plot_class_distribution(
        self,
        distribution: Dict[str, int],
        title: str = "Class Distribution",
        figsize: Tuple[int, int] = (8, 6)
    ) -> Figure:
        """
        Create a bar chart of class distribution.
        
        Args:
            distribution: Dict of class name -> count
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        classes = list(distribution.keys())
        counts = list(distribution.values())
        colors = [self.COLORS['chart_colors'][i % len(self.COLORS['chart_colors'])] 
                  for i in range(len(classes))]
        
        bars = ax.bar(range(len(classes)), counts, color=colors)
        ax.set_xticks(range(len(classes)))
        ax.set_xticklabels(classes, rotation=45, ha='right')
        ax.set_xlabel('Class')
        ax.set_ylabel('Count')
        ax.set_title(title)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                   str(count), ha='center', va='bottom',
                   color=self.COLORS['text'], fontsize=9)
        
        fig.tight_layout()
        return fig
    
    def plot_pie_chart(
        self,
        data: Dict[str, float],
        title: str = "Distribution",
        figsize: Tuple[int, int] = (8, 6)
    ) -> Figure:
        """
        Create a pie chart.
        
        Args:
            data: Dict of label -> value
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        labels = list(data.keys())
        values = list(data.values())
        colors = [self.COLORS['chart_colors'][i % len(self.COLORS['chart_colors'])] 
                  for i in range(len(labels))]
        
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            colors=colors, textprops={'color': self.COLORS['text']}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
        
        ax.set_title(title)
        fig.tight_layout()
        return fig
    
    def plot_histogram(
        self,
        data: List[float],
        title: str = "Distribution",
        xlabel: str = "Value",
        bins: int = 30,
        figsize: Tuple[int, int] = (8, 6)
    ) -> Figure:
        """
        Create a histogram.
        
        Args:
            data: List of values
            title: Chart title
            xlabel: X-axis label
            bins: Number of bins
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        ax.hist(data, bins=bins, color=self.COLORS['primary'], 
                edgecolor=self.COLORS['surface'], alpha=0.8)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Frequency')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        return fig
    
    def plot_confusion_matrix(
        self,
        matrix: np.ndarray,
        labels: List[str],
        title: str = "Confusion Matrix",
        figsize: Tuple[int, int] = (8, 6)
    ) -> Figure:
        """
        Create a confusion matrix heatmap.
        
        Args:
            matrix: 2D numpy array confusion matrix
            labels: Class labels
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        im = ax.imshow(matrix, cmap='Blues')
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax)
        cbar.ax.yaxis.set_tick_params(color=self.COLORS['text'])
        
        # Set ticks and labels
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_yticklabels(labels)
        
        # Add cell annotations
        for i in range(len(labels)):
            for j in range(len(labels)):
                text = ax.text(j, i, f'{matrix[i, j]:.0f}',
                              ha='center', va='center',
                              color='white' if matrix[i, j] > matrix.max()/2 else 'black')
        
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title(title)
        
        fig.tight_layout()
        return fig
    
    def plot_metrics_comparison(
        self,
        experiments: List[Dict[str, Any]],
        metrics: List[str],
        title: str = "Experiment Comparison",
        figsize: Tuple[int, int] = (10, 6)
    ) -> Figure:
        """
        Create a grouped bar chart comparing metrics across experiments.
        
        Args:
            experiments: List of dicts with 'name' and 'metrics' keys
            metrics: List of metric names to compare
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        n_experiments = len(experiments)
        n_metrics = len(metrics)
        bar_width = 0.8 / n_experiments
        
        for i, exp in enumerate(experiments):
            values = [exp.get('metrics', {}).get(m, 0) for m in metrics]
            positions = [j + i * bar_width for j in range(n_metrics)]
            color = self.COLORS['chart_colors'][i % len(self.COLORS['chart_colors'])]
            ax.bar(positions, values, bar_width, label=exp.get('name', f'Exp {i+1}'),
                  color=color)
        
        ax.set_xticks([j + bar_width * (n_experiments - 1) / 2 for j in range(n_metrics)])
        ax.set_xticklabels(metrics, rotation=45, ha='right')
        ax.set_ylabel('Value')
        ax.set_title(title)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
        
        fig.tight_layout()
        return fig
    
    def plot_accuracy_trend(
        self,
        timestamps: List[str],
        accuracies: List[float],
        title: str = "Accuracy Trend",
        figsize: Tuple[int, int] = (10, 6)
    ) -> Figure:
        """
        Create a line chart showing accuracy over time.
        
        Args:
            timestamps: List of timestamp strings
            accuracies: List of accuracy values
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        x = range(len(timestamps))
        ax.plot(x, accuracies, marker='o', color=self.COLORS['primary'],
               linewidth=2, markersize=8)
        ax.fill_between(x, accuracies, alpha=0.2, color=self.COLORS['primary'])
        
        ax.set_xticks(x)
        ax.set_xticklabels(timestamps, rotation=45, ha='right')
        ax.set_ylabel('Accuracy')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        # Add value annotations
        for i, (xi, yi) in enumerate(zip(x, accuracies)):
            ax.annotate(f'{yi:.2f}', (xi, yi), textcoords='offset points',
                       xytext=(0, 10), ha='center', fontsize=9,
                       color=self.COLORS['text'])
        
        fig.tight_layout()
        return fig
    
    def plot_feature_importance(
        self,
        features: List[str],
        importances: List[float],
        title: str = "Feature Importance",
        figsize: Tuple[int, int] = (8, 6)
    ) -> Figure:
        """
        Create a horizontal bar chart of feature importances.
        
        Args:
            features: List of feature names
            importances: List of importance values
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        # Sort by importance
        sorted_idx = np.argsort(importances)
        features = [features[i] for i in sorted_idx]
        importances = [importances[i] for i in sorted_idx]
        
        colors = [self.COLORS['primary'] if imp > 0 else self.COLORS['error'] 
                  for imp in importances]
        
        ax.barh(range(len(features)), importances, color=colors)
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features)
        ax.set_xlabel('Importance')
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis='x')
        
        fig.tight_layout()
        return fig
    
    def plot_missing_values(
        self,
        missing_data: Dict[str, Dict[str, Any]],
        title: str = "Missing Values",
        figsize: Tuple[int, int] = (10, 6)
    ) -> Figure:
        """
        Create a bar chart showing missing values per column.
        
        Args:
            missing_data: Dict of column -> {'count': n, 'percentage': p}
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        if not missing_data:
            ax.text(0.5, 0.5, 'No missing values', ha='center', va='center',
                   fontsize=14, color=self.COLORS['text'])
            ax.set_title(title)
            return fig
        
        columns = list(missing_data.keys())
        percentages = [missing_data[col]['percentage'] for col in columns]
        counts = [missing_data[col]['count'] for col in columns]
        
        bars = ax.bar(range(len(columns)), percentages, 
                     color=self.COLORS['warning'])
        ax.set_xticks(range(len(columns)))
        ax.set_xticklabels(columns, rotation=45, ha='right')
        ax.set_ylabel('Missing %')
        ax.set_title(title)
        
        # Add count labels
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                   f'n={count}', ha='center', va='bottom',
                   color=self.COLORS['text'], fontsize=9)
        
        fig.tight_layout()
        return fig
    
    def plot_correlation_matrix(
        self,
        df: pd.DataFrame,
        title: str = "Correlation Matrix",
        figsize: Tuple[int, int] = (10, 8)
    ) -> Figure:
        """
        Create a correlation matrix heatmap.
        
        Args:
            df: pandas DataFrame with numeric columns
            title: Chart title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig = self.create_figure(figsize)
        ax = fig.add_subplot(111)
        
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        corr = numeric_df.corr()
        
        im = ax.imshow(corr, cmap='RdYlBu', vmin=-1, vmax=1)
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax)
        
        # Set ticks and labels
        columns = corr.columns.tolist()
        ax.set_xticks(range(len(columns)))
        ax.set_yticks(range(len(columns)))
        ax.set_xticklabels(columns, rotation=45, ha='right')
        ax.set_yticklabels(columns)
        
        # Add correlation values
        for i in range(len(columns)):
            for j in range(len(columns)):
                val = corr.iloc[i, j]
                color = 'white' if abs(val) > 0.5 else 'black'
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                       color=color, fontsize=8)
        
        ax.set_title(title)
        fig.tight_layout()
        return fig
