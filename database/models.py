"""
ModelSmith - Data Models
Dataclasses for datasets, experiments, and models.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class Dataset:
    """Represents a dataset in ModelSmith."""
    id: str
    name: str
    path: str
    type: str  # 'csv', 'json', 'images'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    row_count: int = 0
    column_count: int = 0
    file_size: int = 0
    schema: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'type': self.type,
            'created_at': self.created_at,
            'description': self.description,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'file_size': self.file_size,
            'schema': json.dumps(self.schema),
            'labels': json.dumps(self.labels),
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dataset':
        schema = data.get('schema', '{}')
        labels = data.get('labels', '{}')
        return cls(
            id=data['id'],
            name=data['name'],
            path=data['path'],
            type=data['type'],
            created_at=data.get('created_at', datetime.now().isoformat()),
            description=data.get('description', ''),
            row_count=data.get('row_count', 0),
            column_count=data.get('column_count', 0),
            file_size=data.get('file_size', 0),
            schema=json.loads(schema) if isinstance(schema, str) else schema,
            labels=json.loads(labels) if isinstance(labels, str) else labels,
            version=data.get('version', 1)
        )


@dataclass
class Experiment:
    """Represents an ML experiment in ModelSmith."""
    id: str
    name: str
    dataset_id: str
    model_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    feature_columns: List[str] = field(default_factory=list)
    target_column: str = ""
    status: str = "created"  # created, running, completed, failed
    duration_seconds: float = 0.0
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'dataset_id': self.dataset_id,
            'model_type': self.model_type,
            'parameters': json.dumps(self.parameters),
            'metrics': json.dumps(self.metrics),
            'timestamp': self.timestamp,
            'description': self.description,
            'feature_columns': json.dumps(self.feature_columns),
            'target_column': self.target_column,
            'status': self.status,
            'duration_seconds': self.duration_seconds,
            'notes': self.notes,
            'tags': json.dumps(self.tags)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experiment':
        return cls(
            id=data['id'],
            name=data['name'],
            dataset_id=data['dataset_id'],
            model_type=data['model_type'],
            parameters=json.loads(data.get('parameters', '{}')),
            metrics=json.loads(data.get('metrics', '{}')),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            description=data.get('description', ''),
            feature_columns=json.loads(data.get('feature_columns', '[]')),
            target_column=data.get('target_column', ''),
            status=data.get('status', 'created'),
            duration_seconds=data.get('duration_seconds', 0.0),
            notes=data.get('notes', ''),
            tags=json.loads(data.get('tags', '[]'))
        )


@dataclass
class Model:
    """Represents a registered model in ModelSmith."""
    id: str
    name: str
    experiment_id: str
    file_path: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    framework: str = ""  # sklearn, pytorch, tensorflow, etc.
    version: str = "1.0.0"
    metrics: Dict[str, float] = field(default_factory=dict)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    file_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'experiment_id': self.experiment_id,
            'file_path': self.file_path,
            'created_at': self.created_at,
            'framework': self.framework,
            'version': self.version,
            'metrics': json.dumps(self.metrics),
            'notes': self.notes,
            'tags': json.dumps(self.tags),
            'file_size': self.file_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Model':
        return cls(
            id=data['id'],
            name=data['name'],
            experiment_id=data['experiment_id'],
            file_path=data['file_path'],
            created_at=data.get('created_at', datetime.now().isoformat()),
            framework=data.get('framework', ''),
            version=data.get('version', '1.0.0'),
            metrics=json.loads(data.get('metrics', '{}')),
            notes=data.get('notes', ''),
            tags=json.loads(data.get('tags', '[]')),
            file_size=data.get('file_size', 0)
        )


@dataclass
class Annotation:
    """Represents a label/annotation for a dataset item."""
    id: str
    dataset_id: str
    item_index: int  # Row index for tabular, file index for images
    item_path: str = ""  # For image datasets
    label: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'item_index': self.item_index,
            'item_path': self.item_path,
            'label': self.label,
            'tags': json.dumps(self.tags),
            'metadata': json.dumps(self.metadata),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Annotation':
        return cls(
            id=data['id'],
            dataset_id=data['dataset_id'],
            item_index=data['item_index'],
            item_path=data.get('item_path', ''),
            label=data.get('label', ''),
            tags=json.loads(data.get('tags', '[]')),
            metadata=json.loads(data.get('metadata', '{}')),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat())
        )
