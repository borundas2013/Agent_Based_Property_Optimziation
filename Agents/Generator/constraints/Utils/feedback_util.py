import pandas as pd
import os
import json
import re



def read_feedback_data(file_path=None):
    """
    Read JSON/JSONL file, count JSON objects, and return them for access.
    
    Args:
        file_path: Path to the JSON/JSONL file (default: first file in RLHF_TSMP/feedback_data)
    
    Returns:
        list: List of JSON objects from the file
    """
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    print(f"Reading from: {os.path.basename(file_path)}\n")
    
    # Create output file path
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.dirname(file_path)
    output_file = os.path.join(output_dir, f"{base_name}_null_monomers.txt")
    
    json_objects = []
    
    # Read all lines (for JSONL) or entire file (for JSON)
    with open(file_path, 'r', encoding='utf-8') as f, open(output_file, 'w', encoding='utf-8') as out_f:
        if file_path.endswith('.jsonl'):
            # JSONL format: each line is a JSON object
            null_monomer_count = 0
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    try:
                        json_obj = json.loads(line)
                        A_monomer_1 = json_obj.get("candidates", {}).get("A", {}).get("monomer_1")
                        A_monomer_2 = json_obj.get("candidates", {}).get("A", {}).get("monomer_2")
                        B_monomer_1 = json_obj.get("candidates", {}).get("B", {}).get("monomer_1")
                        B_monomer_2 = json_obj.get("candidates", {}).get("B", {}).get("monomer_2")
                        
                        
                        if A_monomer_1 is None or A_monomer_2 is None or B_monomer_1 is None or B_monomer_2 is None:
                            null_monomer_count += 1
                            print(f"Line {line_num}: Found null monomer value")
                            print("Raw text:", json_obj['metadata']['raw_response'])
                            
                            # Write to file
                            out_f.write(f"Line {line_num}: Found null monomer value\n")
                            out_f.write(f"Raw text: {json.dumps(json_obj.get('metadata', {}).get('raw_response', ''), indent=2)}\n")
                            out_f.write("-" * 80 + "\n\n")
                            

                        json_objects.append(json_obj)
                    
                    except json.JSONDecodeError as e:
                        print(f"Line {line_num}: Error parsing JSON - {e}")
                        print(f"  Error at position: {e.pos}")
                        # Show context around the error
                        if e.pos < len(line):
                            start = max(0, e.pos - 50)
                            end = min(len(line), e.pos + 50)
                            context = line[start:end]
                            marker_pos = e.pos - start
                            print(f"  Context: ...{context}...")
                            print(f"  {' ' * (marker_pos + 9)}^")
    
    count = len(json_objects)
    print(f"Total JSON objects found: {count}\n")
    print(f"Total null monomer values found: {null_monomer_count}\n")
    return json_objects

def check_null_monomers(json_obj: dict) -> bool:
    """
    Check if any monomer value is None or missing.
    
    Args:
        json_obj: JSON object containing candidates
        
    Returns:
        bool: True if any monomer is null, False otherwise
    """
    A_monomer_1 = json_obj.get("candidates", {}).get("A", {}).get("monomer_1")
    A_monomer_2 = json_obj.get("candidates", {}).get("A", {}).get("monomer_2")
    B_monomer_1 = json_obj.get("candidates", {}).get("B", {}).get("monomer_1")
    B_monomer_2 = json_obj.get("candidates", {}).get("B", {}).get("monomer_2")
    
    return A_monomer_1 is None or A_monomer_2 is None or B_monomer_1 is None or B_monomer_2 is None


