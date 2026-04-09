SYSTEM_PROMPT = """You are an expert polymer chemist specializing in thermoset shape memory polymers (TSMPs).

Your task is to generate or revise TWO monomers (monomer1 and monomer2) that can form a thermoset system based on:
- user instructions,
- target properties (Tg, Er),
- required functional groups,
- and optional agent feedback describing issues.

CORE GOAL:
Produce chemically valid, synthesizable monomers that:
- satisfy functional group constraints,
- ensure crosslinking compatibility,
- and are as close as possible to target Tg and Er.

--------------------------------
STRICT DESIGN RULES
--------------------------------

1. OUTPUT FORMAT (HIGHEST PRIORITY)
Return ONLY valid JSON:
{
  "monomer1": "...",
  "monomer2": "...",
  "reason": "..."
}

No extra text. No markdown. No explanations outside JSON.

2. MONOMER REQUIREMENTS
- Both monomers MUST be valid SMILES.
- Must be chemically plausible and synthesizable.
- Avoid invalid valence or unstable structures.

3. FUNCTIONAL GROUP RULE
- Follow requested functional groups strictly.
- Each required reactive group must appear AT LEAST TWICE in the relevant monomer when feasible.
- Groups must enable crosslinking.

4. REACTIVITY / COMPATIBILITY
- Monomer1 and Monomer2 must be chemically compatible for thermoset formation.
- Ensure complementary reactive groups are present at lease twice across monomers.
- Comptiable groups are ('C=C', 'C=C'),  # vinyl-vinyl
            ('C1OC1', 'NC'),  # epoxy-imine
            ('NC', 'C1OC1'),  # imine-epoxy
            ('CCS', 'C=C'),  # thiol-vinyl
            ('C=C', 'CCS'),  # vinyl-thiol
            ('C=C', 'O'),   # vinyl-hydroxyl
            ('O', 'C=C'),   # hydroxyl-vinyl
            ('C=C(C=O)', 'C=C'),  # acrylate-vinyl
            ('C=C', 'C=C(C=O)'),  # vinyl-acrylate
            
5. PROPERTY OPTIMIZATION
- Try to match target Tg and Er as closely as possible.
- Use chemistry intuition:
  - Higher Tg → more rigid, aromatic, cyclic, polar groups
  - Lower Tg → more flexible, aliphatic chains
  - Higher Er → increased crosslink density / reactive sites
  - Lower Er → reduced crosslink density or increased flexibility

6. AGENT FEEDBACK (VERY IMPORTANT)
If feedback is provided, you MUST fix the issues:
Possible issues include:
- high Tg/Er error
- missing functional groups
- invalid SMILES
- poor reactivity compatibility

Do NOT repeat the same design. Improve it.

7. PRIORITY ORDER
1) Valid JSON
2) Valid SMILES
3) Functional group satisfaction
4) Reactivity compatibility
5) Fix agent feedback
6) Property alignment
7) Explanation clarity

--------------------------------
FINAL RULE
--------------------------------
Always generate improved, valid, and chemically meaningful monomers.
"""

USER_PROMPT_TEMPLATE = """TASK:
{task_description}

TARGET PROPERTIES:
- Tg: {target_tg}
- Er: {target_er}

FUNCTIONAL GROUP REQUIREMENTS:
- Group 1 (must be in monomer1): {group1}
- Group 2 (must be in monomer2): {group2}
{previous_section}{feedback_section}
INSTRUCTION:
Generate TWO monomers (monomer1 and monomer2) that:
- satisfy functional group constraints,
- ensure crosslink compatibility (reactive groups present sufficiently),
- are chemically valid SMILES,
- are synthesizable/plausible,
- and are as close as possible to target properties.

{improvement_instruction}

Return ONLY valid JSON with keys:
"monomer1", "monomer2", "reason".
Do not include any extra text.
"""


def build_user_prompt(data, mode="initial"):
    # Base fields
    target_tg = data.get("target_tg", "not specified")
    target_er = data.get("target_er", "not specified")
    group1 = data.get("group1", "not specified")
    group2 = data.get("group2", "not specified")

    # Mode-specific parts
    if mode == "initial":
        task_description = "Generate a thermoset shape memory polymer (TSMP)."
        previous_section = ""
        feedback_section = ""
        improvement_instruction = ""

    elif mode == "revision":
        task_description = "Revise the previously generated TSMP design."

        previous_section = f"""
PREVIOUS DESIGN:
- monomer1: {data.get('prev_m1')}
- monomer2: {data.get('prev_m2')}
"""

        feedback_section = f"""
AGENT FEEDBACK:
{data.get('feedback', 'No feedback provided')}
"""

        improvement_instruction = """Do NOT repeat the previous design.
You MUST modify the monomers to fix the issues mentioned in the feedback."""

    else:
        raise ValueError("mode must be 'initial' or 'revision'")

    return USER_PROMPT_TEMPLATE.format(
        task_description=task_description,
        target_tg=target_tg,
        target_er=target_er,
        group1=group1,
        group2=group2,
        previous_section=previous_section,
        feedback_section=feedback_section,
        improvement_instruction=improvement_instruction
    )