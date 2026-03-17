from tools import remove_bond_by_groups, add_group, get_all_properties, generate_TSMP_samples, optimize_TSMP
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from dotenv import load_dotenv
import os

# Load environment variables with explicit path
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")

load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")
MODEL_ID = os.getenv("BASE_MODEL_ID")

# Add fallback values for debugging


print("MODEL_ID:", MODEL_ID)
print("api_key:", api_key[:20] + "..." if api_key else "None")


class RemoveBondBySmartsTool(BaseModel):
    smiles1: str = Field(..., description="First molecule (monomer 1)")
    smiles2: str = Field(..., description="Second molecule (monomer 2)")
    bond_smarts: str = Field(..., description="The group/bond pattern to remove (in SMARTS format)")
    target_monomer: str = Field(..., description="Which molecule to modify ('1' or '2')")

class AddGroupBySmartsTool(BaseModel):
    smiles1: str = Field(..., description="First molecule (monomer 1)")
    smiles2: str = Field(..., description="Second molecule (monomer 2)")
    group_smarts: str = Field(..., description="The group to add, defined in SMARTS (must contain [*] as attachment point)")
    target_monomer: str = Field("1", description="Which molecule to modify ('1' or '2')")
    attachment_atom_idx: int = Field(0, description="Atom index in target molecule where the group will attach (default = 0)")

class GetAllPropertiesTool(BaseModel):
    smiles1: str = Field(..., description="First molecule (monomer 1)")
    smiles2: str = Field(..., description="Second molecule (monomer 2)")
    ratio_1: float = Field(0.1, description="Ratio of monomer 1 in the final polymer (default = 0.5)")
    ratio_2: float = Field(0.9, description="Ratio of monomer 2 in the final polymer (default = 0.5)")
    property_type: str = Field("physical", description="Type of property to predict (default = 'physical') from the following options: all, physical, toxicity, solubility")

class GenerateTSMPSamplesTool(BaseModel):
    Tg: float = Field(..., description="Glass transition temperature (Tg) of the polymer")
    Er: float = Field(..., description="Recovery stress (Er) of the polymer")
    Group1: str = Field(..., description="First functional group (monomer 1)")
    Group2: str = Field(..., description="Second functional group (monomer 2)")
    query: str = Field(..., description="Query to generate TSMP samples")

class GeneratePolymerWithGivenSMILES(BaseModel):
    SMILES: str = Field(..., description="SMILES of the polymer")

class OptimizeTSMPTool(BaseModel):
    target_Tg: float = Field(..., description="Target glass transition temperature (Tg) in °C")
    target_Er: float = Field(..., description="Target recovery stress (Er) in MPa")
    monomer1: str = Field(..., description="First monomer SMILES")
    monomer2: str = Field(..., description="Second monomer SMILES")
    tolerance_Tg: float = Field(..., description="Tolerance for Tg prediction (±°C)")
    tolerance_Er: float = Field(..., description="Tolerance for Er prediction (±MPa)")
    # max_iterations: int = Field(..., description="Maximum number of optimization iterations")
    # property_type: str = Field(..., description="Type of property to predict")


@tool
def remove_bond_by_smarts_tool(input: RemoveBondBySmartsTool) -> str:
    """
    Remove a specific group or bond from one of two molecules.

    Parameters:
    - smiles1 (str): First molecule (monomer 1)
    - smiles2 (str): Second molecule (monomer 2) 
    - bond_smarts (str): The group/bond pattern to remove (in SMARTS format)
    - target_monomer (str): Which molecule to modify ("1" or "2")

    Returns:
    - str: Result showing both molecules in the format:
           "Here is the revised output: monomer1 = [modified/unchanged] and monomer2 = [modified/unchanged]"
    """
    smiles1 = input.smiles1
    smiles2 = input.smiles2
    bond_smarts = input.bond_smarts
    target_monomer = input.target_monomer
    return remove_bond_by_groups(smiles1, smiles2, bond_smarts, target_monomer)