def extract_smiles_from_text(text: str) -> tuple:
    """
    Extract monomer SMILES from raw response text.
    
    Args:
        text: Raw text containing monomer information
        
    Returns:
        tuple: (monomer_1, monomer_2) or (None, None) if not found
    """
    if not text:
        return None, None
    
    monomer_1 = None
    monomer_2 = None
    
    # SMILES pattern: typically starts with capital letter or =, contains alphanumeric, 
    # parentheses, brackets, equals signs, and other chemical symbols
    # Valid SMILES characters: A-Z, a-z, 0-9, =, (, ), [, ], +, -, #, @, /, \, ., %
    # SMILES usually start with C, O, N, =, or similar and are reasonably long
    smiles_pattern = r'[A-Za-z0-9=()\[\]+#@/\\\-.,%]+'
    
    # Pattern 1: "Monomer 1 (description): SMILES" on same line
    pattern1 = r'Monomer\s+1\s*(?:\([^)]+\))?\s*:?\s*(' + smiles_pattern + r')'
    match = re.search(pattern1, text, re.IGNORECASE | re.MULTILINE)
    if match:
        monomer_1 = match.group(1).strip()
    else:
        # Pattern 2: "Monomer 1:" on one line, SMILES on next line
        pattern2 = r'Monomer\s+1\s*(?:\([^)]+\))?\s*:?\s*\n\s*(' + smiles_pattern + r')'
        match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
        if match:
            monomer_1 = match.group(1).strip()
    
    # Pattern for Monomer 2
    pattern1 = r'Monomer\s+2\s*(?:\([^)]+\))?\s*:?\s*(' + smiles_pattern + r')'
    match = re.search(pattern1, text, re.IGNORECASE | re.MULTILINE)
    if match:
        monomer_2 = match.group(1).strip()
    else:
        # Pattern 2: "Monomer 2:" on one line, SMILES on next line
        pattern2 = r'Monomer\s+2\s*(?:\([^)]+\))?\s*:?\s*\n\s*(' + smiles_pattern + r')'
        match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
        if match:
            monomer_2 = match.group(1).strip()
    
    # If we didn't find with "Monomer" labels, try alternative patterns
    if not monomer_1 or not monomer_2:
        # Pattern 3: Two SMILES on separate lines (newline separated)
        # Look for lines that look like SMILES (start with C, O, N, =, etc. and are reasonably long)
        lines = text.split('\n')
        smiles_candidates = []
        for line in lines:
            line = line.strip()
            # Check if line looks like a SMILES (starts with valid char, has reasonable length, contains valid chars)
            if line and len(line) > 3 and re.match(r'^[A-Za-z0-9=()\[\]+#@/\\\-.,%]', line):
                # Remove common prefixes like "Monomer 1:", "SMILES:", etc.
                line = re.sub(r'^(Monomer\s+\d+|SMILES?)\s*:?\s*', '', line, flags=re.IGNORECASE)
                line = line.strip()
                # Check if it still looks like SMILES after cleaning
                if line and len(line) > 3 and re.match(r'^[A-Za-z0-9=()\[\]+#@/\\\-.,%]', line):
                    # Remove trailing descriptive text in parentheses or after certain patterns
                    line = re.split(r'\s*\([^)]*\)\s*$', line)[0]  # Remove trailing (description)
                    line = re.split(r'\s*:\s*[A-Z]', line)[0]  # Remove trailing ": Description"
                    line = line.strip()
                    if line:
                        smiles_candidates.append(line)
        
        # If we found 2+ SMILES candidates, use first two
        if len(smiles_candidates) >= 2:
            if not monomer_1:
                monomer_1 = smiles_candidates[0]
            if not monomer_2:
                monomer_2 = smiles_candidates[1]
        elif len(smiles_candidates) == 1 and not monomer_1:
            monomer_1 = smiles_candidates[0]
        
        # Pattern 4: Comma-separated SMILES (e.g., "SMILES1, SMILES2")
        if not monomer_1 or not monomer_2:
            # Look for comma-separated patterns
            comma_pattern = r'([A-Za-z0-9=()\[\]+#@/\\\-.,%]{5,})\s*,\s*([A-Za-z0-9=()\[\]+#@/\\\-.,%]{5,})'
            match = re.search(comma_pattern, text)
            if match:
                if not monomer_1:
                    monomer_1 = match.group(1).strip()
                if not monomer_2:
                    monomer_2 = match.group(2).strip()
        
        # Pattern 5: SMILES after colon without "Monomer" label (e.g., "description: SMILES")
        if not monomer_1 or not monomer_2:
            # Look for patterns like ": SMILES" that appear after some text
            colon_pattern = r':\s*([A-Za-z0-9=()\[\]+#@/\\\-.,%]{5,})'
            matches = list(re.finditer(colon_pattern, text))
            if len(matches) >= 2:
                if not monomer_1:
                    monomer_1 = matches[0].group(1).strip()
                if not monomer_2:
                    monomer_2 = matches[1].group(1).strip()
            elif len(matches) == 1 and not monomer_1:
                monomer_1 = matches[0].group(1).strip()
    
    # Clean up monomer_1
    if monomer_1:
        # Remove trailing punctuation that's not part of SMILES
        monomer_1 = re.sub(r'[.,;:]+$', '', monomer_1)
        # Remove any trailing text that doesn't look like SMILES (stop at space, newline, or invalid char)
        monomer_1 = re.split(r'[^A-Za-z0-9=()\[\]+#@/\\\-.,%]', monomer_1)[0]
        # Remove very short results (likely not valid SMILES)
        if len(monomer_1) < 3:
            monomer_1 = None
    
    # Clean up monomer_2
    if monomer_2:
        # Remove trailing punctuation that's not part of SMILES
        monomer_2 = re.sub(r'[.,;:]+$', '', monomer_2)
        # Remove any trailing text that doesn't look like SMILES
        monomer_2 = re.split(r'[^A-Za-z0-9=()\[\]+#@/\\\-.,%]', monomer_2)[0]
        # Remove very short results (likely not valid SMILES)
        if len(monomer_2) < 3:
            monomer_2 = None
    
    return monomer_1, monomer_2


