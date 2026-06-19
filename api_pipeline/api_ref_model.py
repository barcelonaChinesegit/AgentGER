"""API-backed RefModel wrapper."""

from typing import Dict, Any, Optional

from .api_model import get_model
from src.prompts import build_ref_prompt, REF_PROMPT
from src.utils import parse_final_json


EVALUATE_PROMPT_WITH_IMPROVEMENT = REF_PROMPT


def evaluate_with_improvement(
    image_path: str,
    summary: str,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
) -> Optional[Dict[str, Any]]:
    """Run RefModel-style evaluation-guided refinement via the API model."""
    model = get_model()
    output = model.generate(
        image_path=image_path,
        prompt=build_ref_prompt(summary),
        max_new_tokens=2048,
        temperature=temperature,
        top_p=top_p,
        do_sample=do_sample,
    )

    if not output:
        print("警告: API 返回空结果")
        return None

    result = parse_final_json(output)
    if result is None:
        print("警告: 无法解析 RefModel API 结果")
        print(f"原始输出: {output[:500]}...")
    return result


def evaluate_with_improvement_retry(
    image_path: str,
    summary: str,
    max_retries: int = 3,
    base_temperature: float = 0.7,
) -> Optional[Dict[str, Any]]:
    """Run API RefModel with temperature-based retries."""
    temperatures = [base_temperature, base_temperature + 0.1, base_temperature + 0.2]

    for i in range(max_retries):
        temp = temperatures[i] if i < len(temperatures) else base_temperature + 0.1 * i
        print(f"API RefModel 尝试 {i + 1}/{max_retries} (temperature={temp:.2f})")
        result = evaluate_with_improvement(
            image_path=image_path,
            summary=summary,
            temperature=temp,
            top_p=0.9,
            do_sample=True,
        )
        if result is not None:
            return result

    print("API RefModel 所有重试均失败")
    return None
