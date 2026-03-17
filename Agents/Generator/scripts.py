import pandas as pd
import os
from dual_smile_process import *
from template import *
import json

def load_dataset():
    """Load dataset from Data folder and return all columns"""
    data_path = os.path.join('Agents','Generator', 'unique_smiles_Er.csv')
    try:
        monomer1, monomer2, er, tg = process_dual_monomer_data(data_path)
        return monomer1, monomer2, er, tg
        
    except FileNotFoundError:
        print(f"Error: Could not find dataset at {data_path}")
        return None
    except Exception as e:
        print(f"Error loading dataset: {str(e)}")
        return None
    
def prepare_user_prompt(monomer1, monomer2, er=None, tg=None,group1=None,group2=None):
    prompt_1 = None
    prompt_2 = None
    prompt_3 = None
    Tg = None
    Er = None
    try:
        properties_prompt = random.choice(property_prompt_template)
        group_prompt = random.choice(group_prompt_template)
        mix_prompt = random.choice(mix_prompt_template)
        if tg is not None and er is not None:
            Tg = int(tg)
            Er = int(er)
            prompt_1 = properties_prompt.format(Tg=Tg, Er=Er)
        
        if group1 and group2:
            prompt_2 = group_prompt.format(Group1=group1, Group2=group2)
            if Tg is not None and Er is not None:
                prompt_3 = mix_prompt.format(Group1=group1, Group2=group2, Tg=Tg, Er=Er)
        
        # else:
        #     print(f"No valid groups found for monomer1: {monomer1} and monomer2: {monomer2}")
    except Exception as e:
        print(f"Error preparing user prompt: {str(e)}")

    return prompt_1, prompt_2, prompt_3


    
def prepare_multi_turn_prompt(monomer1, monomer2, er, tg):
   
    user_prompt_list_property = []
    assistant_prompt_list_property = []
    system_prompt_list_property = []
    user_prompt_list_group = []
    assistant_prompt_list_group = []
    system_prompt_list_group = []
    user_prompt_list_mix = []
    assistant_prompt_list_mix = []
    system_prompt_list_mix = []
    no_valid_prompt = 0
    for i in range(len(monomer1)):
        try:
            user_prompt_property = []
            assistant_prompt_property = []
            system_prompt_property = []
            user_prompt_group = []
            assistant_prompt_group = []
            system_prompt_group = []
            user_prompt_mix = []
            assistant_prompt_mix = []
            system_prompt_mix = []
            reaction, groups = check_reaction_validity(monomer1[i], monomer2[i])

            
            monomer_1 = monomer1[i]
            monomer_2 = monomer2[i]
            Tg = tg[i]
            Er = er[i]
            
            if Tg is not None and Er is not None:
                Tg = int(Tg)
                Er = int(Er)
            if not groups:
                group1, group2 = None, None
            else:
                group1, group2 = groups[0], groups[1]
            
            prompt_1, prompt_2, prompt_3 = prepare_user_prompt(monomer_1, monomer_2, Er, Tg, group1, group2)
            if prompt_1:
                system_prompt_property.append(system_prompt_template)
                user_prompt_property.append(random.choice(conversational_tsmp_templates))
                assistant_prompt_property.append(random.choice(preference_prompt_templates))
                user_prompt_property.append(random.choice(property_preference_responses))
                assistant_prompt_property.append(random.choice(property_specification_templates))
                user_prompt_property.append(prompt_1)
                assistant_prompt = random.choice(output_format_template)
                prompt= assistant_prompt.format(SMILES_1=monomer_1, SMILES_2=monomer_2)
                assistant_prompt_property.append(prompt)
            
            if prompt_2:
                system_prompt_group.append(system_prompt_template)
                
               
                user_prompt_group.append(random.choice(conversational_tsmp_templates))
                assistant_prompt_group.append(random.choice(preference_prompt_templates))
                user_prompt_group.append(random.choice(group_preference_responses))
                assistant_prompt_group.append(random.choice(group_selection_templates))
                user_prompt_group.append(prompt_2)
                assistant_prompt = random.choice(output_format_template)
                prompt= assistant_prompt.format(SMILES_1=monomer_1, SMILES_2=monomer_2)
                assistant_prompt_group.append(prompt)
            if prompt_3:
                system_prompt_mix.append(system_prompt_template)
                user_prompt_mix.append(random.choice(conversational_tsmp_templates))
                assistant_prompt_mix.append(random.choice(preference_prompt_templates))
                user_prompt_mix.append(random.choice(both_preference_responses))
                assistant_prompt_mix.append(random.choice(both_options_explanation_templates))
                user_prompt_mix.append(prompt_3)
                assistant_prompt = random.choice(output_format_template)
                prompt= assistant_prompt.format(SMILES_1=monomer_1, SMILES_2=monomer_2)
                assistant_prompt_mix.append(prompt)
                
        except Exception as e:
            print(f"Error preparing prompt: {str(e)}")
        
        if prompt_2:
            system_prompt_list_group.append(system_prompt_group)
            user_prompt_list_group.append(user_prompt_group)
            assistant_prompt_list_group.append(assistant_prompt_group)
        if prompt_3:
            system_prompt_list_mix.append(system_prompt_mix)
            user_prompt_list_mix.append(user_prompt_mix)
            assistant_prompt_list_mix.append(assistant_prompt_mix)
        if prompt_1:
            system_prompt_list_property.append(system_prompt_property)
            user_prompt_list_property.append(user_prompt_property)
            assistant_prompt_list_property.append(assistant_prompt_property)
       

    return  user_prompt_list_property, assistant_prompt_list_property,system_prompt_list_property,user_prompt_list_group, assistant_prompt_list_group,system_prompt_list_group,user_prompt_list_mix, assistant_prompt_list_mix,system_prompt_list_mix

