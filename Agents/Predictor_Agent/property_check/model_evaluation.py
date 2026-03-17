# model_evaluation.py
"""Model evaluation and comparison functions"""

import os
import numpy as np
import pandas as pd
from model_utils import eval_regression


def compare_models(current_tg_pred, current_er_pred, loaded_tg_pred, loaded_er_pred,
                   y_tg_test, y_er_test, test_smiles1, test_smiles2, output_path):
    """
    Compare predictions from current models vs loaded models and save to CSV
    
    Args:
        current_tg_pred: Predictions from current Tg model
        current_er_pred: Predictions from current Er model
        loaded_tg_pred: Predictions from loaded Tg model
        loaded_er_pred: Predictions from loaded Er model
        y_tg_test: True Tg values
        y_er_test: True Er values
        test_smiles1: List of SMILES strings for component 1
        test_smiles2: List of SMILES strings for component 2
        output_path: Path to save comparison CSV
        
    Returns:
        Dictionary with comparison statistics
    """
    # Calculate differences
    tg_diff = current_tg_pred - loaded_tg_pred
    er_diff = current_er_pred - loaded_er_pred
    
    tg_abs_diff = np.abs(tg_diff)
    er_abs_diff = np.abs(er_diff)
    
    # Calculate max differences
    tg_max_diff = np.max(tg_abs_diff)
    er_max_diff = np.max(er_abs_diff)
    
    # Check if predictions are identical (within numerical precision)
    tg_identical = np.allclose(current_tg_pred, loaded_tg_pred, rtol=1e-10, atol=1e-10)
    er_identical = np.allclose(current_er_pred, loaded_er_pred, rtol=1e-10, atol=1e-10)
    
    print("\n" + "-"*60)
    print("Comparison Summary:")
    print("-"*60)
    print(f"Tg Model:")
    print(f"  Max absolute difference: {tg_max_diff:.10f}")
    print(f"  Mean absolute difference: {np.mean(tg_abs_diff):.10f}")
    print(f"  Predictions identical: {tg_identical}")
    print(f"\nEr Model:")
    print(f"  Max absolute difference: {er_max_diff:.10f}")
    print(f"  Mean absolute difference: {np.mean(er_abs_diff):.10f}")
    print(f"  Predictions identical: {er_identical}")
    print("-"*60)
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame({
        'Sample_Index': range(len(y_tg_test)),
        'SMILES_1': test_smiles1,
        'SMILES_2': test_smiles2,
        # Tg predictions
        'Tg_Current_Predicted': current_tg_pred,
        'Tg_Loaded_Predicted': loaded_tg_pred,
        'Tg_Difference': tg_diff,
        'Tg_Absolute_Difference': tg_abs_diff,
        # Er predictions
        'Er_Current_Predicted': current_er_pred,
        'Er_Loaded_Predicted': loaded_er_pred,
        'Er_Difference': er_diff,
        'Er_Absolute_Difference': er_abs_diff,
        # Actual values for reference
        'Tg_Actual': y_tg_test,
        'Er_Actual': y_er_test
    })
    
    # Add summary row
    summary_row = pd.DataFrame({
        'Sample_Index': ['SUMMARY'],
        'SMILES_1': [f'Tg Max Diff: {tg_max_diff:.10f}, Mean Diff: {np.mean(tg_abs_diff):.10f}, Identical: {tg_identical}'],
        'SMILES_2': [f'Er Max Diff: {er_max_diff:.10f}, Mean Diff: {np.mean(er_abs_diff):.10f}, Identical: {er_identical}'],
        'Tg_Current_Predicted': ['Tg Comparison'],
        'Tg_Loaded_Predicted': [''],
        'Tg_Difference': [''],
        'Tg_Absolute_Difference': [''],
        'Er_Current_Predicted': ['Er Comparison'],
        'Er_Loaded_Predicted': [''],
        'Er_Difference': [''],
        'Er_Absolute_Difference': [''],
        'Tg_Actual': [''],
        'Er_Actual': ['']
    })
    
    comparison_df = pd.concat([comparison_df, summary_row], ignore_index=True)
    
    # Save to CSV
    comparison_df.to_csv(output_path, index=False)
    print(f"\nComparison results saved to: {output_path}")
    print(f"CSV contains {len(y_tg_test)} test samples with current vs loaded model predictions")
    
    return {
        'tg_max_diff': tg_max_diff,
        'tg_mean_diff': np.mean(tg_abs_diff),
        'tg_identical': tg_identical,
        'er_max_diff': er_max_diff,
        'er_mean_diff': np.mean(er_abs_diff),
        'er_identical': er_identical
    }


def evaluate_loaded_models(loaded_tg_model, loaded_er_model, X_test, y_tg_test, y_er_test,
                          test_smiles1, test_smiles2, output_path):
    """
    Evaluate loaded models on test data and save predictions to CSV
    
    Args:
        loaded_tg_model: Loaded Tg model
        loaded_er_model: Loaded Er model
        X_test: Test features
        y_tg_test: True Tg values
        y_er_test: True Er values
        test_smiles1: List of SMILES strings for component 1
        test_smiles2: List of SMILES strings for component 2
        output_path: Path to save predictions CSV
        
    Returns:
        Dictionary with metrics and predictions DataFrame
    """
    # Make predictions
    loaded_y_tg_pred = loaded_tg_model.predict(X_test)
    loaded_y_er_pred_log = loaded_er_model.predict(X_test)
    loaded_y_er_pred = np.expm1(loaded_y_er_pred_log)
    
    # Evaluate loaded models
    print("\nEvaluating loaded models on test set...")
    tg_metrics = eval_regression("Tg (loaded model)", y_tg_test, loaded_y_tg_pred)
    er_metrics = eval_regression("Er (loaded model)", y_er_test, loaded_y_er_pred)
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'Sample_Index': range(len(y_tg_test)),
        'SMILES_1': test_smiles1,
        'SMILES_2': test_smiles2,
        'Tg_Actual': y_tg_test,
        'Tg_Predicted': loaded_y_tg_pred,
        'Tg_Absolute_Error': np.abs(y_tg_test - loaded_y_tg_pred),
        'Er_Actual': y_er_test,
        'Er_Predicted': loaded_y_er_pred,
        'Er_Absolute_Error': np.abs(y_er_test - loaded_y_er_pred)
    })
    
    summary_row = pd.DataFrame({
        'Sample_Index': ['SUMMARY'],
        'SMILES_1': [f'Tg - MAE: {tg_metrics["mae"]:.4f}, RMSE: {tg_metrics["rmse"]:.4f}, R2: {tg_metrics["r2"]:.4f}'],
        'SMILES_2': [f'Er - MAE: {er_metrics["mae"]:.4f}, RMSE: {er_metrics["rmse"]:.4f}, R2: {er_metrics["r2"]:.4f}'],
        'Tg_Actual': ['Tg Metrics'],
        'Tg_Predicted': [''],
        'Tg_Absolute_Error': [''],
        'Er_Actual': ['Er Metrics'],
        'Er_Predicted': [''],
        'Er_Absolute_Error': ['']
    })
    
    results_df = pd.concat([results_df, summary_row], ignore_index=True)
    results_df.to_csv(output_path, index=False)
    
    print(f"\nLoaded model predictions saved to: {output_path}")
    
    return {
        'tg_metrics': tg_metrics,
        'er_metrics': er_metrics,
        'predictions_df': results_df
    }
