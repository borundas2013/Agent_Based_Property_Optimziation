import sys
sys.path.insert(0,'/ddnB/work/borun22/env/borun_torch/')
model_path = "/ddnB/work/borun22/Transfer_learning/NewCOT/LLM/DeepSeek/deepseek_qlora_finetuned/"
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain_core.tools import tool
from langchain.agents import initialize_agent, Tool, AgentType
from pydantic import BaseModel, Field
from tools import remove_bond_by_smarts, add_group_by_smarts
from langchain.tools import StructuredTool



# === Load LLM ===
def load_unsloth_llm(model_path: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype="auto", device_map="auto"
    )
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,
                    max_new_tokens=512, do_sample=False)
    return HuggingFacePipeline(pipeline=pipe)

# === Tool schemas ===
class RemoveBondBySmartsTool(BaseModel):
    smiles1: str = Field(..., description="First molecule (monomer 1)")
    smiles2: str = Field(..., description="Second molecule (monomer 2)")
    bond_smarts: str = Field(..., description="The group/bond pattern to remove (SMARTS format)")
    target_monomer: str = Field(..., description="Which molecule to modify ('1' or '2')")

class AddGroupBySmartsTool(BaseModel):
    smiles1: str = Field(..., description="First molecule (monomer 1)")
    smiles2: str = Field(..., description="Second molecule (monomer 2)")
    group_smarts: str = Field(..., description="Group to add (SMARTS with [*])")
    target_monomer: str = Field("1", description="Monomer to modify ('1' or '2')")
    attachment_atom_idx: int = Field(0, description="Atom index for attachment (default 0)")

def remove_bond_by_smarts_tool(smiles1: str, smiles2: str, bond_smarts: str, target_monomer: str) -> str:
    """Remove a specific bond or group from one of two monomers using SMARTS pattern.
    
    Args:
        smiles1 (str): First molecule (monomer 1)
        smiles2 (str): Second molecule (monomer 2) 
        bond_smarts (str): The bond/group pattern to remove in SMARTS format
        target_monomer (str): Which monomer to modify ('1' or '2')
    
    Returns:
        str: Result showing both molecules after modification
    """
    return remove_bond_by_smarts(smiles1, smiles2, bond_smarts, target_monomer)

def add_group_by_smarts_tool(smiles1: str, smiles2: str, group_smarts: str, target_monomer: str, attachment_atom_idx: int = 0) -> str:
    """Add a functional group to one of two monomers using SMARTS pattern.
    
    Args:
        smiles1 (str): First molecule (monomer 1)
        smiles2 (str): Second molecule (monomer 2)
        group_smarts (str): The group to add in SMARTS format (must contain [*])
        target_monomer (str): Which monomer to modify ('1' or '2')
        attachment_atom_idx (int, optional): Atom index for attachment. Defaults to 0.
    
    Returns:
        str: Result showing both molecules after modification
    """
    return add_group_by_smarts(smiles1, smiles2, group_smarts, target_monomer, attachment_atom_idx)

tool_registry = {
    "remove_bond_by_smarts_tool": StructuredTool(
        name="remove_bond_by_smarts_tool",
        description="Remove a SMARTS-defined bond/group from one of the monomers.",
        func=remove_bond_by_smarts_tool,
        args_schema=RemoveBondBySmartsTool
    ),
    "add_group_by_smarts_tool": StructuredTool(
        name="add_group_by_smarts_tool",
        description="Add a SMARTS-defined group to one of the two monomers.",
        func=add_group_by_smarts_tool,
        args_schema=AddGroupBySmartsTool
    )
}

