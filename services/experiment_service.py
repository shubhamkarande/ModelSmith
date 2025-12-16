"""
ModelSmith - Experiment Service
Handles experiment tracking, logging, and comparison.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import Experiment


class ExperimentService:
    """Service for managing experiments."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_experiment(
        self,
        name: str,
        dataset_id: str,
        model_type: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        feature_columns: Optional[List[str]] = None,
        target_column: str = "",
        tags: Optional[List[str]] = None
    ) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            dataset_id: ID of the dataset used
            model_type: Type of model (e.g., 'RandomForest', 'LogisticRegression')
            description: Optional description
            parameters: Model hyperparameters
            feature_columns: List of feature column names
            target_column: Target column name
            tags: Optional list of tags
            
        Returns:
            Created Experiment object
        """
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            dataset_id=dataset_id,
            model_type=model_type,
            description=description,
            parameters=parameters or {},
            feature_columns=feature_columns or [],
            target_column=target_column,
            tags=tags or [],
            status='created'
        )
        
        return self.db.create_experiment(experiment)
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID."""
        return self.db.get_experiment(experiment_id)
    
    def get_all_experiments(self) -> List[Experiment]:
        """Get all experiments."""
        return self.db.get_all_experiments()
    
    def get_experiments_by_dataset(self, dataset_id: str) -> List[Experiment]:
        """Get all experiments for a dataset."""
        return self.db.get_experiments_by_dataset(dataset_id)
    
    def start_experiment(self, experiment_id: str) -> Experiment:
        """Mark an experiment as running."""
        experiment = self.db.get_experiment(experiment_id)
        if experiment:
            experiment.status = 'running'
            experiment.timestamp = datetime.now().isoformat()
            return self.db.update_experiment(experiment)
        raise ValueError(f"Experiment not found: {experiment_id}")
    
    def log_metrics(self, experiment_id: str, metrics: Dict[str, float]) -> Experiment:
        """
        Log metrics for an experiment.
        
        Args:
            experiment_id: Experiment ID
            metrics: Dictionary of metric name -> value
            
        Returns:
            Updated Experiment object
        """
        experiment = self.db.get_experiment(experiment_id)
        if experiment:
            experiment.metrics.update(metrics)
            return self.db.update_experiment(experiment)
        raise ValueError(f"Experiment not found: {experiment_id}")
    
    def log_parameters(self, experiment_id: str, parameters: Dict[str, Any]) -> Experiment:
        """
        Log/update parameters for an experiment.
        
        Args:
            experiment_id: Experiment ID
            parameters: Dictionary of parameter name -> value
            
        Returns:
            Updated Experiment object
        """
        experiment = self.db.get_experiment(experiment_id)
        if experiment:
            experiment.parameters.update(parameters)
            return self.db.update_experiment(experiment)
        raise ValueError(f"Experiment not found: {experiment_id}")
    
    def complete_experiment(
        self,
        experiment_id: str,
        metrics: Optional[Dict[str, float]] = None,
        duration_seconds: float = 0.0,
        notes: str = ""
    ) -> Experiment:
        """
        Mark an experiment as completed.
        
        Args:
            experiment_id: Experiment ID
            metrics: Final metrics to log
            duration_seconds: Total duration
            notes: Optional completion notes
            
        Returns:
            Updated Experiment object
        """
        experiment = self.db.get_experiment(experiment_id)
        if experiment:
            experiment.status = 'completed'
            experiment.duration_seconds = duration_seconds
            if metrics:
                experiment.metrics.update(metrics)
            if notes:
                experiment.notes = notes
            return self.db.update_experiment(experiment)
        raise ValueError(f"Experiment not found: {experiment_id}")
    
    def fail_experiment(self, experiment_id: str, error_message: str) -> Experiment:
        """Mark an experiment as failed."""
        experiment = self.db.get_experiment(experiment_id)
        if experiment:
            experiment.status = 'failed'
            experiment.notes = f"Failed: {error_message}"
            return self.db.update_experiment(experiment)
        raise ValueError(f"Experiment not found: {experiment_id}")
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment."""
        return self.db.delete_experiment(experiment_id)
    
    def compare_experiments(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple experiments.
        
        Args:
            experiment_ids: List of experiment IDs to compare
            
        Returns:
            Comparison data with metrics and parameters
        """
        experiments = []
        for exp_id in experiment_ids:
            exp = self.db.get_experiment(exp_id)
            if exp:
                experiments.append(exp)
        
        if not experiments:
            return {'experiments': [], 'metrics': {}, 'parameters': {}}
        
        # Collect all unique metrics and parameters
        all_metrics = set()
        all_params = set()
        for exp in experiments:
            all_metrics.update(exp.metrics.keys())
            all_params.update(exp.parameters.keys())
        
        # Build comparison structure
        comparison = {
            'experiments': [
                {
                    'id': exp.id,
                    'name': exp.name,
                    'model_type': exp.model_type,
                    'status': exp.status,
                    'timestamp': exp.timestamp
                }
                for exp in experiments
            ],
            'metrics': {
                metric: {exp.id: exp.metrics.get(metric) for exp in experiments}
                for metric in all_metrics
            },
            'parameters': {
                param: {exp.id: exp.parameters.get(param) for exp in experiments}
                for param in all_params
            }
        }
        
        return comparison
    
    def get_best_experiment(
        self,
        dataset_id: str,
        metric: str,
        higher_is_better: bool = True
    ) -> Optional[Experiment]:
        """
        Get the best experiment for a dataset based on a metric.
        
        Args:
            dataset_id: Dataset ID
            metric: Metric name to compare
            higher_is_better: Whether higher values are better
            
        Returns:
            Best Experiment or None
        """
        experiments = self.db.get_experiments_by_dataset(dataset_id)
        
        best_exp = None
        best_value = None
        
        for exp in experiments:
            if exp.status != 'completed':
                continue
            
            value = exp.metrics.get(metric)
            if value is None:
                continue
            
            if best_value is None:
                best_exp = exp
                best_value = value
            elif higher_is_better and value > best_value:
                best_exp = exp
                best_value = value
            elif not higher_is_better and value < best_value:
                best_exp = exp
                best_value = value
        
        return best_exp
    
    def search_experiments(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_metric: Optional[Dict[str, float]] = None
    ) -> List[Experiment]:
        """
        Search experiments with filters.
        
        Args:
            model_type: Filter by model type
            status: Filter by status
            tags: Filter by tags (any match)
            min_metric: Minimum metric values
            
        Returns:
            List of matching experiments
        """
        experiments = self.db.get_all_experiments()
        
        results = []
        for exp in experiments:
            # Model type filter
            if model_type and exp.model_type != model_type:
                continue
            
            # Status filter
            if status and exp.status != status:
                continue
            
            # Tags filter
            if tags:
                if not any(tag in exp.tags for tag in tags):
                    continue
            
            # Metric filter
            if min_metric:
                passes = True
                for metric, min_val in min_metric.items():
                    if exp.metrics.get(metric, 0) < min_val:
                        passes = False
                        break
                if not passes:
                    continue
            
            results.append(exp)
        
        return results
    
    def export_report(self, experiment_id: str, output_path: str) -> str:
        """
        Export an experiment report as HTML.
        
        Args:
            experiment_id: Experiment ID
            output_path: Path to save the HTML report
            
        Returns:
            Path to the generated report
        """
        experiment = self.db.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        # Build HTML report
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Experiment Report: {experiment.name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #4fc3f7; border-bottom: 2px solid #4fc3f7; padding-bottom: 10px; }}
        h2 {{ color: #81c784; margin-top: 30px; }}
        .card {{ background: #252526; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
        .stat {{ background: #2d2d30; padding: 16px; border-radius: 6px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4fc3f7; }}
        .stat-label {{ font-size: 12px; color: #888; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #3c3c3c; }}
        th {{ background: #2d2d30; color: #4fc3f7; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .status.completed {{ background: #2e7d32; color: white; }}
        .status.running {{ background: #f57c00; color: white; }}
        .status.failed {{ background: #c62828; color: white; }}
        .status.created {{ background: #1565c0; color: white; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Experiment Report</h1>
        
        <div class="card">
            <h2 style="margin-top:0">{experiment.name}</h2>
            <p><span class="status {experiment.status}">{experiment.status.upper()}</span></p>
            <p>{experiment.description or 'No description provided.'}</p>
        </div>
        
        <h2>📊 Metrics</h2>
        <div class="grid">
"""
        
        # Add metrics cards
        for metric, value in experiment.metrics.items():
            formatted = f"{value:.4f}" if isinstance(value, float) else str(value)
            html += f"""            <div class="stat">
                <div class="stat-value">{formatted}</div>
                <div class="stat-label">{metric}</div>
            </div>
"""
        
        html += """        </div>
        
        <h2>⚙️ Parameters</h2>
        <div class="card">
            <table>
                <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
                <tbody>
"""
        
        # Add parameters
        for param, value in experiment.parameters.items():
            html += f"                    <tr><td>{param}</td><td>{value}</td></tr>\n"
        
        if not experiment.parameters:
            html += "                    <tr><td colspan='2'>No parameters logged</td></tr>\n"
        
        html += f"""                </tbody>
            </table>
        </div>
        
        <h2>📝 Details</h2>
        <div class="card">
            <table>
                <tr><td><strong>Model Type</strong></td><td>{experiment.model_type}</td></tr>
                <tr><td><strong>Created</strong></td><td>{experiment.timestamp}</td></tr>
                <tr><td><strong>Duration</strong></td><td>{experiment.duration_seconds:.1f}s</td></tr>
                <tr><td><strong>Tags</strong></td><td>{', '.join(experiment.tags) if experiment.tags else 'None'}</td></tr>
            </table>
        </div>
        
        <h2>📄 Notes</h2>
        <div class="card">
            <p>{experiment.notes or 'No notes added.'}</p>
        </div>
        
        <div class="footer">
            Generated by ModelSmith | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
