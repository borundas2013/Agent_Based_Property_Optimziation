# model_trainer.py
"""Main PropertyModelTrainer class for training property prediction models"""

import os
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupShuffleSplit

from model_utils import setup_paths, get_project_paths, eval_regression
from model_io import save_models, load_models, save_test_results_csv
from model_evaluation import compare_models

# Setup import paths
current_dir, src_dir = setup_paths()
from data_processor import load_data, extract_molecular_features, create_train_test_split, create_groups


class PropertyModelTrainer:
    """Class for training and evaluating property prediction models"""
    
    def __init__(self, data_path=None, test_size=0.2, random_state=42):
        """
        Initialize the PropertyModelTrainer
        
        Args:
            data_path: Path to the data CSV file
            test_size: Proportion of data to use for testing
            random_state: Random state for reproducibility
        """
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root, self.out_dir = get_project_paths(self.current_dir)
        
        if data_path is None:
            self.data_path = os.path.join(self.project_root, "data", "unique_smiles_Er.csv")
        else:
            self.data_path = data_path
            
        self.test_size = test_size
        self.random_state = random_state
        
        self.model_tg_path = os.path.join(self.out_dir, "tg_hgb_with_G.pkl")
        self.model_er_path = os.path.join(self.out_dir, "er_hgb_log1p_with_G.pkl")
        
        # Data attributes
        self.smiles1_list = None
        self.smiles2_list = None
        self.tg_list = None
        self.er_list = None
        self.ratio1_list = None
        self.ratio2_list = None
        self.X = None
        self.y_tg = None
        self.y_er = None
        
        # Train/test split attributes
        self.X_train = None
        self.X_test = None
        self.y_tg_train = None
        self.y_tg_test = None
        self.y_er_train = None
        self.y_er_test = None
        self.y_er_train_log = None
        self.y_er_test_log = None
        self.test_indices = None
        self.test_smiles1 = None
        self.test_smiles2 = None
        
        # Models
        self.tg_model = None
        self.er_model = None
        
        # Predictions
        self.y_tg_pred = None
        self.y_er_pred_log = None
        self.y_er_pred = None
        
        # Evaluation metrics
        self.tg_metrics = None
        self.er_log_metrics = None
        self.er_metrics = None
    
    def load_data(self):
        """Load data from CSV file"""
        self.smiles1_list, self.smiles2_list, self.tg_list, self.er_list, \
            self.ratio1_list, self.ratio2_list = load_data(self.data_path)
    
    def extract_features(self):
        """Extract molecular features"""
        self.X = extract_molecular_features(
            self.smiles1_list,
            self.smiles2_list,
            ratio1_list=self.ratio1_list,
            ratio2_list=self.ratio2_list,
            fp_bits=1024,
            use_symmetric=True
        )
        
        self.y_tg = np.array(self.tg_list, dtype=np.float32)
        self.y_er = np.array(self.er_list, dtype=np.float32)
    
    def split_data(self):
        """Create train/test split and track test indices for CSV output"""
        # Use create_train_test_split for the actual split
        self.X_train, self.X_test, self.y_tg_train, self.y_tg_test, self.y_er_train, self.y_er_test = create_train_test_split(
            self.X, self.y_tg, self.y_er,
            smiles1_list=self.smiles1_list,
            smiles2_list=self.smiles2_list,
            test_size=self.test_size,
            random_state=self.random_state,
            use_group_split=True
        )
        
        # Get test indices for tracking purposes
        try:
            groups = create_groups(self.smiles1_list, self.smiles2_list)
        except Exception:
            groups = [f"{s1}|{s2}" for s1, s2 in zip(self.smiles1_list, self.smiles2_list)]
        
        gss = GroupShuffleSplit(n_splits=1, test_size=self.test_size, random_state=self.random_state)
        train_idx, test_idx = next(gss.split(self.X, self.y_tg, groups))
        
        # Store test indices and corresponding SMILES
        self.test_indices = test_idx
        self.test_smiles1 = [self.smiles1_list[i] for i in test_idx]
        self.test_smiles2 = [self.smiles2_list[i] for i in test_idx]
        
        # Transform Er (recommended)
        self.y_er_train_log = np.log1p(self.y_er_train)
        self.y_er_test_log = np.log1p(self.y_er_test)
        
        print(f"Training set: {len(self.X_train)} samples")
        print(f"Test set: {len(self.X_test)} samples")
        print(f"Feature dimensions: {self.X_train.shape[1]}")
    
    def initialize_models(self):
        """Initialize the models with same parameters as before"""
        # Good defaults for ~1k samples; you can tune later.
        self.tg_model = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.05,
            max_depth=6,
            max_iter=600,
            min_samples_leaf=15,
            l2_regularization=1e-3,
            random_state=42
        )
        
        self.er_model = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.05,
            max_depth=6,
            max_iter=600,
            min_samples_leaf=15,
            l2_regularization=1e-3,
            random_state=42
        )
    
    def train_models(self):
        """Train both models"""
        print("\nTraining Tg model...")
        self.tg_model.fit(self.X_train, self.y_tg_train)
        
        print("Training Er model (log1p)...")
        self.er_model.fit(self.X_train, self.y_er_train_log)
    
    def predict(self):
        """Make predictions on test set"""
        # Tg predictions
        self.y_tg_pred = self.tg_model.predict(self.X_test)
        
        # Er predictions (log space)
        self.y_er_pred_log = self.er_model.predict(self.X_test)
        
        # Er predictions (original scale)
        self.y_er_pred = np.expm1(self.y_er_pred_log)
    
    def evaluate_models(self):
        """Evaluate both models"""
        # Tg evaluation
        self.tg_metrics = eval_regression("Tg (test)", self.y_tg_test, self.y_tg_pred)
        
        # Er (log space) evaluation
        self.er_log_metrics = eval_regression("Er log1p (test)", self.y_er_test_log, self.y_er_pred_log)
        
        # Er (original scale) evaluation
        self.er_metrics = eval_regression("Er original scale (test)", self.y_er_test, self.y_er_pred)
    
    def save_models(self):
        """Save trained models"""
        save_models(self.tg_model, self.er_model, self.model_tg_path, self.model_er_path)
    
    def save_test_results_csv(self, output_path=None):
        """Save test results to CSV with side-by-side comparison and errors"""
        if output_path is None:
            output_path = os.path.join(self.out_dir, "test_results.csv")
        
        save_test_results_csv(
            self.y_tg_test, self.y_tg_pred,
            self.y_er_test, self.y_er_pred,
            self.test_smiles1, self.test_smiles2,
            self.tg_metrics, self.er_metrics,
            output_path
        )
    
    def compare_with_loaded_models(self, output_path=None):
        """
        Load saved models, predict on test data, and compare with current model predictions.
        This verifies that models are saved and loaded correctly.
        
        Args:
            output_path: Path to save comparison CSV. If None, saves to models directory.
        """
        if self.tg_model is None or self.er_model is None:
            raise ValueError("Current models are not trained. Please train models first.")
        
        if self.X_test is None:
            raise ValueError("Test data is not available. Please run split_data() first.")
        
        print("\n" + "="*60)
        print("Comparing Current Models vs Loaded Models")
        print("="*60)
        
        # Load models from disk
        print(f"\nLoading models from disk...")
        print(f"  Tg model: {self.model_tg_path}")
        print(f"  Er model: {self.model_er_path}")
        
        loaded_tg_model, loaded_er_model = load_models(self.model_tg_path, self.model_er_path)
        print("Models loaded successfully!")
        
        # Make predictions with loaded models
        print("\nMaking predictions with loaded models...")
        loaded_y_tg_pred = loaded_tg_model.predict(self.X_test)
        loaded_y_er_pred_log = loaded_er_model.predict(self.X_test)
        loaded_y_er_pred = np.expm1(loaded_y_er_pred_log)
        
        # Ensure current predictions exist
        if self.y_tg_pred is None or self.y_er_pred is None:
            print("Current predictions not available. Generating predictions...")
            self.predict()
        
        # Set output path
        if output_path is None:
            output_path = os.path.join(self.out_dir, "model_comparison.csv")
        
        # Compare models
        comparison_stats = compare_models(
            self.y_tg_pred, self.y_er_pred,
            loaded_y_tg_pred, loaded_y_er_pred,
            self.y_tg_test, self.y_er_test,
            self.test_smiles1, self.test_smiles2,
            output_path
        )
        
        return comparison_stats
    
    def train_and_evaluate(self, compare_after_save=True):
        """
        Complete pipeline: load, extract, split, train, evaluate, and save
        
        Args:
            compare_after_save: If True, compare current models with loaded models after saving
        """
        self.load_data()
        self.extract_features()
        self.split_data()
        self.initialize_models()
        self.train_models()
        self.predict()
        self.evaluate_models()
        self.save_models()
        self.save_test_results_csv()
        
        # Compare with loaded models to verify save/load works correctly
        if compare_after_save:
            try:
                self.compare_with_loaded_models()
            except Exception as e:
                print(f"\nWarning: Could not compare with loaded models: {e}")