def prepare_single_turn_prompt(monomer1, monomer2, er, tg):
   
    user_prompt_list_property = []
    assistant_prompt_list_property = []
    system_prompt_list_property = []
    user_prompt_list_group = []
    assistant_prompt_list_group = []
    system_prompt_list_group = []
    user_prompt_list_mix = []
    assistant_prompt_list_mix = []
    system_prompt_list_mix = []
    no_valid_prompt = 0
    for i in range(len(monomer1)):
        try:
            user_prompt_property = []
            assistant_prompt_property = []
            system_prompt_property = []
            user_prompt_group = []
            assistant_prompt_group = []
            system_prompt_group = []
            user_prompt_mix = []
            assistant_prompt_mix = []
            system_prompt_mix = []
            reaction, groups = check_reaction_validity(monomer1[i], monomer2[i])

            
            monomer_1 = monomer1[i]
            monomer_2 = monomer2[i]
            Tg = tg[i]
            Er = er[i]
            
            if Tg is not None and Er is not None:
                Tg = int(Tg)
                Er = int(Er)
            if not groups:
                group1, group2 = None, None
            else:
                group1, group2 = groups[0], groups[1]
            
            prompt_1, prompt_2, prompt_3 = prepare_user_prompt(monomer_1, monomer_2, Er, Tg, group1, group2)
            if prompt_1:
                system_prompt_property.append(system_prompt_template)

                user_prompt_property.append(prompt_1)
                assistant_prompt = random.choice(output_format_template)
                prompt= assistant_prompt.format(SMILES_1=monomer_1, SMILES_2=monomer_2)
                assistant_prompt_property.append(prompt)
            
            if prompt_2:
                system_prompt_group.append(system_prompt_template)
                
                user_prompt_group.append(prompt_2)
                assistant_prompt = random.choice(output_format_template)
                prompt= assistant_prompt.format(SMILES_1=monomer_1, SMILES_2=monomer_2)
                assistant_prompt_group.append(prompt)
            if prompt_3:
                system_prompt_mix.append(system_prompt_template)
                user_prompt_mix.append(prompt_3)
                assistant_prompt = random.choice(output_format_template)
                prompt= assistant_prompt.format(SMILES_1=monomer_1, SMILES_2=monomer_2)
                assistant_prompt_mix.append(prompt)
                
        except Exception as e:
            print(f"Error preparing prompt: {str(e)}")
        
        if prompt_2:
            system_prompt_list_group.append(system_prompt_group)
            user_prompt_list_group.append(user_prompt_group)
            assistant_prompt_list_group.append(assistant_prompt_group)
        if prompt_3:
            system_prompt_list_mix.append(system_prompt_mix)
            user_prompt_list_mix.append(user_prompt_mix)
            assistant_prompt_list_mix.append(assistant_prompt_mix)
        if prompt_1:
            system_prompt_list_property.append(system_prompt_property)
            user_prompt_list_property.append(user_prompt_property)
            assistant_prompt_list_property.append(assistant_prompt_property)
       

    return  user_prompt_list_property, assistant_prompt_list_property,system_prompt_list_property,user_prompt_list_group, assistant_prompt_list_group,system_prompt_list_group,user_prompt_list_mix, assistant_prompt_list_mix,system_prompt_list_mix

