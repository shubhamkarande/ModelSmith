"""
ModelSmith - Labeling Service
Handles dataset labeling and annotation management.
"""

import os
import uuid
import json
import csv
from typing import Optional, Dict, Any, List
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import Annotation, Dataset


class LabelingService:
    """Service for managing dataset labels and annotations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_label(
        self,
        dataset_id: str,
        item_index: int,
        label: str,
        item_path: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Annotation:
        """
        Add a label to a dataset item.
        
        Args:
            dataset_id: Dataset ID
            item_index: Row index for tabular, file index for images
            label: Label value
            item_path: Optional file path for image datasets
            tags: Optional list of tags
            metadata: Optional additional metadata
            
        Returns:
            Created Annotation object
        """
        annotation = Annotation(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            item_index=item_index,
            item_path=item_path,
            label=label,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        return self.db.create_annotation(annotation)
    
    def update_label(
        self,
        annotation_id: str,
        label: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Annotation:
        """Update an existing annotation."""
        annotations = self.db.get_annotations_by_dataset("")
        annotation = None
        
        # Find annotation by ID
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM annotations WHERE id = ?', (annotation_id,))
            row = cursor.fetchone()
            if row:
                annotation = Annotation.from_dict(dict(row))
        
        if not annotation:
            raise ValueError(f"Annotation not found: {annotation_id}")
        
        if label is not None:
            annotation.label = label
        if tags is not None:
            annotation.tags = tags
        if metadata is not None:
            annotation.metadata.update(metadata)
        
        annotation.updated_at = datetime.now().isoformat()
        
        return self.db.update_annotation(annotation)
    
    def get_annotations(self, dataset_id: str) -> List[Annotation]:
        """Get all annotations for a dataset."""
        return self.db.get_annotations_by_dataset(dataset_id)
    
    def get_annotation_by_index(
        self,
        dataset_id: str,
        item_index: int
    ) -> Optional[Annotation]:
        """Get annotation for a specific item index."""
        annotations = self.db.get_annotations_by_dataset(dataset_id)
        for ann in annotations:
            if ann.item_index == item_index:
                return ann
        return None
    
    def delete_label(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        return self.db.delete_annotation(annotation_id)
    
    def bulk_label(
        self,
        dataset_id: str,
        labels: List[Dict[str, Any]]
    ) -> List[Annotation]:
        """
        Add multiple labels at once.
        
        Args:
            dataset_id: Dataset ID
            labels: List of dicts with item_index, label, and optional tags
            
        Returns:
            List of created Annotation objects
        """
        annotations = []
        for label_data in labels:
            annotation = self.add_label(
                dataset_id=dataset_id,
                item_index=label_data['item_index'],
                label=label_data['label'],
                item_path=label_data.get('item_path', ''),
                tags=label_data.get('tags'),
                metadata=label_data.get('metadata')
            )
            annotations.append(annotation)
        
        return annotations
    
    def get_label_statistics(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get labeling statistics for a dataset.
        
        Returns:
            Dict with label counts, progress, etc.
        """
        annotations = self.db.get_annotations_by_dataset(dataset_id)
        dataset = self.db.get_dataset(dataset_id)
        
        if not dataset:
            return {'error': 'Dataset not found'}
        
        # Count labels
        label_counts = {}
        tag_counts = {}
        
        for ann in annotations:
            # Count labels
            if ann.label:
                label_counts[ann.label] = label_counts.get(ann.label, 0) + 1
            
            # Count tags
            for tag in ann.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            'total_items': dataset.row_count,
            'labeled_items': len(annotations),
            'unlabeled_items': max(0, dataset.row_count - len(annotations)),
            'progress_percent': (len(annotations) / dataset.row_count * 100) if dataset.row_count > 0 else 0,
            'label_distribution': label_counts,
            'tag_distribution': tag_counts,
            'unique_labels': len(label_counts),
            'unique_tags': len(tag_counts)
        }
    
    def export_annotations(
        self,
        dataset_id: str,
        output_path: str,
        format: str = 'json'
    ) -> str:
        """
        Export annotations to file.
        
        Args:
            dataset_id: Dataset ID
            output_path: Output file path
            format: 'json' or 'csv'
            
        Returns:
            Path to exported file
        """
        annotations = self.db.get_annotations_by_dataset(dataset_id)
        
        if format == 'json':
            data = [
                {
                    'item_index': ann.item_index,
                    'item_path': ann.item_path,
                    'label': ann.label,
                    'tags': ann.tags,
                    'metadata': ann.metadata,
                    'created_at': ann.created_at,
                    'updated_at': ann.updated_at
                }
                for ann in annotations
            ]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        
        elif format == 'csv':
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['item_index', 'item_path', 'label', 'tags', 'created_at'])
                
                for ann in annotations:
                    writer.writerow([
                        ann.item_index,
                        ann.item_path,
                        ann.label,
                        ';'.join(ann.tags),
                        ann.created_at
                    ])
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return output_path
    
    def import_annotations(
        self,
        dataset_id: str,
        input_path: str,
        format: str = 'json'
    ) -> List[Annotation]:
        """
        Import annotations from file.
        
        Args:
            dataset_id: Dataset ID
            input_path: Input file path
            format: 'json' or 'csv'
            
        Returns:
            List of imported Annotation objects
        """
        annotations = []
        
        if format == 'json':
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                annotation = self.add_label(
                    dataset_id=dataset_id,
                    item_index=item['item_index'],
                    label=item.get('label', ''),
                    item_path=item.get('item_path', ''),
                    tags=item.get('tags'),
                    metadata=item.get('metadata')
                )
                annotations.append(annotation)
        
        elif format == 'csv':
            with open(input_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    tags = row.get('tags', '').split(';') if row.get('tags') else []
                    annotation = self.add_label(
                        dataset_id=dataset_id,
                        item_index=int(row['item_index']),
                        label=row.get('label', ''),
                        item_path=row.get('item_path', ''),
                        tags=[t.strip() for t in tags if t.strip()]
                    )
                    annotations.append(annotation)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return annotations
    
    def clear_annotations(self, dataset_id: str) -> int:
        """Clear all annotations for a dataset."""
        return self.db.delete_annotations_by_dataset(dataset_id)
    
    def get_unlabeled_indices(self, dataset_id: str, total_items: int) -> List[int]:
        """Get list of item indices that don't have labels yet."""
        annotations = self.db.get_annotations_by_dataset(dataset_id)
        labeled_indices = {ann.item_index for ann in annotations}
        
        return [i for i in range(total_items) if i not in labeled_indices]
