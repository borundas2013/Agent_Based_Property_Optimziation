from StructureFineTuning_Agent.structurefinetune import remove_bond_by_smarts, add_group_by_smarts
from Predictor_Agent.TgEr.predict import predict_property
from Predictor_Agent.Solubility.solubility_prediction import predict_solubility
from Predictor_Agent.Toxicity.predict_toxicity import predict_toxicity_for_smiles_pair
from Generator_Agent.property_sample_generator import generate_samples
from Generator_Agent.structure_optimization import optimize_structure

def remove_bond_by_groups(smiles1: str, smiles2: str, bond_smarts: str, target_monomer: str = "1") -> str:
    return remove_bond_by_smarts(smiles1, smiles2, bond_smarts, target_monomer)

def add_group(smiles1: str, smiles2: str, group_smarts: str, target_monomer: str = "1", attachment_atom_idx: int = 0) -> str:
    return add_group_by_smarts(smiles1, smiles2, group_smarts, target_monomer, attachment_atom_idx)


    
def get_property_for_all(smiles1: str, smiles2: str, ratio_1: float, ratio_2: float) -> dict:
    scores = predict_property(smiles1, smiles2, ratio_1, ratio_2)
    solubility, solubility_logs = predict_solubility(smiles1, smiles2)

    Tg = scores["tg_score"] 
    Er = scores["er_score"]
    solubility = solubility['average_hydration_free_energy']
    solubility_esol = solubility_logs['average_logS']
    solubility_esol_solubility = solubility_logs['solubility']
    toxicity_result = predict_toxicity_for_smiles_pair(smiles1, smiles2)
    return Tg, Er, solubility, solubility_esol, solubility_esol_solubility, toxicity_result

def get_property_for_toxicity(smiles1: str, smiles2: str) -> dict:
    toxicity_result = predict_toxicity_for_smiles_pair(smiles1, smiles2)
    return toxicity_result

def get_property_for_physical(smiles1: str, smiles2: str, ratio_1: float, ratio_2: float) -> dict:
    scores = predict_property(smiles1, smiles2, ratio_1, ratio_2)
    Tg = scores["tg_score"] 
    Er = scores["er_score"]
    return Tg, Er

def get_property_for_solubility(smiles1: str, smiles2: str) -> dict:
    solubility, solubility_logs = predict_solubility(smiles1, smiles2)
    solubility_esol = solubility_logs['average_logS']
    solubility_esol_solubility = solubility_logs['solubility']
    return solubility['average_hydration_free_energy'], solubility_esol, solubility_esol_solubility


def get_all_properties(smiles1: str, smiles2: str, ratio_1: float, ratio_2: float, property_type: str) -> dict:

    if property_type.lower() == "all":
        Tg, Er, solubility, solubility_esol, solubility_esol_solubility, toxicity_result = get_property_for_all(smiles1, smiles2, ratio_1, ratio_2)
        response = f"""**Comprehensive Property Analysis**

**Thermal and Mechanical Properties:**
• **Glass Transition Temperature (Tg):** {Tg:.2f} °C  
  _Temperature where the polymer transitions from rigid to flexible state._
• **Recovery Stress (Er):** {Er:.2f} MPa  
  _Material's shape recovery capability under stress._

**Solubility Assessment:**
• **ESOL Solubility (logS):**
  - LogS Value: {solubility_esol:.2f} (log mol/L)
  - Classification: {solubility_esol_solubility}
  _Higher logS values indicate better water solubility._

• **Hydration Energy Model:**
  - Value: {solubility:.2f} kcal/mol
  _Complementary measure of water interaction tendency._

**Toxicity Profile:**  
{toxicity_result['table']}

**Safety Summary:**  
This monomer combination shows {toxicity_result['summary']['overall_assessment']} with {toxicity_result['summary']['high_risk_count']} high-risk endpoints out of 12."""

    elif property_type.lower() == "toxicity":
        toxicity_result = get_property_for_toxicity(smiles1, smiles2)
        response = f"""**Toxicity Assessment**

{toxicity_result['table']}

**Understanding the Results:**  
Each endpoint is classified based on toxicity probability:
- High Risk: ≥ 0.7 probability
- Moderate Risk: 0.5-0.7 probability
- Low Risk: < 0.5 probability

**Overall Assessment:** {toxicity_result['summary']['overall_assessment']}
Number of High-Risk Endpoints: {toxicity_result['summary']['high_risk_count']} out of 12"""    

    elif property_type.lower() == "physical":
        Tg, Er = get_property_for_physical(smiles1, smiles2, ratio_1, ratio_2)
        response = f"""**Physical Properties Assessment**

**Thermal Properties:**
• **Glass Transition Temperature (Tg):** {Tg:.2f} °C  
  _Key temperature where polymer changes from glass-like to rubber-like._

**Mechanical Properties:**
• **Recovery Stress (Er):** {Er:.2f} MPa  
  _Indicates shape memory and recovery potential._
"""

    elif property_type.lower() == "solubility":
        solubility, solubility_esol, solubility_esol_solubility = get_property_for_solubility(smiles1, smiles2)
        print("solubility_esol_solubility:", solubility_esol_solubility)
        print("solubility_esol:", solubility_esol)
        print("solubility:", solubility)
        response = f"""**Solubility Analysis**

**Primary Solubility Measure (ESOL Model):**
• **LogS Value:** {solubility_esol:.2f} log mol/L
• **Interpretation:** {solubility_esol_solubility}
  _LogS is the standard measure of water solubility:_
  - Values > 0: Very soluble
  - Values -1 to 0: Soluble
  - Values -2 to -1: Moderately soluble
  - Values -3 to -2: Slightly soluble
  - Values < -3: Poorly soluble

**Supporting Measure:**
• **Hydration Energy:** {solubility:.2f} kcal/mol
  _Provides additional insight into water interaction potential._"""
    
    return response

def generate_TSMP_samples(Tg:float, Er:float, Group1:str, Group2:str) -> dict:
    return generate_samples(Tg, Er, Group1, Group2)

def optimize_TSMP(target_Tg, target_Er, tolerance_Tg, tolerance_Er, monomer1, monomer2,max_iterations, property_type, ) -> dict:
    return optimize_structure(target_Tg, target_Er, tolerance_Tg, tolerance_Er, monomer1, monomer2,max_iterations, property_type)