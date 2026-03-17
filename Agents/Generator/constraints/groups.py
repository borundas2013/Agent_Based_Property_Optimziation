import rdkit.Chem as Chem
from typing import List, Tuple, Dict, Optional
import sys
import os



from constraints.Utils.Util import is_valid_smiles

class ChemicalGroupAnalyzer:
    """Analyzer for chemical groups and reaction consistency in polymer structures."""
    
    def __init__(self, threshold: int = 2):
        """
        Initialize the chemical group analyzer.
        
        Args:
            threshold: Minimum number of groups required for reaction consistency
        """
        self.threshold = threshold
        
        # Define SMARTS patterns for different functional groups
        self.group_patterns = {
            'epoxy': 'C1OC1',
            'imine': ['NC', 'Nc'],
            'vinyl': 'C=C',
            'thiol': 'CCS',
            'acrylate': 'C=C(C=O)',
            'hydroxyl': 'O',
            'carbonyl': 'C=O',
            'carboxyl': 'C(=O)O',
            'thioether': 'CS'
        }
    
    
    def has_epoxy_group(self, smiles: str) -> bool:
        """
        Check if SMILES contains epoxy groups.
        
        Args:
            smiles: SMILES string to analyze
            
        Returns:
            True if epoxy groups are present, False otherwise
        """
        if not is_valid_smiles(smiles):
            return False
            
        mol = Chem.MolFromSmiles(smiles)
        substructure = Chem.MolFromSmarts(self.group_patterns['epoxy'])
        return mol.HasSubstructMatch(substructure)

    def has_imine(self, smiles: str) -> bool:
        """
        Check if SMILES contains imine groups.
        
        Args:
            smiles: SMILES string to analyze
            
        Returns:
            True if imine groups are present, False otherwise
        """
        if not is_valid_smiles(smiles):
            return False
            
        mol = Chem.MolFromSmiles(smiles)
        imine_pattern_1 = Chem.MolFromSmarts(self.group_patterns['imine'][0])
        imine_pattern_2 = Chem.MolFromSmarts(self.group_patterns['imine'][1])
        
        return (mol.HasSubstructMatch(imine_pattern_1) or 
                mol.HasSubstructMatch(imine_pattern_2))

    def has_vinyl_group(self, smiles: str) -> bool:
        """
        Check if SMILES contains vinyl groups.
        
        Args:
            smiles: SMILES string to analyze
            
        Returns:
            True if vinyl groups are present, False otherwise
        """
        if not is_valid_smiles(smiles):
            return False
            
        mol = Chem.MolFromSmiles(smiles)
        vinyl_pattern = Chem.MolFromSmarts(self.group_patterns['vinyl'])
        return mol.HasSubstructMatch(vinyl_pattern)

    def has_thiol_group(self, smiles: str) -> bool:
        """
        Check if SMILES contains thiol groups.
        
        Args:
            smiles: SMILES string to analyze
            
        Returns:
            True if thiol groups are present, False otherwise
        """
        if not is_valid_smiles(smiles):
            return False
            
        mol = Chem.MolFromSmiles(smiles)
        thiol_substructure = Chem.MolFromSmarts(self.group_patterns['thiol'])
        return mol.HasSubstructMatch(thiol_substructure)

    def has_acrylate_group(self, smiles: str) -> bool:
        """
        Check if SMILES contains acrylate groups.
        
        Args:
            smiles: SMILES string to analyze
            
        Returns:
            True if acrylate groups are present, False otherwise
        """
        if not is_valid_smiles(smiles):
            return False
            
        mol = Chem.MolFromSmiles(smiles)
        acrylate_substructure = Chem.MolFromSmarts(self.group_patterns['acrylate'])
        return mol.HasSubstructMatch(acrylate_substructure)

    def has_hydroxyl_group(self, smiles: str) -> bool:
        """
        Check if SMILES contains hydroxyl groups.
        
        Args:
            smiles: SMILES string to analyze
            
        Returns:
            True if hydroxyl groups are present, False otherwise
        """
        if not is_valid_smiles(smiles):
            return False
            
        mol = Chem.MolFromSmiles(smiles)
        hydroxyl_substructure = Chem.MolFromSmarts(self.group_patterns['hydroxyl'])
        return mol.HasSubstructMatch(hydroxyl_substructure)

    def count_functional_groups(self, smiles: str, smarts_pattern: str) -> int:
        """
        Count occurrences of a functional group pattern in SMILES.
        
        Args:
            smiles: SMILES string to analyze
            smarts_pattern: SMARTS pattern to search for
            
        Returns:
            Number of matches found
        """
        if not is_valid_smiles(smiles):
            return 0
            
        mol = Chem.MolFromSmiles(smiles)
        return len(mol.GetSubstructMatches(Chem.MolFromSmarts(smarts_pattern)))

    def check_reaction_consistency(self, smiles1: str, smiles2: str) -> bool:
        """
        Check if two SMILES strings have consistent reactive groups for polymerization.
        
        Args:
            smiles1: First SMILES string
            smiles2: Second SMILES string
            
        Returns:
            True if reaction is consistent, False otherwise
        """
        # Validate both SMILES strings first
        if not is_valid_smiles(smiles1) or not is_valid_smiles(smiles2):
            return False,None,None
        reaction_pairs = [
            ('C=C', 'C=C'),  # vinyl-vinyl
            ('C1OC1', 'NC'),  # epoxy-imine
            ('NC', 'C1OC1'),  # imine-epoxy
            ('CCS', 'C=C'),  # thiol-vinyl
            ('C=C', 'CCS'),  # vinyl-thiol
            ('C=C', 'O'),   # vinyl-hydroxyl
            ('O', 'C=C'),   # hydroxyl-vinyl
            ('C=C(C=O)', 'C=C'),  # acrylate-vinyl
            ('C=C', 'C=C(C=O)'),  # vinyl-acrylate
            ('C=O', 'NC'),  # carbonyl-imine
            ('NC', 'C=O'),  # imine-carbonyl
            ('C(=O)O', 'C1OC1'),  # carboxyl-epoxy
            ('C1OC1', 'C(=O)O'),  # epoxy-carboxyl
            ('CS', 'C1OC1'),  # thioether-epoxy
            ('C1OC1', 'CS')   # epoxy-thioether
        ]
        
        for pattern1, pattern2 in reaction_pairs:
            count1 = self.count_functional_groups(smiles1, pattern1)
            count2 = self.count_functional_groups(smiles2, pattern2)
            
            if count1 >= self.threshold and count2 >= self.threshold:
                return True, pattern1, pattern2
                
        return False, None, None

    def check_group_consistency(self, group1: str, group2: str, 
                              smiles1: str, smiles2: str) -> bool:
        """
        Check if specified groups are present in the corresponding SMILES strings.
        
        Args:
            group1: Name of first group to check
            group2: Name of second group to check
            smiles1: First SMILES string
            smiles2: Second SMILES string
            
        Returns:
            True if both groups are present in their respective SMILES
        """
        # Validate both SMILES strings first
        if not is_valid_smiles(smiles1) or not is_valid_smiles(smiles2):
            return False, False
        group_detectors = {
            'C=C': self.has_vinyl_group,
            'C1OC1': self.has_epoxy_group,
            'O': self.has_hydroxyl_group,
            'CCS': self.has_thiol_group,
            'C=C(C=O)': self.has_acrylate_group,
            'NC': self.has_imine
        }
        
        # Check if group1 is present in smiles1
        group1_present = False
        if group1 in group_detectors:
            group1_present = group_detectors[group1](smiles1)
        
        # Check if group2 is present in smiles2
        group2_present = False
        if group2 in group_detectors:
            group2_present = group_detectors[group2](smiles2)
        
        return group1_present,  group2_present

    