def save_conversation_to_json(conversations, output_file=""):
    if not output_file.endswith('.jsonl'):
        output_file = output_file.rsplit('.', 1)[0] + '.jsonl'
    
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(conversations,ensure_ascii=False)+"\n")
        print(f"Successfully saved conversation to {output_file}")
    except Exception as e:
        print(f"Error saving conversation to {output_file}: {str(e)}")

def save_polymer_conversation(user_prompt_list, assistant_prompt_list, system_prompts,output_file_train,output_file_valid):
    
    if not (len(user_prompt_list) == len(assistant_prompt_list) == len(system_prompts)):
        raise ValueError("Input lists must have equal length")
        
    output_file_train = os.path.join("Agents","Generator","data", output_file_train)
    output_file_valid = os.path.join("Agents","Generator","data", output_file_valid)


    split_idx = int(len(user_prompt_list) * 0.9)
    train_user_data = user_prompt_list[:split_idx]
    valid_user_data = user_prompt_list[split_idx:]  

    train_assistant = assistant_prompt_list[:split_idx]
    valid_assistant = assistant_prompt_list[split_idx:]

    train_system = system_prompts[:split_idx]
    valid_system = system_prompts[split_idx:]
    
    for i in range(len(train_user_data)):
        messages = []
        messages.append({"role": "system", "content": train_system[i][0]})
        for j in range(len(train_user_data[i])):    
            messages.append({"role": "user", "content": train_user_data[i][j]})
            messages.append({"role": "assistant", "content": train_assistant[i][j]})
        conversation = {"messages": messages}
        
        save_conversation_to_json(conversation, output_file_train)

    for i in range(len(valid_user_data)):
        messages = []
        messages.append({"role": "system", "content": valid_system[i][0]})
        for j in range(len(valid_user_data[i])):    
            messages.append({"role": "user", "content": valid_user_data[i][j]})
            messages.append({"role": "assistant", "content": valid_assistant[i][j]})
        conversation = {"messages": messages}
        
        save_conversation_to_json(conversation, output_file_valid)
        
    
    

   


if __name__ == "__main__":
    monomer1s, monomer2s, ers, tgs = load_dataset()
    user_prompt_list_property, assistant_prompt_list_property,system_prompt_list_property,user_prompt_list_group, assistant_prompt_list_group,system_prompt_list_group,user_prompt_list_mix, assistant_prompt_list_mix,system_prompt_list_mix = prepare_multi_turn_prompt(monomer1s, monomer2s, ers, tgs)
    combined_user_prompt_list = user_prompt_list_property + user_prompt_list_group + user_prompt_list_mix
    combined_assistant_prompt_list = assistant_prompt_list_property + assistant_prompt_list_group + assistant_prompt_list_mix
    combined_system_prompt_list = system_prompt_list_property + system_prompt_list_group + system_prompt_list_mix
   
    save_polymer_conversation(combined_user_prompt_list, combined_assistant_prompt_list,combined_system_prompt_list,"training_polymer_for_gpt.jsonl","validation_polymer_for_gpt.jsonl")

    user_prompt_list_property, assistant_prompt_list_property,system_prompt_list_property,user_prompt_list_group, assistant_prompt_list_group,system_prompt_list_group,user_prompt_list_mix, assistant_prompt_list_mix,system_prompt_list_mix = prepare_single_turn_prompt(monomer1s, monomer2s, ers, tgs)
    combined_user_prompt_list_single_turn = user_prompt_list_property + user_prompt_list_group + user_prompt_list_mix
    combined_assistant_prompt_list_single_turn = assistant_prompt_list_property + assistant_prompt_list_group + assistant_prompt_list_mix
    combined_system_prompt_list_single_turn = system_prompt_list_property + system_prompt_list_group + system_prompt_list_mix
   
    save_polymer_conversation(combined_user_prompt_list_single_turn, combined_assistant_prompt_list_single_turn,combined_system_prompt_list_single_turn,"training_polymer_single_turn_for_gpt.jsonl","validation_polymer_single_turn_for_gpt.jsonl")

    both_user_prompt_list = combined_user_prompt_list + combined_user_prompt_list_single_turn
    both_assistant_prompt_list = combined_assistant_prompt_list + combined_assistant_prompt_list_single_turn
    both_system_prompt_list = combined_system_prompt_list + combined_system_prompt_list_single_turn
   
    save_polymer_conversation(both_user_prompt_list, both_assistant_prompt_list,both_system_prompt_list,"training_polymer_both_for_gpt.jsonl","validation_polymer_both_for_gpt.jsonl")  




 

   