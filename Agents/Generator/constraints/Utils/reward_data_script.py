import pandas as pd
import os
import json
import random
from dual_smile_process import *
from template import *

def load_dataset():
    """Load dataset from Data folder and return all columns"""
    data_path = os.path.join('RLHF_TSMP','data', 'unique_smiles_Er.csv')
    try:
        monomer1, monomer2, er, tg = process_dual_monomer_data(data_path)
        return monomer1, monomer2, er, tg
        
    except FileNotFoundError:
        print(f"Error: Could not find dataset at {data_path}")
        return None
    except Exception as e:
        print(f"Error loading dataset: {str(e)}")
        return None

def prepare_json_data(monomer1, monomer2, er=None, tg=None, group1=None, group2=None, prompt=None):
    """Prepare JSON data structure for a single sample.
    
    Args:
        monomer1: First monomer SMILES
        monomer2: Second monomer SMILES
        er: Recovery stress value (optional)
        tg: Glass transition temperature (optional)
        group1: First functional group (optional)
        group2: Second functional group (optional)
        prompt: User instruction prompt
    
    Returns:
        dict: JSON data structure with instruction, answer, prompt, and target
    """
    # Build target dictionary - check most specific case first
    target = {}
    
    if tg is not None and er is not None and group1 is not None and group2 is not None:
        # Mixed: both properties and groups
        target = {
            "tg": tg,
            "er": er,
            "group1": group1,
            "group2": group2,
        }
    elif tg is not None and er is not None:
        # Properties only
        target = {
            "tg": tg,
            "er": er,
        }
    elif group1 is not None and group2 is not None:
        # Groups only
        target = {
            "group1": group1,
            "group2": group2,
        }
    
    if prompt is None:
        raise ValueError("Prompt cannot be None")
    
    json_data = {
        # "instruction": prompt,
        # "answer": {
        #     "Monomer1": monomer1,
        #     "Monomer2": monomer2
        # },
        "prompt": [
            {
                "role": "system",
                "content": system_prompt_template
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        "target": target
    }
    return json_data
count=0
def prepare_user_prompt(monomer1, monomer2, er=None, tg=None):
    global count
    prompt_1 = None
    prompt_2 = None
    prompt_3 = None
    Tg = None
    Er = None
    make_json_data_prompt_1 = None
    make_json_data_prompt_2 = None
    make_json_data_prompt_3 = None
    
    
    try:
        properties_prompt = random.choice(property_prompt_template)
        group_prompt = random.choice(group_prompt_template)
        mix_prompt = random.choice(mix_prompt_template)
        reaction, groups = check_reaction_validity(monomer1, monomer2)

      
        if tg is not None and er is not None:
            Tg = int(tg)
            Er = int(er)
            prompt_1 = properties_prompt.format(Tg=Tg, Er=Er)
            make_json_data_prompt_1 = prepare_json_data(monomer1, monomer2, er=Er, tg=Tg, prompt=prompt_1)
            
        if not groups:
            count+=1
            group1, group2 = None, None
        else:
            group1, group2 = groups[0], groups[1]  
        
        if group1 and group2:
            prompt_2 = group_prompt.format(Group1=group1, Group2=group2)
            make_json_data_prompt_2 = prepare_json_data(monomer1, monomer2, group1=group1, group2=group2, prompt=prompt_2)
           
            if Tg is not None and Er is not None:
                prompt_3 = mix_prompt.format(Group1=group1, Group2=group2, Tg=Tg, Er=Er)
                make_json_data_prompt_3 = prepare_json_data(monomer1, monomer2, er=Er, tg=Tg, group1=group1, group2=group2, prompt=prompt_3)
                
        # else:
        #     print(f"No valid groups found for monomer1: {monomer1} and monomer2: {monomer2}")
    except Exception as e:
        print(f"Error preparing user prompt: {str(e)}")

    return make_json_data_prompt_1, make_json_data_prompt_2, make_json_data_prompt_3





if __name__ == "__main__":
    # Load dataset
    result = load_dataset()
    if result is None:
        print("Failed to load dataset. Exiting.")
        exit(1)
    
    monomer1s, monomer2s, ers, tgs = result
    
    if not all([monomer1s, monomer2s, ers, tgs]):
        print("Error: Dataset returned empty or incomplete data.")
        exit(1)
    
    if len(monomer1s) != len(monomer2s) or len(monomer1s) != len(ers) or len(monomer1s) != len(tgs):
        print(f"Error: Mismatched data lengths - monomer1s: {len(monomer1s)}, monomer2s: {len(monomer2s)}, "
              f"ers: {len(ers)}, tgs: {len(tgs)}")
        exit(1)
    
    # Collect all samples
    all_samples = []
    errors = 0
    
    print(f"Processing {len(monomer1s)} samples...")
    for i in range(len(monomer1s)):
        try:
            json_data_1, json_data_2, json_data_3 = prepare_user_prompt(
                monomer1s[i], monomer2s[i], ers[i], tgs[i]
            )
            
            # Add each valid JSON data as a separate sample
            if json_data_1 is not None:
                all_samples.append(json_data_1)
            if json_data_2 is not None:
                all_samples.append(json_data_2)
            if json_data_3 is not None:
                all_samples.append(json_data_3)
                
        except Exception as e:
            errors += 1
            print(f"Error processing sample {i}: {str(e)}")
            continue
    
    print(f"Successfully processed {len(all_samples)} samples ({errors} errors)")
    print(f"No valid groups found for {count} samples")
    # Save to single JSON file
    output_file = os.path.join('RLHF_TSMP', 'data', 'new_data', 'reward_training_data_withoout_instruction.jsonl')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_samples, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(all_samples)} samples to {output_file}")
    except Exception as e:
        print(f"Error saving JSON file: {str(e)}")
        exit(1)
    
    


 

   