import rdkit.Chem as Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import Draw
import os
import pandas as pd
import json


def load_data(data_path):
    """Load and parse polymer data from CSV"""
    try:
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} samples")
        print(f"Columns: {list(df.columns)}")
        
        num_drawn = 0
        smiles1_list = []
        smiles2_list = []
        ratio1_list = []
        ratio2_list = []
        tg_list = []
        er_list = []

        # Process each row
        for _, row in df.iterrows():
            sl = row['SL']
            
            smiles1, smiles2 = row['smiles1'], row['smiles2']
                # ratio1, ratio2 = row['Ratio_1'], row['Ratio_2']
                # er, tg = row['Er'], row['Tg']
                # smiles1_list.append(smiles1)
                # smiles2_list.append(smiles2)
                # ratio1_list.append(ratio1)
                # ratio2_list.append(ratio2)
                # tg_list.append(tg)
                # er_list.append(er)
               
                # Validate SMILES
            if is_valid_smiles(smiles1) and is_valid_smiles(smiles2):
                try:
                    draw_two_mols(smiles1, smiles2, sl)
                    num_drawn += 1
                except Exception as e:
                    print(f"Error drawing molecules: {str(e)}")
                    continue
            else:
                print(f"Skipping malformed SMILES pair: {smiles1}, {smiles2}, sl: {sl}")
                continue
        # data_dict = {
        #     'smiles1': smiles1_list,
        #     'smiles2': smiles2_list,
        #     'ratio1': ratio1_list,
        #     'ratio2': ratio2_list,
        #     'tg': tg_list,
        #     'er': er_list
        # }
        # pd.DataFrame(data_dict).to_csv(os.path.join(base_dir, "data", "unique_smiles_Er_two_mols.csv"), index=False)
        print(f"Saved {num_drawn} images to data/images")
        return num_drawn
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        raise

def load_smiles_data(data_path):
        try:
            # Read Excel file
            df = pd.read_csv(data_path)
    
            smiles1_list = []
            smiles2_list = []

            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract the two SMILES from the SMILES column
                    smiles_pair = eval(row['Smiles'])  # Safely evaluate string representation of list
                    if len(smiles_pair) == 2:
                        smiles1, smiles2 = smiles_pair[0], smiles_pair[1]
                        smiles1_list.append(smiles1)
                        smiles2_list.append(smiles2)
                except:
                    print(f"Skipping malformed SMILES pair: {row['SMILES']}")
                    continue
            return smiles1_list, smiles2_list
            
            
        except Exception as e:
            print(f"Error processing Excel file: {str(e)}")
            raise

def is_valid_smiles(smiles: str) -> bool:
    if not smiles or not isinstance(smiles, str):
        return False
    
    mol_obj = Chem.MolFromSmiles(smiles)
    return mol_obj is not None

def mol(s):
    if s is None or not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    m = Chem.MolFromSmiles(s)
    if m is None: 
        return None
    #Chem.SanitizeMol(m)
    return m

def canon(s):
    m = mol(s)  # Fixed: was _mol(s)
    return Chem.MolToSmiles(m, canonical=True) if m else None

def fp(m):  # ECFP4 bit vector
    return AllChem.GetMorganFingerprintAsBitVect(m, radius=2, nBits=2048)

def scaffold(m):
    core = MurckoScaffold.GetScaffoldForMol(m)
    #print(core, Chem.MolToSmiles(core, canonical=True),Chem.MolToSmiles(m))
    return Chem.MolToSmiles(core, canonical=True) if core else ""

def draw_two_mols(smiles1: str, smiles2: str, sl: str, image_format: str = "png") -> str:
    """
    Draw two molecules side-by-side and save as a single image.

    Args:
        smiles1: SMILES string for first molecule
        smiles2: SMILES string for second molecule
        sl: File name stem (from SL) without extension
        image_format: 'png' or 'jpg'/'jpeg'

    Returns:
        The path to the saved image file.
    """

    ext = image_format.lower()
    if ext == "jpg":
        ext = "jpeg"

    mol1 = Chem.MolFromSmiles(smiles1) if smiles1 else None
    mol2 = Chem.MolFromSmiles(smiles2) if smiles2 else None
    if mol1 is None or mol2 is None:
        raise ValueError("Invalid SMILES provided; cannot render molecules")

    AllChem.Compute2DCoords(mol1)
    AllChem.Compute2DCoords(mol2)

    img = Draw.MolsToGridImage(
        [mol1, mol2],
        molsPerRow=2,
        subImgSize=(1024, 1024),

    )

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    images_dir = os.path.join(project_root, "data", "images")
    os.makedirs(images_dir, exist_ok=True)

    # Sanitize filename
    safe_stem = str(sl)
    out_path = os.path.join(images_dir, f"{safe_stem}.{ext}")

    # PIL Image save
    img.save(out_path)
    return out_path


def add_history():
    """
    Add monomer pairs from CSV to duplicate_history.json in the format "SMILES1||SMILES2"
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    data_path = os.path.join(project_root, "RLHF_TSMP","data","scores_data", "unique_smiles_Er_two_mols_combined.csv")
    df = pd.read_csv(data_path)
    smiles1_list = df['Smiles 1'].tolist()
    smiles2_list = df['Smiles 2'].tolist()
    
    history_file = os.path.join(project_root, "RLHF_TSMP","src","Reward_component","unique_duplicate_reward", "duplicate_history.json")
    
    # Load existing history
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    order_invariant = history.get("order_invariant_pair", True)
    existing_pairs = set(history.get("pair_history", []))
    history_max = history.get("history_max", 100)
    
    print(f"Loaded existing history with {len(existing_pairs)} pairs")
    print(f"Order invariant: {order_invariant}, History max: {history_max}")
    
    # Process pairs and add to history
    new_pairs = []
    skipped_invalid = 0
    
    for smiles1, smiles2 in zip(smiles1_list, smiles2_list):
        # Canonicalize SMILES
        c1 = canon(smiles1)
        c2 = canon(smiles2)
        
        # Skip if invalid SMILES
        if c1 is None or c2 is None:
            skipped_invalid += 1
            continue
        
        # Create pair key (order invariant if enabled)
        if order_invariant:
            a, b = (c1, c2) if c1 <= c2 else (c2, c1)
            pair_key = f"{a}||{b}"
        else:
            pair_key = f"{c1}||{c2}"
        
        # Add if not already in history
        if pair_key not in existing_pairs:
            new_pairs.append(pair_key)
            existing_pairs.add(pair_key)
    
    # Update history - add all new pairs
    current_history = history.get("pair_history", [])
    updated_history = current_history + new_pairs
    
    # Update history_max to accommodate all pairs (or keep it larger)
    total_pairs = len(updated_history)
    if total_pairs > history_max:
        history["history_max"] = total_pairs  # Update to fit all pairs
    
    history["pair_history"] = updated_history
    
    # Save updated history
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
    
    print(f"\nAdded {len(new_pairs)} new pairs to history")
    print(f"Skipped {skipped_invalid} invalid SMILES pairs")
    print(f"Total pairs in history: {total_pairs}")
    print(f"Updated history_max to: {history['history_max']}")
    print(f"History saved to: {history_file}")

if __name__ == "__main__":
    # base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # .../RLHF_TSMP
    # data_path = os.path.join(base_dir, "data", "unique_smiles_Er_two_mols.csv")
    # print(f"Reading CSV from: {data_path}")
    # load_data(data_path)

    add_history()