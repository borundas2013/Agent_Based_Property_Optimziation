import pandas as pd
import numpy as np
import os
import sys
from rdkit import Chem, DataStructs
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from Generator.constraints.Utils.Util import is_valid_smiles, mol, scaffold, fp
import rdkit.Chem as Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit import DataStructs

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
data_path = os.path.join(project_root, "data", 'unique_smiles_Er.csv')

def load_data(data_path):
    """Load and parse polymer data from CSV"""
    try:
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} samples")
        print(f"Columns: {list(df.columns)}")
        
        smiles1_list = []
        smiles2_list = []
        tg_list = []
        er_list = []
        ratio1_list = []
        ratio2_list = []

        # Process each row
        for _, row in df.iterrows():
            try:
                # Extract the two SMILES from the SMILES column
                smiles_pair = eval(row['Smiles'])  # Safely evaluate string representation of list
                if len(smiles_pair) == 2:
                    smiles1, smiles2 = smiles_pair[0], smiles_pair[1]
                    
                    # Validate SMILES
                    if is_valid_smiles(smiles1) and is_valid_smiles(smiles2):
                        smiles1_list.append(smiles1)
                        smiles2_list.append(smiles2)
                        tg_list.append(row['Tg'])
                        er_list.append(row['Er'])
                        ratio1_list.append(row['Ratio_1'])
                        ratio2_list.append(row['Ratio_2'])
            except:
                continue
                
        print(f"Successfully parsed {len(smiles1_list)} valid polymer pairs")
        print("Maximum Tg: ", max(tg_list))
        print("Minimum Tg: ", min(tg_list))
        print("Maximum Er: ", max(er_list))
        print("Minimum Er: ", min(er_list))
       
        return smiles1_list, smiles2_list, tg_list, er_list, ratio1_list, ratio2_list
        
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        raise


def extract_molecular_features(smiles1_list, smiles2_list, ratio1_list=None, ratio2_list=None,
                             fp_bits=1024, use_symmetric=True):
    """
    Extract molecular features from SMILES pairs with optimized dimensionality
    
    Args:
        fp_bits: Number of fingerprint bits (1024 or 2048)
        use_symmetric: If True, use symmetric features (f1+f2, |f1-f2|) instead of raw f1,f2
    """
    print(f"Extracting molecular features (fp_bits={fp_bits}, symmetric={use_symmetric})...")
    
    features_list = []
    
    # Handle case where ratios are not provided
    if ratio1_list is None:
        ratio1_list = [0.5] * len(smiles1_list)
        ratio2_list = [0.5] * len(smiles2_list)
    
    for i, (smiles1, smiles2, ratio1, ratio2) in enumerate(zip(smiles1_list, smiles2_list, ratio1_list, ratio2_list)):
        if i % 100 == 0:
            print(f"Processing {i}/{len(smiles1_list)}")
            
        # Get molecular objects
        mol1 = mol(smiles1)
        mol2 = mol(smiles2)
        
        if mol1 is None or mol2 is None:
            continue
            
        # Extract features for both molecules
        features1 = extract_single_molecule_features(mol1, fp_bits)
        features2 = extract_single_molecule_features(mol2, fp_bits)
        
        # Create ratio features
        ratio_features = np.array([ratio1, ratio2])
        
        if use_symmetric:
            # Symmetric features: more efficient and often better for polymers
            combined_features = np.concatenate([
                features1 + features2,  # Sum features
                np.abs(features1 - features2),  # Absolute difference
                ratio_features,  # Ratio features
                features1 * ratio1 + features2 * ratio2  # Weighted combination
            ])
        else:
            # Raw features: f1, f2, differences
            combined_features = np.concatenate([
                features1,  # Features from molecule 1
                features2,  # Features from molecule 2
                ratio_features,  # Ratio features
                np.abs(features1 - features2),  # Difference features
                features1 * ratio1 + features2 * ratio2  # Weighted combination
            ])
        
        features_list.append(combined_features)
    
    return np.array(features_list)


def extract_single_molecule_features(mol_obj, fp_bits=1024):
    """Extract features from a single molecule with configurable fingerprint size"""
    features = []
    
    # Basic molecular descriptors (dense features)
    features.extend([
        Descriptors.MolWt(mol_obj),
        Descriptors.MolLogP(mol_obj),
        Descriptors.NumHDonors(mol_obj),
        Descriptors.NumHAcceptors(mol_obj),
        Descriptors.NumRotatableBonds(mol_obj),
        Descriptors.NumAromaticRings(mol_obj),
        Descriptors.NumSaturatedRings(mol_obj),
        Descriptors.TPSA(mol_obj),
        Descriptors.FractionCSP3(mol_obj),
        Descriptors.NumHeteroatoms(mol_obj),
        Descriptors.HeavyAtomCount(mol_obj),
        mol_obj.GetNumBonds()
    ])
    
    # Morgan fingerprint (ECFP4) - configurable bit size
    fp_bits_obj = AllChem.GetMorganFingerprintAsBitVect(mol_obj, radius=2, nBits=fp_bits)
    fp_array = np.array(fp_bits_obj)
    features.extend(fp_array)
    
    return np.array(features)


