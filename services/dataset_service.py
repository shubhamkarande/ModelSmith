"""
ModelSmith - Dataset Service
Handles dataset loading, analysis, and management.
"""

import os
import uuid
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import pandas as pd
import numpy as np
from PIL import Image

from database.db_manager import DatabaseManager
from database.models import Dataset


class DatasetService:
    """Service for managing datasets."""
    
    SUPPORTED_CSV_EXTENSIONS = ['.csv', '.tsv']
    SUPPORTED_JSON_EXTENSIONS = ['.json', '.jsonl']
    SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def import_dataset(self, path: str, name: Optional[str] = None) -> Dataset:
        """
        Import a dataset from a file or directory.
        
        Args:
            path: Path to CSV, JSON file, or image directory
            name: Optional name for the dataset
            
        Returns:
            Created Dataset object
        """
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")
        
        # Determine dataset type
        if os.path.isdir(path):
            dataset_type = 'images'
            file_size = self._get_directory_size(path)
        else:
            ext = os.path.splitext(path)[1].lower()
            if ext in self.SUPPORTED_CSV_EXTENSIONS:
                dataset_type = 'csv'
            elif ext in self.SUPPORTED_JSON_EXTENSIONS:
                dataset_type = 'json'
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            file_size = os.path.getsize(path)
        
        # Generate dataset name if not provided
        if name is None:
            name = os.path.basename(path)
        
        # Create dataset object
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name=name,
            path=path,
            type=dataset_type,
            file_size=file_size
        )
        
        # Analyze dataset
        dataset = self._analyze_dataset(dataset)
        
        # Save to database
        return self.db.create_dataset(dataset)
    
    def _analyze_dataset(self, dataset: Dataset) -> Dataset:
        """Analyze dataset and update statistics."""
        if dataset.type == 'csv':
            return self._analyze_csv(dataset)
        elif dataset.type == 'json':
            return self._analyze_json(dataset)
        elif dataset.type == 'images':
            return self._analyze_images(dataset)
        return dataset
    
    def _analyze_csv(self, dataset: Dataset) -> Dataset:
        """Analyze CSV dataset."""
        try:
            df = pd.read_csv(dataset.path, nrows=1000)  # Sample for large files
            full_df = pd.read_csv(dataset.path)
            
            dataset.row_count = len(full_df)
            dataset.column_count = len(full_df.columns)
            dataset.schema = {col: str(dtype) for col, dtype in full_df.dtypes.items()}
        except Exception as e:
            dataset.description = f"Error analyzing: {str(e)}"
        
        return dataset
    
    def _analyze_json(self, dataset: Dataset) -> Dataset:
        """Analyze JSON dataset."""
        try:
            with open(dataset.path, 'r', encoding='utf-8') as f:
                # Try to read as JSON lines first
                first_line = f.readline().strip()
                f.seek(0)
                
                if first_line.startswith('['):
                    # Regular JSON array
                    data = json.load(f)
                else:
                    # JSON lines
                    data = [json.loads(line) for line in f if line.strip()]
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.json_normalize(data)
                dataset.row_count = len(df)
                dataset.column_count = len(df.columns)
                dataset.schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
        except Exception as e:
            dataset.description = f"Error analyzing: {str(e)}"
        
        return dataset
    
    def _analyze_images(self, dataset: Dataset) -> Dataset:
        """Analyze image folder dataset."""
        try:
            image_count = 0
            classes = {}
            
            for root, dirs, files in os.walk(dataset.path):
                # Get class from folder name
                rel_path = os.path.relpath(root, dataset.path)
                class_name = rel_path if rel_path != '.' else 'root'
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.SUPPORTED_IMAGE_EXTENSIONS:
                        image_count += 1
                        classes[class_name] = classes.get(class_name, 0) + 1
            
            dataset.row_count = image_count
            dataset.column_count = len(classes)
            dataset.schema = classes
        except Exception as e:
            dataset.description = f"Error analyzing: {str(e)}"
        
        return dataset
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get a dataset by ID."""
        return self.db.get_dataset(dataset_id)
    
    def get_all_datasets(self) -> List[Dataset]:
        """Get all datasets."""
        return self.db.get_all_datasets()
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        return self.db.delete_dataset(dataset_id)
    
    def update_dataset(self, dataset: Dataset, increment_version: bool = True) -> Dataset:
        """
        Update a dataset and optionally increment its version.
        
        Args:
            dataset: Dataset object with updated fields
            increment_version: Whether to increment the version number
            
        Returns:
            Updated Dataset object
        """
        if increment_version:
            dataset.version += 1
        return self.db.update_dataset(dataset)
    
    def refresh_dataset(self, dataset_id: str) -> Dataset:
        """
        Re-analyze a dataset and update its statistics.
        Increments version number.
        
        Args:
            dataset_id: Dataset ID to refresh
            
        Returns:
            Updated Dataset object
        """
        dataset = self.db.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        # Re-analyze
        dataset = self._analyze_dataset(dataset)
        dataset.version += 1
        
        return self.db.update_dataset(dataset)
    
    def load_data(self, dataset: Dataset, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load dataset data as pandas DataFrame.
        
        Args:
            dataset: Dataset object
            limit: Maximum number of rows to load
            
        Returns:
            pandas DataFrame
        """
        if dataset.type == 'csv':
            return pd.read_csv(dataset.path, nrows=limit)
        elif dataset.type == 'json':
            with open(dataset.path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                f.seek(0)
                
                if first_line.startswith('['):
                    data = json.load(f)
                else:
                    data = [json.loads(line) for line in f if line.strip()]
            
            df = pd.json_normalize(data)
            if limit:
                df = df.head(limit)
            return df
        elif dataset.type == 'images':
            # Return DataFrame with image paths and classes
            rows = []
            for root, dirs, files in os.walk(dataset.path):
                rel_path = os.path.relpath(root, dataset.path)
                class_name = rel_path if rel_path != '.' else 'root'
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.SUPPORTED_IMAGE_EXTENSIONS:
                        rows.append({
                            'filename': file,
                            'path': os.path.join(root, file),
                            'class': class_name
                        })
                        if limit and len(rows) >= limit:
                            break
                if limit and len(rows) >= limit:
                    break
            
            return pd.DataFrame(rows)
        
        raise ValueError(f"Unknown dataset type: {dataset.type}")
    
    def get_statistics(self, dataset: Dataset) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a dataset.
        
        Returns dict with:
            - basic_stats: row count, column count, etc.
            - column_stats: per-column statistics
            - missing_values: missing value information
            - class_distribution: for classification datasets
        """
        stats = {
            'basic_stats': {
                'row_count': dataset.row_count,
                'column_count': dataset.column_count,
                'file_size': dataset.file_size,
                'type': dataset.type
            },
            'column_stats': {},
            'missing_values': {},
            'class_distribution': {}
        }
        
        try:
            df = self.load_data(dataset, limit=10000)
            
            if dataset.type in ['csv', 'json']:
                # Column statistics
                for col in df.columns:
                    col_stats = {'dtype': str(df[col].dtype)}
                    
                    if pd.api.types.is_numeric_dtype(df[col]):
                        col_stats.update({
                            'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                            'std': float(df[col].std()) if not df[col].isna().all() else None,
                            'min': float(df[col].min()) if not df[col].isna().all() else None,
                            'max': float(df[col].max()) if not df[col].isna().all() else None,
                            'median': float(df[col].median()) if not df[col].isna().all() else None
                        })
                    else:
                        col_stats.update({
                            'unique_count': int(df[col].nunique()),
                            'top_values': df[col].value_counts().head(5).to_dict()
                        })
                    
                    stats['column_stats'][col] = col_stats
                
                # Missing values
                missing = df.isnull().sum()
                stats['missing_values'] = {
                    col: {'count': int(count), 'percentage': float(count / len(df) * 100)}
                    for col, count in missing.items() if count > 0
                }
                
            elif dataset.type == 'images':
                stats['class_distribution'] = dataset.schema
        
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def detect_target_column(self, dataset: Dataset) -> Optional[str]:
        """Attempt to detect the target column for ML tasks."""
        try:
            df = self.load_data(dataset, limit=100)
            
            # Look for common target column names
            target_names = ['target', 'label', 'class', 'y', 'outcome', 'result']
            for name in target_names:
                for col in df.columns:
                    if name.lower() in col.lower():
                        return col
            
            # For image datasets, return 'class'
            if dataset.type == 'images':
                return 'class'
            
            # Return last column as fallback
            if len(df.columns) > 0:
                return df.columns[-1]
                
        except Exception:
            pass
        
        return None
    
    def get_class_distribution(self, dataset: Dataset, target_column: Optional[str] = None) -> Dict[str, int]:
        """Get class distribution for a target column."""
        try:
            df = self.load_data(dataset)
            
            if target_column is None:
                target_column = self.detect_target_column(dataset)
            
            if target_column and target_column in df.columns:
                return df[target_column].value_counts().to_dict()
            
            if dataset.type == 'images':
                return dataset.schema
                
        except Exception:
            pass
        
        return {}
