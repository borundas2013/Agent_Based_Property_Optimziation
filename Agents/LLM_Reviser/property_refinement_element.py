from typing import Any, Dict
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

openai_key = os.getenv("OPENAI_API_KEY")


import json
from typing import Dict, Any


import json
from typing import Dict, Any

from typing import Any, Dict, List
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def make_llm_reviser_messages(revision_request: Dict[str, Any]) -> List[Dict[str, str]]:
    target = revision_request["target_properties"]
    cand = revision_request["current_candidate"]
    pred = revision_request["predicted_properties"]
    err = revision_request["error_values"]
    status = revision_request["property_status"]
    diagnosis = revision_request["diagnosis"]
    instr = revision_request["revision_instruction"]
    priority = revision_request["priority_property"]
    mode = revision_request.get("optimization_mode", "joint")

    system_prompt = system_prompt = """You are a chemistry-aware molecular reviser for thermoset shape-memory polymer design.

Your task is to revise an existing two-monomer candidate so that the revised candidate better matches the requested target properties while remaining suitable for thermoset shape-memory polymer applications.

Core chemistry rules:
1. Return exactly two monomers and keep the monomer count unchanged.
2. Preserve the original candidate as much as possible, unless the property gap is large enough to justify a stronger revision.
3. Both revised monomers must be syntactically valid SMILES strings and chemically reasonable.
4. Preserve important reactive/polymerizable functionality whenever possible.
5. Do not make random changes; every edit should support the requested property correction.
6. If a safe chemically reasonable revision is not possible, return the original monomers unchanged and explain briefly in the revision_summary.

Optimization rules:
7. Follow the requested optimization mode strictly.
8. If the mode is tg_first, prioritize Tg correction and avoid damaging Er more than necessary.
9. If the mode is er_first, prioritize Er correction and avoid damaging Tg more than necessary.
10. If the mode is joint, balance both properties together.
11. Preserve properties already within tolerance whenever reasonably possible.
12. Use the provided target-versus-predicted property direction to decide whether Tg and Er should increase, decrease, or be preserved.

Chemistry guidance for property revision:
- To increase Tg, prefer edits that increase rigidity, aromaticity, cyclic constraint, polarity-driven stiffness, or reduce excessive flexible spacer content.
- To decrease Tg, prefer edits that increase chain flexibility, reduce excessive rigidity, or introduce more flexible linkers/spacers.
- To increase Er, prefer edits that preserve or improve reactive/crosslink-supporting functionality and maintain a mechanically supportive structure without making the system unrealistically rigid or invalid.
- To decrease Er, prefer edits that reduce excessive stiffness or overly strong crosslink-driving structure while preserving valid reactive functionality.
- Avoid using the same generic edit for all cases.
- For small property gaps, prefer conservative local edits.
- For large property gaps, stronger but chemically justified revisions are allowed.
- Preserve important polymerizable/reactive groups whenever possible.
- Use these as guidance, not absolute rules; prioritize chemically plausible revisions and property-direction consistency.

JSON formatting rules:
13. Output must be valid JSON parseable by a standard JSON parser.
14. Do NOT include markdown, backticks, comments, labels, or extra prose outside JSON.
15. Use exactly these three keys and no others:
   - "revised_monomer_1"
   - "revised_monomer_2"
   - "revision_summary"

Expected JSON schema:
{
  "revised_monomer_1": "string",
  "revised_monomer_2": "string",
  "revision_summary": "string"
}"""

    if mode == "tg_first":
        mode_instruction = """
Optimization mode: TG_FIRST

Primary goal:
- Move predicted Tg toward the target Tg.

Secondary goal:
- Avoid worsening Er more than necessary.

Mode-specific guidance:
- If Tg is too low, prefer more rigidity, aromaticity, cyclic content, or reduced flexible spacers/linkers.
- If Tg is too high, prefer more flexibility or reduced excessive rigidity.
- Stronger structural edits are allowed if the Tg gap is large.
- Preserve TSMP suitability and important reactive functionality.
"""
    elif mode == "er_first":
        mode_instruction = """
Optimization mode: ER_FIRST

Primary goal:
- Move predicted Er toward the target Er.

Secondary goal:
- Avoid worsening Tg more than necessary.

Mode-specific guidance:
- If Er is too low, prefer changes that improve recovery-stress-supporting structure and effective crosslink-supporting functionality without making the structure unrealistic or invalid.
- If Er is too high, prefer changes that moderate excessive stiffness or overly strong crosslink-driving features.
- Do not use generic Tg-style edits unless they also support Er correction.
- Preserve TSMP suitability and important reactive functionality.
"""
    else:
        mode_instruction = """
Optimization mode: JOINT

Primary goal:
- Improve both Tg and Er together.

Mode-specific guidance:
- Balance rigidity and recoverability.
- Prefer edits that improve the priority property while keeping the other property stable or improved.
- If both properties are outside tolerance, coordinated edits across one or both monomers are allowed when chemically justified.
- Preserve TSMP suitability and important reactive functionality.
"""

    user_prompt = f"""Revise the following two-monomer TSMP candidate based on the property revision request.

Original generation prompt:
{revision_request["original_prompt"]}

Target properties:
- Tg: {target["tg"]}
- Er: {target["er"]}

Current monomer candidate:
- Monomer 1 (SMILES): {cand["monomer_1"]}
- Monomer 2 (SMILES): {cand["monomer_2"]}

Predicted properties of current candidate:
- Predicted Tg: {pred["tg"]}
- Predicted Er: {pred["er"]}

Property revision status:
- Tg: {status["tg"]}
- Er: {status["er"]}
- Priority property: {priority}
- Optimization mode: {mode}

Error values:
- Tg error (dtg): {err["dtg"]}
- Er error (der): {err["der"]}
- Tg tolerance: {err["tol_tg"]}
- Er tolerance: {err["tol_er"]}

Diagnosis summary:
{diagnosis["summary"]}

Recommended actions:
{json.dumps(diagnosis["recommended_actions"], ensure_ascii=False)}

Revision goal:
{instr["goal"]}

Mode-specific instructions:
{mode_instruction}

Important instructions:
- Keep the monomer count at exactly two.
- Keep the revised monomers chemically plausible and valid SMILES.
- Preserve important reactive/polymerizable functionality whenever possible.
- If one property is already within tolerance, avoid changing it unnecessarily.
- If the gap is small, prefer conservative edits.
- If the gap is large, stronger but chemically justified edits are allowed.
- Keep the basic identity of each monomer recognizable unless a more substantial change is clearly needed.

CRITICAL OUTPUT INSTRUCTIONS:
- Respond with a single JSON object only.
- Do NOT include any prose, explanations, markdown formatting, or backticks outside the JSON.
- Use exactly these keys:
  "revised_monomer_1", "revised_monomer_2", "revision_summary"

Return exactly this JSON format:
{{
  "revised_monomer_1": "...",
  "revised_monomer_2": "...",
  "revision_summary": "..."
}}"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_llm_reviser(revision_request: Dict[str, Any]) -> str:
    messages = make_llm_reviser_messages(revision_request)

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
    )

    content = response.choices[0].message.content
    print(content)
    return content

def make_llm_reviser_messages_2(revision_request: Dict[str, Any]):

    system_prompt = """You are a chemistry-aware molecular reviser for thermoset shape-memory polymer design.