def extract_monomers_from_raw_response(json_obj: dict) -> dict:
    """
    Extract monomer SMILES from raw_response if candidates are null.
    
    Args:
        json_obj: JSON object containing candidates and metadata
        
    Returns:
        dict: Updated JSON object with extracted monomers, or original if extraction fails
    """
    raw_response = json_obj.get("metadata", {}).get("raw_response", {})
    
    if not raw_response:
        return json_obj
    
    # Handle both dict format (with "A" and "B" keys) and string format
    if isinstance(raw_response, dict):
        # Extract for candidate A
        text_a = raw_response.get("A", "")
        if text_a:
            monomer_1_a, monomer_2_a = extract_smiles_from_text(text_a)
            if monomer_1_a and json_obj.get("candidates", {}).get("A", {}).get("monomer_1") is None:
                json_obj.setdefault("candidates", {}).setdefault("A", {})["monomer_1"] = monomer_1_a
            if monomer_2_a and json_obj.get("candidates", {}).get("A", {}).get("monomer_2") is None:
                json_obj.setdefault("candidates", {}).setdefault("A", {})["monomer_2"] = monomer_2_a
        
        # Extract for candidate B
        text_b = raw_response.get("B", "")
        if text_b:
            monomer_1_b, monomer_2_b = extract_smiles_from_text(text_b)
            if monomer_1_b and json_obj.get("candidates", {}).get("B", {}).get("monomer_1") is None:
                json_obj.setdefault("candidates", {}).setdefault("B", {})["monomer_1"] = monomer_1_b
            if monomer_2_b and json_obj.get("candidates", {}).get("B", {}).get("monomer_2") is None:
                json_obj.setdefault("candidates", {}).setdefault("B", {})["monomer_2"] = monomer_2_b
    
    elif isinstance(raw_response, str):
        # If raw_response is a single string, try to extract both monomers
        monomer_1, monomer_2 = extract_smiles_from_text(raw_response)
        if monomer_1:
            json_obj.setdefault("candidates", {}).setdefault("A", {})["monomer_1"] = monomer_1
        if monomer_2:
            json_obj.setdefault("candidates", {}).setdefault("A", {})["monomer_2"] = monomer_2
    
    return json_obj


def fix_null_monomers(json_obj: dict) -> dict:
    """
    Check for null monomers and extract from raw_response if needed.
    
    Args:
        json_obj: JSON object to check and fix
        
    Returns:
        dict: Updated JSON object with fixed monomers
    """
    if check_null_monomers(json_obj):
        json_obj = extract_monomers_from_raw_response(json_obj)
    
    return json_obj


