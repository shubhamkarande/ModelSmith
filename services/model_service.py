"""
ModelSmith - Model Service
Handles model registration and management.
"""

import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import Model


class ModelService:
    """Service for managing registered models."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def register_model(
        self,
        name: str,
        experiment_id: str,
        file_path: str,
        framework: str = "",
        version: str = "1.0.0",
        metrics: Optional[Dict[str, float]] = None,
        notes: str = "",
        tags: Optional[List[str]] = None
    ) -> Model:
        """
        Register a new model.
        
        Args:
            name: Model name
            experiment_id: ID of the experiment that produced this model
            file_path: Path to the model file
            framework: ML framework (sklearn, pytorch, etc.)
            version: Model version
            metrics: Performance metrics
            notes: Optional notes
            tags: Optional tags
            
        Returns:
            Created Model object
        """
        file_path = os.path.abspath(file_path)
        
        # Get file size if file exists
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        model = Model(
            id=str(uuid.uuid4()),
            name=name,
            experiment_id=experiment_id,
            file_path=file_path,
            framework=framework,
            version=version,
            metrics=metrics or {},
            notes=notes,
            tags=tags or [],
            file_size=file_size
        )
        
        return self.db.create_model(model)
    
    def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        return self.db.get_model(model_id)
    
    def get_all_models(self) -> List[Model]:
        """Get all models."""
        return self.db.get_all_models()
    
    def get_models_by_experiment(self, experiment_id: str) -> List[Model]:
        """Get all models for an experiment."""
        return self.db.get_models_by_experiment(experiment_id)
    
    def update_model(
        self,
        model_id: str,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metrics: Optional[Dict[str, float]] = None
    ) -> Model:
        """
        Update model metadata.
        
        Args:
            model_id: Model ID
            notes: New notes (None to keep existing)
            tags: New tags (None to keep existing)
            metrics: Additional metrics to add
            
        Returns:
            Updated Model object
        """
        model = self.db.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        if notes is not None:
            model.notes = notes
        if tags is not None:
            model.tags = tags
        if metrics:
            model.metrics.update(metrics)
        
        return self.db.update_model(model)
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        return self.db.delete_model(model_id)
    
    def get_model_with_experiment(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a model with its experiment details.
        
        Returns:
            Dict with model and experiment info
        """
        model = self.db.get_model(model_id)
        if not model:
            return None
        
        experiment = self.db.get_experiment(model.experiment_id)
        
        return {
            'model': model,
            'experiment': experiment
        }
    
    def search_models(
        self,
        framework: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_metric: Optional[Dict[str, float]] = None
    ) -> List[Model]:
        """
        Search models with filters.
        
        Args:
            framework: Filter by framework
            tags: Filter by tags (any match)
            min_metric: Minimum metric values
            
        Returns:
            List of matching models
        """
        models = self.db.get_all_models()
        
        results = []
        for model in models:
            # Framework filter
            if framework and model.framework != framework:
                continue
            
            # Tags filter
            if tags:
                if not any(tag in model.tags for tag in tags):
                    continue
            
            # Metric filter
            if min_metric:
                passes = True
                for metric, min_val in min_metric.items():
                    if model.metrics.get(metric, 0) < min_val:
                        passes = False
                        break
                if not passes:
                    continue
            
            results.append(model)
        
        return results
    
    def get_latest_version(self, name: str) -> Optional[Model]:
        """Get the latest version of a model by name."""
        models = self.db.get_all_models()
        
        matching = [m for m in models if m.name == name]
        if not matching:
            return None
        
        # Sort by version (simple string comparison)
        matching.sort(key=lambda m: m.version, reverse=True)
        return matching[0]
    
    def increment_version(self, model_id: str) -> Model:
        """
        Create a new version of a model.
        Increments the patch version (e.g., 1.0.0 -> 1.0.1).
        """
        model = self.db.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        # Parse and increment version
        parts = model.version.split('.')
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
            model.version = '.'.join(parts)
        else:
            model.version = model.version + '.1'
        
        return self.db.update_model(model)
    
    def verify_model_file(self, model_id: str) -> Dict[str, Any]:
        """
        Verify that a model file exists and is accessible.
        
        Returns:
            Dict with verification status and details
        """
        model = self.db.get_model(model_id)
        if not model:
            return {'exists': False, 'error': 'Model not found'}
        
        result = {
            'model_id': model_id,
            'file_path': model.file_path,
            'exists': os.path.exists(model.file_path)
        }
        
        if result['exists']:
            result['file_size'] = os.path.getsize(model.file_path)
            result['modified_time'] = datetime.fromtimestamp(
                os.path.getmtime(model.file_path)
            ).isoformat()
        else:
            result['error'] = 'Model file not found'
        
        return result
