from __future__ import annotations

import os
from typing import Dict, Optional

import paths  # noqa: F401
from dotenv import load_dotenv
from openai import OpenAI
from serialization import parse_monomer_json
from template import SYSTEM_PROMPT, build_user_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(user_prompt: str, model: str = "gpt-5-mini") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        seed=42,
    )

    raw = response.choices[0].message.content
    if raw is None:
        raise ValueError("Model returned empty content")
    return raw


def generate_monomers(
    target_tg: Optional[float],
    target_er: Optional[float],
    group1: Optional[str],
    group2: Optional[str],
    prev_m1: Optional[str] = None,
    prev_m2: Optional[str] = None,
    feedback_text: Optional[str] = None,
    model: str = "gpt-5-mini",
) -> Dict[str, str]:
    mode = "revision" if (prev_m1 and prev_m2 and feedback_text) else "initial"

    data = {
        "target_tg": target_tg,
        "target_er": target_er,
        "group1": group1,
        "group2": group2,
        "prev_m1": prev_m1,
        "prev_m2": prev_m2,
        "feedback": feedback_text,
    }

    user_prompt = build_user_prompt(data, mode=mode)
    raw = call_llm(user_prompt=user_prompt, model=model)
    return parse_monomer_json(raw)