@tool
def add_group_by_smarts_tool(input: AddGroupBySmartsTool) -> str:
    """
    Add a functional group or substructure defined by SMARTS to one of two molecules.

    Parameters:
    - smiles1 (str): First molecule (monomer 1)
    - smiles2 (str): Second molecule (monomer 2)
    - group_smarts (str): The group to add, defined in SMARTS (must contain [*] as attachment point)
    - target_monomer (str): Which molecule to modify ("1" or "2")
    - attachment_atom_idx (int): Atom index in target molecule where the group will attach (default = 0)

    Returns:
    - str: Result showing both molecules in the format:
           "Here is the revised output: monomer1 = [modified/unchanged] and monomer2 = [modified/unchanged]"
    """
    smiles1 = input.smiles1
    smiles2 = input.smiles2
    group_smarts = input.group_smarts
    target_monomer = input.target_monomer
    attachment_atom_idx = input.attachment_atom_idx 
    return add_group(smiles1, smiles2, group_smarts, target_monomer, attachment_atom_idx)

@tool
def get_all_properties_tool(input: GetAllPropertiesTool) -> str:
    """
    Get all properties of a given SMILES pair.

    Parameters:
    - smiles1 (str): First molecule (monomer 1)
    - smiles2 (str): Second molecule (monomer 2)
    - ratio_1 (float): Ratio of monomer 1 in the final polymer (default = 0.1)
    - ratio_2 (float): Ratio of monomer 2 in the final polymer (default = 0.9)
    - property_type (str): Type of property to predict (default = "physical")

    Returns:
    - dict: Result showing asked properties of the given SMILES pair
    """
    smiles1 = input.smiles1
    smiles2 = input.smiles2
    ratio_1 = input.ratio_1
    ratio_2 = input.ratio_2
    property_type = input.property_type
    print("------------Parameters--------------------")
    print(smiles1, smiles2, ratio_1, ratio_2, property_type)
    return get_all_properties(smiles1, smiles2, ratio_1, ratio_2, property_type)


@tool
def generate_TSMP_samples_tool(input: GenerateTSMPSamplesTool) -> str:
    """
    Generate TSMP samples for a given Tg, Er, Group1, Group2, and query.

    Parameters:
    - Tg (float): Glass transition temperature (Tg) of the polymer
    - Er (float): Recovery stress (Er) of the polymer
    - Group1 (str): First functional group (monomer 1)
    - Group2 (str): Second functional group (monomer 2)
    - query (str): Query to generate TSMP samples

    Returns:
    - str: Result showing generated TSMP samples
    """
    Tg = input.Tg
    Er = input.Er
    Group1 = input.Group1
    Group2 = input.Group2
    print("------------Parameters--------------------")
    print(Tg, Er, Group1, Group2)
    return generate_TSMP_samples(Tg, Er, Group1, Group2)


@tool
def generate_polymer_with_given_SMILES_tool(input: GeneratePolymerWithGivenSMILES) -> str:
    """
    Generate a polymer structure from a given SMILES string representation.

    This function takes a SMILES string as input and generates a polymer structure.
    The SMILES string should represent a valid chemical structure that can be 
    polymerized.

    Parameters:
    - input (GeneratePolymerWithGivenSMILES): Input object containing:
        - SMILES (str): SMILES string representation of the monomer/polymer structure.
                       Should be a valid SMILES string following standard notation.

    Returns:
    - str:  string containing:
           - The generated polymer structure in SMILES format
           - Contain two monomers in SMILES format in the generated polymer structure
           - First monomer is the the given monomer in SMILES format
           - Second monomer is the the generated monomer in SMILES format
           - Details about the polymerization process
           - Any warnings or errors encountered during generation
           - Validation results for the generated structure

    Raises:
    - ValueError: If the input SMILES string is invalid or cannot be processed
    - RuntimeError: If polymer generation fails
    """
    SMILES = input.SMILES
    print("------------Parameters--------------------")
    print(SMILES)
    #return generate_polymer_with_given_SMILES(SMILES)

