# from typing import Any, Dict
# import os
# from openai import OpenAI
# from dotenv import load_dotenv
# from typing import List
# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# openai_key = os.getenv("OPENAI_API_KEY")


# import json
# from typing import Dict, Any


# import json
# from typing import Dict, Any

# from typing import Any, Dict, List
# import json
# import os
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# def make_llm_reviser_messages(revision_request: Dict[str, Any]) -> List[Dict[str, str]]:
#     target = revision_request["target_properties"]
#     cand = revision_request["current_candidate"]
#     pred = revision_request["predicted_properties"]
#     err = revision_request["error_values"]
#     status = revision_request["property_status"]
#     diagnosis = revision_request["diagnosis"]
#     instr = revision_request["revision_instruction"]
#     priority = revision_request["priority_property"]
#     mode = revision_request.get("optimization_mode", "joint")
#     focus_property = str(revision_request.get("focus_property", "")).lower()
#     if focus_property not in {"tg", "er"}:
#         raise ValueError("focus_property must be either 'tg' or 'er' for single-property revision.")

#     if focus_property == "tg":
#         system_prompt = """You are a chemistry-aware molecular reviser for thermoset shape-memory polymer design.

# Your task is to revise an existing two-monomer candidate to better match the requested Tg target only, while remaining suitable for thermoset shape-memory polymer applications.

# Core chemistry rules:
# 1. Return exactly two monomers and keep the monomer count unchanged.
# 2. Preserve the original candidate as much as possible, unless the Tg gap is large enough to justify a stronger revision.
# 3. Both revised monomers must be syntactically valid SMILES strings and chemically reasonable.
# 4. Preserve important reactive/polymerizable functionality whenever possible.
# 5. Do not make random changes; every edit should support Tg correction.
# 6. If a safe chemically reasonable revision is not possible, return the original monomers unchanged and explain briefly in the revision_summary.

# Single-property optimization rules:
# 7. Optimize Tg only.
# 8. Do not optimize Er and do not use Er as a decision criterion.
# 9. Use target-versus-predicted Tg direction to decide whether Tg should increase, decrease, or be preserved.

# Chemistry guidance for Tg revision:
# - To increase Tg, prefer edits that increase rigidity, aromaticity, cyclic constraint, polarity-driven stiffness, or reduce excessive flexible spacer content.
# - To decrease Tg, prefer edits that increase chain flexibility, reduce excessive rigidity, or introduce more flexible linkers/spacers.
# - Avoid using the same generic edit for all cases.
# - For small Tg gaps, prefer conservative local edits.
# - For large Tg gaps, stronger but chemically justified revisions are allowed.
# - Preserve important polymerizable/reactive groups whenever possible.
# - Use these as guidance, not absolute rules; prioritize chemically plausible revisions and Tg-direction consistency.

# JSON formatting rules:
# 10. Output must be valid JSON parseable by a standard JSON parser.
# 11. Do NOT include markdown, backticks, comments, labels, or extra prose outside JSON.
# 12. Use exactly these three keys and no others:
#    - "revised_monomer_1"
#    - "revised_monomer_2"
#    - "revision_summary"

# Expected JSON schema:
# {
#   "revised_monomer_1": "string",
#   "revised_monomer_2": "string",
#   "revision_summary": "string"
# }"""
#     elif focus_property == "er":
#         system_prompt = """You are a chemistry-aware molecular reviser for thermoset shape-memory polymer design.

# Your task is to revise an existing two-monomer candidate to better match the requested Er target only, while remaining suitable for thermoset shape-memory polymer applications.

# Core chemistry rules:
# 1. Return exactly two monomers and keep the monomer count unchanged.
# 2. Preserve the original candidate as much as possible, unless the Er gap is large enough to justify a stronger revision.
# 3. Both revised monomers must be syntactically valid SMILES strings and chemically reasonable.
# 4. Preserve important reactive/polymerizable functionality whenever possible.
# 5. Do not make random changes; every edit should support Er correction.
# 6. If a safe chemically reasonable revision is not possible, return the original monomers unchanged and explain briefly in the revision_summary.

# Single-property optimization rules:
# 7. Optimize Er only.
# 8. Do not optimize Tg and do not use Tg as a decision criterion.
# 9. Use target-versus-predicted Er direction to decide whether Er should increase, decrease, or be preserved.

# Chemistry guidance for Er revision:
# - To increase Er, prefer edits that preserve or improve reactive/crosslink-supporting functionality and maintain a mechanically supportive structure without making the system unrealistically rigid or invalid.
# - To decrease Er, prefer edits that reduce excessive stiffness or overly strong crosslink-driving structure while preserving valid reactive functionality.
# - Avoid using the same generic edit for all cases.
# - For small Er gaps, prefer conservative local edits.
# - For large Er gaps, stronger but chemically justified revisions are allowed.
# - Preserve important polymerizable/reactive groups whenever possible.
# - Use these as guidance, not absolute rules; prioritize chemically plausible revisions and Er-direction consistency.

# JSON formatting rules:
# 10. Output must be valid JSON parseable by a standard JSON parser.
# 11. Do NOT include markdown, backticks, comments, labels, or extra prose outside JSON.
# 12. Use exactly these three keys and no others:
#    - "revised_monomer_1"
#    - "revised_monomer_2"
#    - "revision_summary"
# 13. If property gap is large:
# - You are allowed to modify BOTH monomers
# - Coordinated edits across both monomers are encouraged

