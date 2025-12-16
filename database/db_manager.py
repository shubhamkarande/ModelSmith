"""
ModelSmith - Database Manager
SQLite database connection and schema management.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from .models import Dataset, Experiment, Model, Annotation


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            home = Path.home()
            data_dir = home / "ModelSmith"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "modelsmith.db")
        
        self.db_path = db_path
        self._ensure_directory()
        self._init_schema()
    
    def _ensure_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Datasets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    row_count INTEGER DEFAULT 0,
                    column_count INTEGER DEFAULT 0,
                    file_size INTEGER DEFAULT 0,
                    schema TEXT DEFAULT '{}',
                    labels TEXT DEFAULT '{}',
                    version INTEGER DEFAULT 1
                )
            ''')
            
            # Experiments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    parameters TEXT DEFAULT '{}',
                    metrics TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    feature_columns TEXT DEFAULT '[]',
                    target_column TEXT DEFAULT '',
                    status TEXT DEFAULT 'created',
                    duration_seconds REAL DEFAULT 0.0,
                    notes TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                )
            ''')
            
            # Models table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    framework TEXT DEFAULT '',
                    version TEXT DEFAULT '1.0.0',
                    metrics TEXT DEFAULT '{}',
                    notes TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    file_size INTEGER DEFAULT 0,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                )
            ''')
            
            # Annotations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    item_index INTEGER NOT NULL,
                    item_path TEXT DEFAULT '',
                    label TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                )
            ''')
            
            # Create indexes for common queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiments_dataset ON experiments(dataset_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_experiment ON models(experiment_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotations_dataset ON annotations(dataset_id)')
            
            # Schema version tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_info (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            cursor.execute(
                'INSERT OR REPLACE INTO schema_info (key, value) VALUES (?, ?)',
                ('version', str(self.SCHEMA_VERSION))
            )
    
    # Dataset CRUD operations
    def create_dataset(self, dataset: Dataset) -> Dataset:
        """Create a new dataset record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = dataset.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            cursor.execute(
                f'INSERT INTO datasets ({columns}) VALUES ({placeholders})',
                list(data.values())
            )
        return dataset
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get a dataset by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,))
            row = cursor.fetchone()
            if row:
                return Dataset.from_dict(dict(row))
        return None
    
    def get_all_datasets(self) -> List[Dataset]:
        """Get all datasets."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM datasets ORDER BY created_at DESC')
            return [Dataset.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_dataset(self, dataset: Dataset) -> Dataset:
        """Update a dataset record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = dataset.to_dict()
            set_clause = ', '.join([f'{k} = ?' for k in data.keys() if k != 'id'])
            values = [v for k, v in data.items() if k != 'id']
            values.append(dataset.id)
            cursor.execute(
                f'UPDATE datasets SET {set_clause} WHERE id = ?',
                values
            )
        return dataset
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and its annotations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM annotations WHERE dataset_id = ?', (dataset_id,))
            cursor.execute('DELETE FROM datasets WHERE id = ?', (dataset_id,))
            return cursor.rowcount > 0
    
    # Experiment CRUD operations
    def create_experiment(self, experiment: Experiment) -> Experiment:
        """Create a new experiment record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = experiment.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            cursor.execute(
                f'INSERT INTO experiments ({columns}) VALUES ({placeholders})',
                list(data.values())
            )
        return experiment
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM experiments WHERE id = ?', (experiment_id,))
            row = cursor.fetchone()
            if row:
                return Experiment.from_dict(dict(row))
        return None
    
    def get_all_experiments(self) -> List[Experiment]:
        """Get all experiments."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM experiments ORDER BY timestamp DESC')
            return [Experiment.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def get_experiments_by_dataset(self, dataset_id: str) -> List[Experiment]:
        """Get all experiments for a dataset."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM experiments WHERE dataset_id = ? ORDER BY timestamp DESC',
                (dataset_id,)
            )
            return [Experiment.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_experiment(self, experiment: Experiment) -> Experiment:
        """Update an experiment record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = experiment.to_dict()
            set_clause = ', '.join([f'{k} = ?' for k in data.keys() if k != 'id'])
            values = [v for k, v in data.items() if k != 'id']
            values.append(experiment.id)
            cursor.execute(
                f'UPDATE experiments SET {set_clause} WHERE id = ?',
                values
            )
        return experiment
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment and its models."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM models WHERE experiment_id = ?', (experiment_id,))
            cursor.execute('DELETE FROM experiments WHERE id = ?', (experiment_id,))
            return cursor.rowcount > 0
    
    # Model CRUD operations
    def create_model(self, model: Model) -> Model:
        """Create a new model record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = model.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            cursor.execute(
                f'INSERT INTO models ({columns}) VALUES ({placeholders})',
                list(data.values())
            )
        return model
    
    def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM models WHERE id = ?', (model_id,))
            row = cursor.fetchone()
            if row:
                return Model.from_dict(dict(row))
        return None
    
    def get_all_models(self) -> List[Model]:
        """Get all models."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM models ORDER BY created_at DESC')
            return [Model.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def get_models_by_experiment(self, experiment_id: str) -> List[Model]:
        """Get all models for an experiment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM models WHERE experiment_id = ? ORDER BY created_at DESC',
                (experiment_id,)
            )
            return [Model.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_model(self, model: Model) -> Model:
        """Update a model record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = model.to_dict()
            set_clause = ', '.join([f'{k} = ?' for k in data.keys() if k != 'id'])
            values = [v for k, v in data.items() if k != 'id']
            values.append(model.id)
            cursor.execute(
                f'UPDATE models SET {set_clause} WHERE id = ?',
                values
            )
        return model
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM models WHERE id = ?', (model_id,))
            return cursor.rowcount > 0
    
    # Annotation CRUD operations
    def create_annotation(self, annotation: Annotation) -> Annotation:
        """Create a new annotation record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = annotation.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            cursor.execute(
                f'INSERT INTO annotations ({columns}) VALUES ({placeholders})',
                list(data.values())
            )
        return annotation
    
    def get_annotations_by_dataset(self, dataset_id: str) -> List[Annotation]:
        """Get all annotations for a dataset."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM annotations WHERE dataset_id = ? ORDER BY item_index',
                (dataset_id,)
            )
            return [Annotation.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_annotation(self, annotation: Annotation) -> Annotation:
        """Update an annotation record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = annotation.to_dict()
            set_clause = ', '.join([f'{k} = ?' for k in data.keys() if k != 'id'])
            values = [v for k, v in data.items() if k != 'id']
            values.append(annotation.id)
            cursor.execute(
                f'UPDATE annotations SET {set_clause} WHERE id = ?',
                values
            )
        return annotation
    
    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM annotations WHERE id = ?', (annotation_id,))
            return cursor.rowcount > 0
    
    def delete_annotations_by_dataset(self, dataset_id: str) -> int:
        """Delete all annotations for a dataset."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM annotations WHERE dataset_id = ?', (dataset_id,))
            return cursor.rowcount