@tool
def optimize_TSMP_tool(input: OptimizeTSMPTool) -> str:
    """
    Iteratively optimize TSMP samples until predicted properties fall within target tolerance.

    This tool generates TSMP samples and then iteratively modifies them until the predicted
    Tg and Er values fall within the specified tolerance range of the target values.

    Parameters:
    - target_Tg (float): Target glass transition temperature (Tg) in °C
    - target_Er (float): Target recovery stress (Er) in MPa
    - tolerance_Tg (float): Tolerance for Tg prediction (±°C)
    - tolerance_Er (float): Tolerance for Er prediction (±MPa)
    - monomer1 (str): First monomer SMILES
    - monomer2 (str): Second monomer SMILES
  

    Returns:
    - str: Optimization results showing the final optimized samples and their properties
    """
   
    
    target_Tg = input.target_Tg
    target_Er = input.target_Er
    tolerance_Tg = input.tolerance_Tg
    tolerance_Er = input.tolerance_Er
    monomer1 = input.monomer1
    monomer2 = input.monomer2
    print("------------Parameters--------------------")
    print(target_Tg, target_Er, tolerance_Tg, tolerance_Er, monomer1, monomer2)
    return optimize_TSMP(target_Tg, target_Er, tolerance_Tg, tolerance_Er, monomer1, monomer2,5, "physical")


    # max_iterations = input.max_iterations
    # property_type = input.property_type




def main():
    try:
        print("Initializing LLM...")
        llm = ChatOpenAI(model=MODEL_ID, api_key=api_key, 
                     temperature=0, max_tokens=1000)
        
        print("Creating agent...")
        agent = create_react_agent(llm,
                                   tools=[remove_bond_by_smarts_tool, 
                                   add_group_by_smarts_tool, 
                                   get_all_properties_tool, 
                                   generate_TSMP_samples_tool, 
                                   generate_polymer_with_given_SMILES_tool,
                                   optimize_TSMP_tool])
        
        print("Agent created successfully!")
        
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print(f"Error type: {type(e)}")
     
        return



    try:
        print("\n" + "="*50)
        print("EXECUTING QUERIES")
        print("="*50)
        
        #
        query="Please generate a TSMP"
        #query="First, Generate a TSMP with Tg = 100 °C, Er = 40 MPa with Group1 = epoxy(C1OC1) in monomer1, Group2 = imine(NC) in monomer2. Then, show me physical properties of the generated samples with ratio_1 = 0.5 and ratio_2 = 0.5."
        #query = "Generate TSMP samples for Tg = 100°C, Er = 40 MPa with epoxy(C1OC1) group in monomer1 and imine(NC) groups in monomer2, and immediately after generation, predict all properties of the generated samples."
        print("User query:", query)
        response = agent.invoke({"messages": [("human", query)]})
        print("Assistant response:", response["messages"][-1].content)
        
        query= response["messages"][-1].content + " Then, optimize the generated samples to achieve Tg = 100 °C, Er = 40 MPa with tolerance of ±5°C for Tg and ±5 MPa for Er."
        print("\nUser query:", query)
        response = agent.invoke({"messages": [("human", query)]})
        print("Assistant response:", response["messages"][-1].content)
        
    except Exception as e:
        print(f"Error during query execution: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    

    # Basic optimization
#query = "Optimize TSMP samples to achieve Tg = 100°C and Er = 40 MPa with Group1 = epoxy(C1OC1) and Group2 = imine(NC). Use tolerance of ±5°C for Tg and ±5 MPa for Er."

# Advanced optimization with custom parameters
#query = "Optimize TSMP with target Tg = 120°C, Er = 50 MPa, tolerance Tg = ±10°C, tolerance Er = ±8 MPa, max 5 iterations, using vinyl(C=C) and acrylate(C=C(C=O)) groups."


if __name__ == "__main__":
   main()