def fix_null_monomers_in_file(file_path: str, output_file: str = None) -> list:
    """
    Read a JSONL file, fix null monomers, and optionally save to output file.
    
    Args:
        file_path: Path to input JSONL file
        output_file: Optional path to output file (if None, overwrites input)
        
    Returns:
        list: List of fixed JSON objects
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    if output_file is None:
        output_file = file_path
    
    # Make sure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    fixed_objects = []
    fixed_count = 0
    total_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
        for line_num, line in enumerate(f_in, start=1):
            line = line.strip()
            if line:
                try:
                    json_obj = json.loads(line)
                    total_count += 1
                    
                    # Check if it has null monomers before fixing
                    had_null = check_null_monomers(json_obj)
                    
                    # Fix null monomers
                    json_obj = fix_null_monomers(json_obj)
                    
                    # Check if it was fixed
                    if had_null and not check_null_monomers(json_obj):
                        fixed_count += 1
                        print(f"Line {line_num}: Fixed null monomers")
                    
                    # Write the (possibly fixed) object to output
                    json.dump(json_obj, f_out, ensure_ascii=False)
                    f_out.write("\n")
                    
                    fixed_objects.append(json_obj)
                    
                except json.JSONDecodeError as e:
                    print(f"Line {line_num}: Error parsing JSON - {e}")
                    # Write the original line even if it has errors
                    f_out.write(line + "\n")
    
    print(f"\nSummary:")
    print(f"  Total objects processed: {total_count}")
    print(f"  Objects with null monomers fixed: {fixed_count}")
    print(f"  Output saved to: {output_file}")
    
    return fixed_objects

if __name__ == "__main__":
    llm_feedback_data = "RLHF_TSMP/feedback_data/feedback_data_lama32_fixed.jsonl"
    gptoss_feedback_data = "RLHF_TSMP/feedback_data/feedback_data_gptoss_fixed.jsonl"
    deepseek_feedback_data = "RLHF_TSMP/feedback_data/feedback_data_deepseek_fixed.jsonl"
    
    
    read_feedback_data(llm_feedback_data)
    read_feedback_data(gptoss_feedback_data)
    read_feedback_data(deepseek_feedback_data)
    
    
    #fix_null_monomers_in_file(file_path, output_file)
    #read_feedback_data(output_file)

    # count = 0
    # max_to_show = 5
    
    # with open(file_path, 'r', encoding='utf-8') as f:
    #     for line in f:
    #         line = line.strip()
    #         if line:
    #             try:
    #                 json_obj = json.loads(line)
    #                 if check_null_monomers(json_obj):
    #                     count += 1
    #                     if count <= max_to_show:
    #                         raw_response = json_obj.get("metadata", {}).get("raw_response", {})
                            
    #                         print("=" * 80)
    #                         print(f"Response {count}:")
    #                         print("\nRaw Response:")
    #                         print(json.dumps(raw_response, indent=2))
                            
    #                         # Extract monomers
    #                         if isinstance(raw_response, dict):
    #                             text_a = raw_response.get("A", "")
    #                             text_b = raw_response.get("B", "")
                                
    #                             monomer_1_a, monomer_2_a = extract_smiles_from_text(text_a)
    #                             monomer_1_b, monomer_2_b = extract_smiles_from_text(text_b)
                                
    #                             print("\nExtracted Monomers - Candidate A:")
    #                             print(f"  Monomer 1: {monomer_1_a}")
    #                             print(f"  Monomer 2: {monomer_2_a}")
                                
    #                             print("\nExtracted Monomers - Candidate B:")
    #                             print(f"  Monomer 1: {monomer_1_b}")
    #                             print(f"  Monomer 2: {monomer_2_b}")
    #                             print("=" * 80)
    #                             print()
                            
    #                         if count >= max_to_show:
    #                             break
    #             except json.JSONDecodeError:
    #                 continue

    