def create_groups(smiles1_list, smiles2_list):
    """Create groups for GroupShuffleSplit based on SMILES components"""
    groups = []
    
    for smiles1, smiles2 in zip(smiles1_list, smiles2_list):
        # Create group based on the combination of both SMILES
        # This ensures samples with same polymer pair stay together
        group_id = hash((smiles1, smiles2))
        groups.append(group_id)
    
    return groups

def create_train_test_split(X, y_tg, y_er, smiles1_list=None, smiles2_list=None, 
                          test_size=0.2, random_state=42, use_group_split=True):
    """Create train/test split using GroupShuffleSplit or regular split"""
    
    if use_group_split and smiles1_list is not None and smiles2_list is not None:
        print(f"Creating GroupShuffleSplit (test_size={test_size}, random_state={random_state})")
        
        # Create groups based on SMILES pairs
        groups = create_groups(smiles1_list, smiles2_list)
        
        # Use GroupShuffleSplit
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        train_idx, test_idx = next(gss.split(X, y_tg, groups))
        
        # Split the data
        X_train, X_test = X[train_idx], X[test_idx]
        y_tg_train, y_tg_test = y_tg[train_idx], y_tg[test_idx]
        y_er_train, y_er_test = y_er[train_idx], y_er[test_idx]
        
        print(f"GroupShuffleSplit: Ensures no polymer pairs appear in both train and test")
        
    else:
        print(f"Creating regular train/test split (test_size={test_size}, shuffle=True, random_state={random_state})")
        
        # Regular train/test split
        X_train, X_test, y_tg_train, y_tg_test, y_er_train, y_er_test = train_test_split(
            X, y_tg, y_er, test_size=test_size, random_state=random_state, shuffle=True
        )
        
        print(f"Regular split: Standard random shuffle")
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Feature dimensions: {X_train.shape[1]}")
    
    return X_train, X_test, y_tg_train, y_tg_test, y_er_train, y_er_test


def scale_features(X_train, X_test, model_type='linear'):
    """
    Scale features based on model type
    
    Args:
        model_type: 'linear' for linear/MLP models (needs scaling), 
                   'tree' for RF/GB/XGB models (no scaling needed)
    """
    if model_type == 'tree':
        print("Tree-based model: No scaling needed")
        return X_train, X_test, None
    else:
        print("Linear/MLP model: Scaling features with StandardScaler...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Save scaler for later use
        joblib.dump(scaler, 'RLHF_TSMP/src/Reward_component/property_alignment/feature_scaler.pkl')
        print("Scaler saved as 'feature_scaler.pkl'")
        
        return X_train_scaled, X_test_scaled, scaler


def load_scaler(scaler_path=None):
    """
    Load a saved StandardScaler from disk
    
    Args:
        scaler_path: Path to the saved scaler file. If None, uses default path
                    'RLHF_TSMP/src/Reward_component/property_alignment/feature_scaler.pkl'
    
    Returns:
        scaler: Loaded StandardScaler object
    
    Raises:
        FileNotFoundError: If the scaler file doesn't exist
        Exception: If there's an error loading the scaler
    """
    if scaler_path is None:
        # Use the same path as in scale_features
        scaler_path = 'RLHF_TSMP/src/Reward_component/property_alignment/feature_scaler.pkl'
    
    try:
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler file not found at: {scaler_path}")
        
        scaler = joblib.load(scaler_path)
        print(f"Scaler loaded successfully from '{scaler_path}'")
        return scaler
        
    except FileNotFoundError:
        print(f"Error: Scaler file not found at '{scaler_path}'")
        raise
    except Exception as e:
        print(f"Error loading scaler from '{scaler_path}': {str(e)}")
        raise


if __name__ == "__main__":
    smiles1_list, smiles2_list, tg_list, er_list, ratio1_list, ratio2_list = load_data(data_path)
    X = extract_molecular_features(smiles1_list, smiles2_list)
    y_tg = np.array(tg_list)
    y_er = np.array(er_list)
    X_train, X_test, y_tg_train, y_tg_test, y_er_train, y_er_test = create_train_test_split(X, y_tg, y_er, smiles1_list, smiles2_list, test_size=0.2, random_state=42,use_group_split=True)
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    print(X_train_scaled.shape, X_test_scaled.shape, scaler)

    #load_scaler('RLHF_TSMP/src/Reward_component/property_alignment/feature_scaler.pkl')
    