# Expected JSON schema:
# {
#   "revised_monomer_1": "string",
#   "revised_monomer_2": "string",
#   "revision_summary": "string"
# }"""
#     if focus_property == "tg":
#         mode_instruction = """
# Optimization mode: TG_ONLY

# Primary goal:
# - Move predicted Tg toward the target Tg.

# Mode-specific guidance:
# - If Tg is too low, prefer more rigidity, aromaticity, cyclic content, or reduced flexible spacers/linkers.
# - If Tg is too high, prefer more flexibility or reduced excessive rigidity.
# - Stronger structural edits are allowed if the Tg gap is large.
# - Ignore Er entirely for optimization decisions.
# """
#     elif focus_property == "er":
#         mode_instruction = """
# Optimization mode: ER_ONLY

# Primary goal:
# - Move predicted Er toward the target Er.

# Mode-specific guidance:
# - If Er is too low, prefer changes that improve recovery-stress-supporting structure and effective crosslink-supporting functionality without making the structure unrealistic or invalid.
# - If Er is too high, prefer changes that moderate excessive stiffness or overly strong crosslink-driving features.
# - Ignore Tg entirely for optimization decisions.
# """
    

#     if focus_property == "tg":
#         target_block = f"""Target property:
# - Tg: {target["tg"]}"""
#         predicted_block = f"""Predicted property of current candidate:
# - Predicted Tg: {pred["tg"]}"""
#         status_block = f"""Property revision status:
# - Tg: {status["tg"]}
# - Priority property: Tg
# - Optimization mode: tg_only"""
#         error_block = f"""Error values:
# - Tg error (dtg): {err["dtg"]}
# - Tg tolerance: {err["tol_tg"]}"""
#         focus_instruction = """Single-property focus instructions:
# - Optimize ONLY Tg.
# - Do NOT optimize Er.
# - Ignore Er target/error/status even if present in metadata.
# - Choose edits only based on Tg direction and chemistry plausibility."""
#     elif focus_property == "er":
#         target_block = f"""Target property:
# - Er: {target["er"]}"""
#         predicted_block = f"""Predicted property of current candidate:
# - Predicted Er: {pred["er"]}"""
#         status_block = f"""Property revision status:
# - Er: {status["er"]}
# - Priority property: Er
# - Optimization mode: er_only"""
#         error_block = f"""Error values:
# - Er error (der): {err["der"]}
# - Er tolerance: {err["tol_er"]}"""
#         focus_instruction = """Single-property focus instructions:
# - Optimize ONLY Er.
# - Do NOT optimize Tg.
# - Ignore Tg target/error/status even if present in metadata.
# - Choose edits only based on Er direction and chemistry plausibility."""
#     else:
#         target_block = f"""Target property:
# - Er: {target["er"]}"""
#         predicted_block = f"""Predicted property of current candidate:
# - Predicted Er: {pred["er"]}"""
#         status_block = f"""Property revision status:
# - Er: {status["er"]}
# - Priority property: Er
# - Optimization mode: er_only"""
#         error_block = f"""Error values:
# - Er error (der): {err["der"]}
# - Er tolerance: {err["tol_er"]}"""
#         focus_instruction = """Single-property focus instructions:
# - Optimize ONLY Er.
# - Do NOT optimize Tg.
# - Ignore Tg target/error/status even if present in metadata.
# - Choose edits only based on Er direction and chemistry plausibility."""

#     user_prompt = f"""Revise the following two-monomer TSMP candidate based on the property revision request.

# Original generation prompt:
# {revision_request["original_prompt"]}

# {target_block}

# Current monomer candidate:
# - Monomer 1 (SMILES): {cand["monomer_1"]}
# - Monomer 2 (SMILES): {cand["monomer_2"]}

# {predicted_block}

# {status_block}

# {error_block}

# Diagnosis summary:
# {diagnosis["summary"]}

# Recommended actions:
# {json.dumps(diagnosis["recommended_actions"], ensure_ascii=False)}

# Revision goal:
# {instr["goal"]}

# Mode-specific instructions:
# {mode_instruction}

# Property-focus instructions:
# {focus_instruction}

# Important instructions:
# - Keep the monomer count at exactly two.
# - Keep the revised monomers chemically plausible and valid SMILES.
# - Preserve important reactive/polymerizable functionality whenever possible.
# - If one property is already within tolerance, avoid changing it unnecessarily.
# - If the gap is small, prefer conservative edits.
# - If the gap is large, stronger but chemically justified edits are allowed.
# - Keep the basic identity of each monomer recognizable unless a more substantial change is clearly needed.

# CRITICAL OUTPUT INSTRUCTIONS:
# - Respond with a single JSON object only.
# - Do NOT include any prose, explanations, markdown formatting, or backticks outside the JSON.
# - Use exactly these keys:
#   "revised_monomer_1", "revised_monomer_2", "revision_summary"

# Return exactly this JSON format:
# {{
#   "revised_monomer_1": "...",
#   "revised_monomer_2": "...",
#   "revision_summary": "..."
# }}"""

#     return [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": user_prompt},
#     ]



# def call_llm_reviser( revision_request: Dict[str, Any]) -> Dict[str, Any]:

#     messages = make_llm_reviser_messages(revision_request)
   
    
#     response = client.chat.completions.create(
#         model="gpt-5-mini",#'gpt-5-mini',
#         messages=messages,
#         seed=42,
#     )
#     content = response.choices[0].message.content
#     print(content)
#     return content