# === Agent setup ===
def get_agent(model_path: str):
    llm = load_unsloth_llm(model_path)
    
    system_message = """You are a tool-based molecule modifier. Your ONLY task is to use the provided tools to modify the given monomers.

    CRITICAL RULES:
    1. You MUST use the tools to modify molecules
    2. You MUST NOT use any other knowledge or generate new molecules
    3. You MUST follow the exact format shown in the examples
    4. You MUST NOT try to create TSMPs or other polymers
    5. You MUST work only with the provided monomers
    6. You MUST NOT suggest or use any functional groups not in the request
    7. You MUST NOT think about or suggest alternative molecules
    8. You MUST take action immediately without excessive thinking

    Available Tools:
    1. remove_bond_by_smarts_tool: Remove a specific bond from a monomer
    2. add_group_by_smarts_tool: Add a functional group to a monomer

    Example format for removing O-O bonds:
    Action: remove_bond_by_smarts_tool
    Action Input: {"smiles1": "CCNC1OC1Cc1ccccc1CCCCBr", "smiles2": "CCC2OC2COOCC", "bond_smarts": "O-O", "target_monomer": "2"}

    Example format for adding a benzene ring:
    Action: add_group_by_smarts_tool
    Action Input: {"smiles1": "CCNC1OC1Cc1ccccc1CCCCBr", "smiles2": "CCC2OC2COOCC", "group_smarts": "[*]c1ccccc1", "target_monomer": "2"}

    Remember: You are a tool-based modifier. Use the tools. Do not try to be creative or use other knowledge."""

    agent = initialize_agent(
        tools=list(tool_registry.values()),
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        system_message=system_message,
        max_iterations=3,
        early_stopping_method="generate"
    )
    return agent, llm

# === Main testing loop ===
def main():
    agent, model = get_agent(model_path)

    test_queries = [
        "Here are two monomers: monomer1 = CCNC1OC1Cc1ccccc1CCCCBr and monomer2 = CCC2OC2COOCC. remove O-O bonds from monomer 2.",
        "Here are two monomers: monomer1 = O=C(OCC1CO1)C3CC2OC3CC2C(=O)OCC4CO4 and monomer2 = CCC2OC2COOCC. add [*]C(=O)O group to monomer 2."
    ]

    llm_output = [{
        "Action": "remove_bond_by_smarts_tool",
        "Action Input": {
            "smiles1": "CCNC1OC1Cc1ccccc1CCCCBr",
            "smiles2": "CCC2OC2COOCC",
            "bond_smarts": "O-O",
            "target_monomer": "2"
        }
    },
    {
        "Action": "add_group_by_smarts_tool",
        "Action Input": {
            "smiles1": "O=C(OCC1CO1)C3CC2OC3CC2C(=O)OCC4CO4",
            "smiles2": "CCC2OC2COOCC",
            "group_smarts": "[*]C(=O)O",
            "target_monomer": "2",
            "attachment_atom_idx": 0
        }
    }]

    for i, query in enumerate(test_queries):
        print(f"\nExample {i+1}:")
        print("User query:", query)
        try:
            # Get response from agent
            #response = agent.invoke({"input": query})
            response = llm_output[i]
            
            # Extract tool name and input directly from response
            if isinstance(response, dict):
                tool_name = response.get("Action")
                tool_input = response.get("Action Input")
                
                if tool_name and tool_input and tool_name in tool_registry:
                    result = tool_registry[tool_name].invoke(tool_input)
                    print("Assistant/Tool result:", result)
                    
                else:
                    print("Invalid tool name or input:", tool_name)
            else:
                print("Unexpected response format from agent")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()


import json

test_queries = [
    "Here are two monomers: monomer1 = CCNC1OC1Cc1ccccc1CCCCBr and monomer2 = CCC2OC2COOCC. remove O-O bonds from monomer 2.",
    "Here are two monomers: monomer1 = O=C(OCC1CO1)C3CC2OC3CC2C(=O)OCC4CO4 and monomer2 = CCC2OC2COOCC. add [*]C(=O)O group to monomer 2."
]

llm_output = [
    {
        "Action": "remove_bond_by_smarts_tool",
        "Action Input": {
            "smiles1": "CCNC1OC1Cc1ccccc1CCCCBr",
            "smiles2": "CCC2OC2COOCC",
            "bond_smarts": "O-O",
            "target_monomer": "2"
        }
    },
    {
        "Action": "add_group_by_smarts_tool",
        "Action Input": {
            "smiles1": "O=C(OCC1CO1)C3CC2OC3CC2C(=O)OCC4CO4",
            "smiles2": "CCC2OC2COOCC",
            "group_smarts": "[*]C(=O)O",
            "target_monomer": "2",
            "attachment_atom_idx": 0
        }
    }
]

data = []
for query, action in zip(test_queries, llm_output):
    action_block = f"Thought: I need to use the tool.\nAction: {action['Action']}\nAction Input: {json.dumps(action['Action Input'])}"
    data.append({
        "input": query,
        "output": action_block
    })

with open("tool_call_dataset.jsonl", "w") as f:
    for sample in data:
        f.write(json.dumps(sample) + "\n")
