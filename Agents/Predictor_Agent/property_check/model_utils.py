# model_utils.py
"""Utility functions for model training and evaluation"""

import os
import sys
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def setup_paths():
    """Setup import paths for data_processor module"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, '..', '..')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    return current_dir, src_dir


def get_project_paths(current_dir):
    """Get project root and output directory paths"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    out_dir = os.path.join(project_root, "src", "Reward_component", "property_alignment", "models")
    os.makedirs(out_dir, exist_ok=True)
    return project_root, out_dir


def eval_regression(name, y_true, y_pred):
    """
    Evaluate regression model and return metrics
    
    Args:
        name: Name/description of the evaluation
        y_true: True target values
        y_pred: Predicted values
        
    Returns:
        Dictionary with MAE, RMSE, and R2 scores
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"\n[{name}]")
    print(f"  MAE : {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  R2  : {r2:.4f}")
    return {"mae": mae, "rmse": rmse, "r2": r2}