Your task is to revise an existing two-monomer candidate to improve only the properties that are flagged for revision, while keeping the overall chemistry and application (thermoset shape-memory polymer) appropriate.

Core rules:
1. Return exactly two monomers and keep the same number of monomers as the original candidate.
2. Preserve the original candidate as much as possible; make minimal necessary changes to the monomer structures.
3. Both revised monomers must be syntactically valid SMILES strings and chemically reasonable.
4. Only revise properties explicitly marked as needing correction; do not intentionally change properties that are already within tolerance.
5. Prefer changes that adjust the priority property while minimally perturbing non-priority properties.
6. If a safe minimal revision is not possible, return the original monomers unchanged and explain briefly in the revision_summary.

JSON formatting rules (very important):
7. Output must be valid JSON that can be parsed by a standard JSON parser.
8. Do NOT include any markdown, backticks, labels, comments, or surrounding text (no ```json, no "Here is the JSON", etc.).
9. Use exactly the following three keys and no others: "revised_monomer_1", "revised_monomer_2", "revision_summary".
10. The values of "revised_monomer_1" and "revised_monomer_2" must be SMILES strings for the two monomers.
11. The "revision_summary" must be a short natural-language explanation of the key structural changes and how they affect the revised properties.

Expected JSON schema:
{
  "revised_monomer_1": "string",
  "revised_monomer_2": "string",
  "revision_summary": "string"
}"""

    target = revision_request["target_properties"]
    cand = revision_request["current_candidate"]
    pred = revision_request["predicted_properties"]
    err = revision_request["error_values"]
    status = revision_request["property_status"]
    diagnosis = revision_request["diagnosis"]
    instr = revision_request["revision_instruction"]
    priority = revision_request["priority_property"]


    user_prompt = f"""Revise the following two-monomer TSMP candidate based on the property revision request.

Original generation prompt:
{revision_request["original_prompt"]}

Target properties:
- Tg: {target["tg"]}
- Er: {target["er"]}

Current monomer candidate:
- Monomer 1 (SMILES): {cand["monomer_1"]}
- Monomer 2 (SMILES): {cand["monomer_2"]}

Predicted properties of current candidate:
- Predicted Tg: {pred["tg"]}
- Predicted Er: {pred["er"]}

Property revision status:
- Tg: {status["tg"]}
- Er: {status["er"]}
- Priority property: {priority}

Error values:
- Tg error (dtg): {err["dtg"]}
- Er error (der): {err["der"]}
- Tg tolerance: {err["tol_tg"]}
- Er tolerance: {err["tol_er"]}

Diagnosis summary:
{diagnosis["summary"]}

Recommended actions:
{json.dumps(diagnosis["recommended_actions"], ensure_ascii=False)}

Revision goal:
{instr["goal"]}

Important instructions:
- Focus revisions on the properties that are outside tolerance, especially the priority property.
- Preserve properties already within tolerance as much as possible.
- Make minimal structural edits that are chemically reasonable for thermoset shape-memory polymer design.
- Keep the monomer count at exactly two and keep the basic identity of each monomer recognizable unless a more substantial change is clearly justified.

CRITICAL OUTPUT INSTRUCTIONS:
- Respond with a single JSON object only.
- Do NOT include any prose, explanations, markdown formatting, or backticks outside the JSON.
- Use exactly these keys: "revised_monomer_1", "revised_monomer_2", "revision_summary".

Return exactly this JSON format (with your own values filled in):
{{
  "revised_monomer_1": "...",
  "revised_monomer_2": "...",
  "revision_summary": "..."
}}"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
def call_llm_reviser( revision_request: Dict[str, Any]) -> Dict[str, Any]:

    messages = make_llm_reviser_messages(revision_request)
    
    response = client.chat.completions.create(
        model='gpt-5-mini',
        messages=messages,
        
    )
    content = response.choices[0].message.content
    print(content)
    return content


def call_repaird_llm_reviser(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    response = client.chat.completions.create(
        model='gpt-5-mini',
        messages=messages,
        
    )
    content = response.choices[0].message.content
    print(content)
    return content