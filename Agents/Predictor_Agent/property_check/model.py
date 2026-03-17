# model.py
"""Main entry point for training property prediction models"""

import os
from model_trainer import PropertyModelTrainer
from model_evaluation import evaluate_loaded_models
from model_io import load_models
from model_utils import setup_paths, get_project_paths

# Setup import paths
current_dir, src_dir = setup_paths()
from data_processor import load_data, extract_molecular_features, create_train_test_split


def compare_saved_models(test_data_path=None, model_tg_path=None, model_er_path=None, output_path=None):
    """
    Standalone function to load saved models and compare predictions on test data.
    Useful for comparing models saved at different times or from different training runs.
    
    Args:
        test_data_path: Path to test data CSV. If None, uses default data path.
        model_tg_path: Path to saved Tg model. If None, uses default path.
        model_er_path: Path to saved Er model. If None, uses default path.
        output_path: Path to save comparison CSV. If None, saves to models directory.
    """
    trainer = PropertyModelTrainer(data_path=test_data_path)
    
    # Override model paths if provided
    if model_tg_path:
        trainer.model_tg_path = model_tg_path
    if model_er_path:
        trainer.model_er_path = model_er_path
    
    # Load data and prepare test set
    trainer.load_data()
    trainer.extract_features()
    trainer.split_data()
    
    # Load models and make predictions
    print("\n" + "="*60)
    print("Loading Models and Making Predictions")
    print("="*60)
    
    loaded_tg_model, loaded_er_model = load_models(trainer.model_tg_path, trainer.model_er_path)
    print("Models loaded successfully!")
    
    # Save results
    if output_path is None:
        output_path = os.path.join(trainer.out_dir, "loaded_model_predictions.csv")
    
    # Evaluate loaded models
    results = evaluate_loaded_models(
        loaded_tg_model, loaded_er_model,
        trainer.X_test, trainer.y_tg_test, trainer.y_er_test,
        trainer.test_smiles1, trainer.test_smiles2,
        output_path
    )
    
    return results


def main():
    """Main function to run the training pipeline"""
    trainer = PropertyModelTrainer()
    trainer.train_and_evaluate(compare_after_save=True)


if __name__ == "__main__":
    main()
