import pandas as pd
import numpy as np
from rdkit import Chem
import Constants
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from transformers import PreTrainedTokenizerFast

import os

    
def hasEpoxyGroup(smile):
    mol = Chem.MolFromSmiles(smile)
    substructure = Chem.MolFromSmarts('C1OC1')
    matches = []
    if mol is not None and mol.HasSubstructMatch(substructure):
        matches = mol.GetSubstructMatches(substructure)
    else:
        return None
    return  'C1OC1'

def has_imine(smiles):
    imine_pattern_1 = Chem.MolFromSmarts('NC')
    imine_pattern_2 = Chem.MolFromSmarts('Nc')
    capital_C = False
    mol = Chem.MolFromSmiles(smiles)
    matches = []
    if mol is not None and mol.HasSubstructMatch(imine_pattern_1):
        matches = mol.GetSubstructMatches(imine_pattern_1)
        capital_C = True
    elif mol is not None and mol.HasSubstructMatch(imine_pattern_2):
        matches = mol.GetSubstructMatches(imine_pattern_2)
        capital_C = False
    else:
        return None
    return 'NC' if capital_C else 'Nc'


def has_vinyl_group(smiles):
    vinyl_pattern = Chem.MolFromSmarts('C=C')
    mol = Chem.MolFromSmiles(smiles)

    if mol is not None  and mol.HasSubstructMatch(vinyl_pattern):
        matches = mol.GetSubstructMatches(vinyl_pattern)
        return 'C=C'
    else:
        return None


def has_thiol_group(smiles):
    thiol_substructure = Chem.MolFromSmarts('CCS')
    mol = Chem.MolFromSmiles(smiles)
    if mol is not None  and mol.HasSubstructMatch(thiol_substructure):
        thiol_substructure = Chem.MolFromSmiles('CCS')
        matches = mol.GetSubstructMatches(thiol_substructure)
        return 'CCS'
    else:
        return None


def has_acrylate_group(smiles):
    mol = Chem.MolFromSmiles(smiles)
    acrylate_substructure = Chem.MolFromSmarts('C=C(C=O)')

    if mol is not None  and mol.HasSubstructMatch(acrylate_substructure):
        acrylate_substructure = Chem.MolFromSmiles('C=C(C=O)')
        matches = mol.GetSubstructMatches(acrylate_substructure)
        return 'C=C(C=O)'
    else:
        return None
    
def has_benzene_ring(smiles):
    # Aromatic notation pattern
    aromatic_pattern = Chem.MolFromSmarts('c1ccccc1')
    # Kekulé notation pattern
    kekule_pattern = Chem.MolFromSmarts('C1=CC=CC=C1')
    
    mol = Chem.MolFromSmiles(smiles)
    
    if mol is not None:
        if mol.HasSubstructMatch(aromatic_pattern):
            return 'c1ccccc1'  # Aromatic notation
        elif mol.HasSubstructMatch(kekule_pattern):
            return 'C1=CC=CC=C1'  # Kekulé notation
    return None

