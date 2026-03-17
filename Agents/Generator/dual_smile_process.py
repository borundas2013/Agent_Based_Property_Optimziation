import Constants
import pandas as pd
import numpy as np
import tensorflow as tf
from rdkit import Chem
from Data_Process_with_prevocab import *
import random

def process_dual_monomer_data(excel_path):

    try:
        # Read Excel file
        df = pd.read_csv(excel_path)
        df = df.sample(frac=1).reset_index(drop=True)
        

        # Initialize lists for storing data
        smiles1_list = []
        smiles2_list = []
        er_list = []
        tg_list = []
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Extract the two SMILES from the SMILES column
                smiles_pair = eval(row['Smiles'])  # Safely evaluate string representation of list
                if len(smiles_pair) == 2:
                    smiles1, smiles2 = smiles_pair[0], smiles_pair[1]
                    smiles1_list.append(smiles1)
                    smiles2_list.append(smiles2)
                    er_list.append(row['Er'])
                    tg_list.append(row['Tg'])
            except:
                print(f"Skipping malformed SMILES pair: {row['SMILES']}")
                continue
                

        return smiles1_list, smiles2_list, er_list, tg_list
        
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")
        raise
def count_functional_groups(smiles, smarts_pattern):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0
    return len(mol.GetSubstructMatches(Chem.MolFromSmarts(smarts_pattern)))



def reaction_valid_samples(smiles1,smiles2,er_list,tg_list):
 
    valid_reaction = []
    invalid_reaction = []
    for i in range(len(smiles1)):
        reaction_valid = filter_valid_groups(smiles1[i], smiles2[i])
        if reaction_valid:
            valid_reaction.append([smiles1[i],smiles2[i],er_list[i],tg_list[i]])
        else:
            invalid_reaction.append([smiles1[i],smiles2[i],er_list[i],tg_list[i]])

    print(len(valid_reaction))
    print(len(invalid_reaction))
    random_invalid_reaction = random.sample(invalid_reaction, 259)
    valid_reaction.extend(random_invalid_reaction) 
    print(len(valid_reaction))
    return valid_reaction

def check_reaction_validity_with_invalid_groups(smiles1, smiles2):
    mol1 = Chem.MolFromSmiles(smiles1)
    mol2 = Chem.MolFromSmiles(smiles2)
    pairs = [
        (Constants.VINYL_SMARTS, Constants.THIOL_SMARTS, ['C=C', 'CCS']),
        (Constants.THIOL_SMARTS, Constants.VINYL_SMARTS, ['CCS', 'C=C']),
        (Constants.VINYL_SMARTS, Constants.ACRYL_SMARTS, ['C=C', 'C=C(C=O)']),
        (Constants.ACRYL_SMARTS, Constants.VINYL_SMARTS, ['C=C(C=O)', 'C=C']),
        (Constants.EPOXY_SMARTS, Constants.IMINE_SMARTS, ['C1OC1', 'NC']),
        (Constants.IMINE_SMARTS, Constants.EPOXY_SMARTS, ['NC', 'C1OC1']),
        (Constants.VINYL_SMARTS, Constants.VINYL_SMARTS, ['C=C', 'C=C']),
        
    ]
    labels = ["No_group","No_group"]
    total_count = 0
    found = False
    for smarts1, smarts2, labels in pairs:
        count1 = count_functional_groups(smiles1, smarts1)
        count2 = count_functional_groups(smiles2, smarts2)
        total = count1 + count2
        if count1 >= 2 and count2 >= 2:
            labels[0] = smarts1
            labels[1] = smarts2
            total_count = total
            found = True
            break
        elif count1 > 0 and count2 > 0:
            labels[0] = smarts1
            labels[1] = smarts2
            total_count = total
            found = True
            break
        elif count1 > 0 and count2 == 0:
            labels[0] = smarts1
            labels[1] = "No_group"
            total_count = count1
            found = True
            break
        elif count1 == 0 and count2 > 0:
            labels[0] = "No_group"
            labels[1] = smarts2
            total_count = count2
            found = True
            break
        else:
            labels[0] = "No_group"
            labels[1] = "No_group"
            total_count = 0
            found = False
        
        
    
    if found:
        return labels, total_count
    else:
        return ["No_group", "No_group"], 0
    
def filter_valid_groups(smiles1, smiles2):
    pairs = [
        (Constants.VINYL_SMARTS, Constants.THIOL_SMARTS, ['C=C', 'CCS']),
        (Constants.THIOL_SMARTS, Constants.VINYL_SMARTS, ['CCS', 'C=C']),
        (Constants.VINYL_SMARTS, Constants.ACRYL_SMARTS, ['C=C', 'C=C(C=O)']),
        (Constants.ACRYL_SMARTS, Constants.VINYL_SMARTS, ['C=C(C=O)', 'C=C']),
        (Constants.EPOXY_SMARTS, Constants.IMINE_SMARTS, ['C1OC1', 'NC']),
        (Constants.IMINE_SMARTS, Constants.EPOXY_SMARTS, ['NC', 'C1OC1']),
        (Constants.VINYL_SMARTS, Constants.VINYL_SMARTS, ['C=C', 'C=C']),
        
    ]
    for smarts1, smarts2, labels in pairs:
        count1 = count_functional_groups(smiles1, smarts1)
        count2 = count_functional_groups(smiles2, smarts2)
        if count1 >= 2 and count2 >= 2:
            return True
       
        else:
            return False



def check_reaction_validity(smiles1, smiles2):
    mol1 = Chem.MolFromSmiles(smiles1)
    mol2 = Chem.MolFromSmiles(smiles2)
    if mol1 is None or mol2 is None:
        return False,[]
    if count_functional_groups(smiles1, Constants.EPOXY_SMARTS) >= 2 and count_functional_groups(smiles2, Constants.IMINE_SMARTS) >= 2:
        return True,['C1OC1','NC']
    if count_functional_groups(smiles1, Constants.IMINE_SMARTS) >= 2 and count_functional_groups(smiles2, Constants.EPOXY_SMARTS) >= 2:
        return True,['NC','C1OC1']
    if count_functional_groups(smiles1, Constants.VINYL_SMARTS) >= 2 and count_functional_groups(smiles2, Constants.THIOL_SMARTS) >= 2:
        return True,['C=C','CCS']
    if count_functional_groups(smiles1, Constants.THIOL_SMARTS) >= 2 and count_functional_groups(smiles2, Constants.VINYL_SMARTS) >= 2:
        return True,['CCS','C=C']
    if count_functional_groups(smiles1, Constants.VINYL_SMARTS) >= 2 and count_functional_groups(smiles2, Constants.ACRYL_SMARTS) >= 2:
        return True,['C=C','C=C(C=O)']
    if count_functional_groups(smiles1, Constants.ACRYL_SMARTS) >= 2 and count_functional_groups(smiles2, Constants.VINYL_SMARTS) >= 2:
        return True,['C=C(C=O)','C=C']  
    
    return False,[]


