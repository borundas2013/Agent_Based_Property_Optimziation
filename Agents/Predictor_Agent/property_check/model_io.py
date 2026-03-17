# model_io.py
"""Model saving, loading, and CSV export utilities"""

import json
import os
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import mean_squared_error


def _metadata_path(model_path: str) -> str:
    return f"{model_path}.meta.json"


def _write_metadata(model_path: str) -> None:
    meta = {
        "sklearn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
    }
    meta_path = _metadata_path(model_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def _read_metadata(model_path: str):
    meta_path = _metadata_path(model_path)
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_models(tg_model, er_model, model_tg_path, model_er_path):
    """
    Save trained models to disk
    
    Args:
        tg_model: Trained Tg model
        er_model: Trained Er model
        model_tg_path: Path to save Tg model
        model_er_path: Path to save Er model
    """
    joblib.dump(tg_model, model_tg_path)
    joblib.dump(er_model, model_er_path)
    _write_metadata(model_tg_path)
    _write_metadata(model_er_path)
    
    print("\nSaved models:")
    print(f"  Tg model -> {model_tg_path}")
    print(f"  Er model -> {model_er_path}")


def load_models(model_tg_path, model_er_path):
    """
    Load models from disk
    
    Args:
        model_tg_path: Path to Tg model file
        model_er_path: Path to Er model file
        
    Returns:
        Tuple of (tg_model, er_model)
    """
    if not os.path.exists(model_tg_path):
        raise FileNotFoundError(f"Tg model file not found: {model_tg_path}")
    if not os.path.exists(model_er_path):
        raise FileNotFoundError(f"Er model file not found: {model_er_path}")
    
    tg_meta = _read_metadata(model_tg_path)
    er_meta = _read_metadata(model_er_path)

    try:
        tg_model = joblib.load(model_tg_path)
        er_model = joblib.load(model_er_path)
    except AttributeError as exc:
        hint = (
            "Model pickle load failed; this is usually a scikit-learn version "
            "mismatch. Recreate the environment with the same scikit-learn version "
            "used to train/save the model, or retrain and resave the model."
        )
        if tg_meta or er_meta:
            hint += f" Detected metadata: tg={tg_meta}, er={er_meta}."
        hint += f" Current scikit-learn: {sklearn.__version__}."
        raise RuntimeError(hint) from exc
    
    return tg_model, er_model


def save_test_results_csv(y_tg_test, y_tg_pred, y_er_test, y_er_pred, 
                          test_smiles1, test_smiles2, tg_metrics, er_metrics,
                          output_path):
    """
    Save test results to CSV with side-by-side comparison and errors
    
    Args:
        y_tg_test: True Tg values
        y_tg_pred: Predicted Tg values
        y_er_test: True Er values
        y_er_pred: Predicted Er values
        test_smiles1: List of SMILES strings for component 1
        test_smiles2: List of SMILES strings for component 2
        tg_metrics: Dictionary with Tg evaluation metrics
        er_metrics: Dictionary with Er evaluation metrics
        output_path: Path to save CSV file
    """
    # Calculate absolute errors for each sample
    tg_abs_error = np.abs(y_tg_test - y_tg_pred)
    er_abs_error = np.abs(y_er_test - y_er_pred)
    
    # Create DataFrame with side-by-side results
    results_df = pd.DataFrame({
        'Sample_Index': range(len(y_tg_test)),
        'SMILES_1': test_smiles1,
        'SMILES_2': test_smiles2,
        'Tg_Actual': y_tg_test,
        'Tg_Predicted': y_tg_pred,
        'Tg_Absolute_Error': tg_abs_error,
        'Er_Actual': y_er_test,
        'Er_Predicted': y_er_pred,
        'Er_Absolute_Error': er_abs_error
    })
    
    # Add overall metrics as a summary row at the end
    summary_row = pd.DataFrame({
        'Sample_Index': ['SUMMARY'],
        'SMILES_1': [f'MAE: {tg_metrics["mae"]:.4f}, RMSE: {np.sqrt(mean_squared_error(y_tg_test, y_tg_pred)):.4f}, R2: {tg_metrics["r2"]:.4f}'],
        'SMILES_2': [f'MAE: {er_metrics["mae"]:.4f}, RMSE: {np.sqrt(mean_squared_error(y_er_test, y_er_pred)):.4f}, R2: {er_metrics["r2"]:.4f}'],
        'Tg_Actual': ['Tg Metrics'],
        'Tg_Predicted': [''],
        'Tg_Absolute_Error': [''],
        'Er_Actual': ['Er Metrics'],
        'Er_Predicted': [''],
        'Er_Absolute_Error': ['']
    })
    
    results_df = pd.concat([results_df, summary_row], ignore_index=True)
    
    # Save to CSV
    results_df.to_csv(output_path, index=False)
    print(f"\nTest results saved to: {output_path}")
    print(f"CSV contains {len(y_tg_test)} test samples with actual vs predicted values and errors")
