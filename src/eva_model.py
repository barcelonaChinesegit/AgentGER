"""EvaModel: Chain-of-Evaluation scoring for figure summaries."""

from typing import Dict, Any, Optional

from .model_loader import get_model
from .prompts import build_eva_prompt, EVA_PROMPT
from .utils import parse_final_json


EVALUATE_PROMPT_SCORE_ONLY = EVA_PROMPT


def evaluate_summary(
    image_path: str,
    summary: str,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: Optional[str] = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
) -> Optional[Dict[str, Any]]:
    """Run EvaModel evaluation and return five scores plus reasoning chains."""
    model = get_model(model_path=model_path, lora_path=lora_path)
    prompt = build_eva_prompt(summary)

    output = model.generate(
        image_path=image_path,
        prompt=prompt,
        max_new_tokens=2048,
        temperature=temperature,
        top_p=top_p,
        do_sample=do_sample,
    )

    result = parse_final_json(output)

    if result is None:
        print("警告: 无法解析 EvaModel 评价结果")
        print(f"原始输出: {output[:500]}...")

    return result


def evaluate_summary_retry(
    image_path: str,
    summary: str,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: Optional[str] = None,
    max_retries: int = 3,
    base_temperature: float = 0.7,
) -> Optional[Dict[str, Any]]:
    """Run EvaModel evaluation with temperature-based retries."""
    temperatures = [base_temperature, base_temperature + 0.1, base_temperature + 0.2]

    for i in range(max_retries):
        temp = temperatures[i] if i < len(temperatures) else base_temperature + 0.1 * i
        print(f"EvaModel 尝试 {i + 1}/{max_retries} (temperature={temp:.2f})")

        result = evaluate_summary(
            image_path=image_path,
            summary=summary,
            model_path=model_path,
            lora_path=lora_path,
            temperature=temp,
            top_p=0.9,
            do_sample=True,
        )

        if result is not None:
            return result

    print("EvaModel 所有重试均失败")
    return None


# Backward-compatible aliases for older scripts.
score_only = evaluate_summary
score_only_retry = evaluate_summary_retry
