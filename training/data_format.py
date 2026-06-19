"""Convert AgentGER JSONL records into Qwen3-VL chat training data."""
import json
import sys
from typing import List, Dict, Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prompts import build_eva_prompt, build_ref_prompt


def load_jsonl(input_path: str) -> List[Dict[str, Any]]:
    """加载 JSONL 文件"""
    data = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def format_output_json(output: Dict[str, Any], include_improved_summary: bool = True) -> str:
    """
    格式化输出为 <evaluation>...</evaluation> 格式
    如果 include_improved_summary 为 True，还会添加 <modification>...</modification> 部分
    """
    evaluation_result = {
        "scores": output.get("scores", {}),
        "reasons": output.get("reasons", {}),
    }
    
    if include_improved_summary:
        modification_result = {
            "improved_summary": output.get("improved_summary", ""),
        }
        return f"<evaluation>\n{json.dumps(evaluation_result, ensure_ascii=False)}\n</evaluation>\n<modification>\n{json.dumps(modification_result, ensure_ascii=False)}\n</modification>"
    else:
        return f"<evaluation>\n{json.dumps(evaluation_result, ensure_ascii=False)}\n</evaluation>"


def convert_to_training_format(
    input_path: str,
    output_path: str,
    include_improved_summary: bool = True,
):
    """
    将 JSONL 数据转换为训练格式
    
    Args:
        input_path: 输入 JSONL 文件路径
        output_path: 输出训练数据文件路径
        include_improved_summary: 是否包含 improved_summary
    """
    data = load_jsonl(input_path)
    
    training_data = []
    
    for item in data:
        image_path = item.get("image_path", "")
        original_summary = item.get("original_summary", "")
        output = item.get("output", {})
        
        # 构建 prompt
        prompt = (
            build_ref_prompt(original_summary)
            if include_improved_summary
            else build_eva_prompt(original_summary)
        )
        
        # 构建 response
        response = format_output_json(output, include_improved_summary)
        
        training_item = {
            "image": image_path,
            "conversations": [
                {
                    "role": "user",
                    "content": prompt,
                },
                {
                    "role": "assistant",
                    "content": response,
                },
            ],
        }
        
        training_data.append(training_item)
        
    # 保存
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
        
    print(f"转换完成: {len(training_data)} 条数据")
    print(f"输出文件: {output_path}")


def generate_training_files(
    input_path: str,
    output_dir: str = "./data/output",
):
    """
    一次性生成两个训练数据文件
    
    Args:
        input_path: 输入 JSONL 文件路径
        output_dir: 输出目录路径
        
    生成文件:
        - ref_training_data.json: 包含 improved_summary (RefModel)
        - eva_training_data.json: 不包含 improved_summary (EvaModel)
    """
    # 确保输出目录存在
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    # 加载数据（只加载一次）
    data = load_jsonl(input_path)
    print(f"加载数据: {len(data)} 条记录")
    
    # 生成 RefModel 训练数据 (包含 improved_summary)
    l1_output_path = output_dir_path / "ref_training_data.json"
    l1_training_data = []
    
    for item in data:
        image_path = item.get("image_path", "")
        original_summary = item.get("original_summary", "")
        output = item.get("output", {})
        
        prompt = build_ref_prompt(original_summary)
        response = format_output_json(output, include_improved_summary=True)
        
        l1_training_data.append({
            "image": image_path,
            "conversations": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ],
        })
    
    with open(l1_output_path, "w", encoding="utf-8") as f:
        json.dump(l1_training_data, f, ensure_ascii=False, indent=2)
    print(f"生成 RefModel 训练数据: {l1_output_path} ({len(l1_training_data)} 条)")
    
    # 生成 EvaModel 训练数据 (不包含 improved_summary)
    l2_output_path = output_dir_path / "eva_training_data.json"
    l2_training_data = []
    
    for item in data:
        image_path = item.get("image_path", "")
        original_summary = item.get("original_summary", "")
        output = item.get("output", {})
        
        prompt = build_eva_prompt(original_summary)
        response = format_output_json(output, include_improved_summary=False)
        
        l2_training_data.append({
            "image": image_path,
            "conversations": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ],
        })
    
    with open(l2_output_path, "w", encoding="utf-8") as f:
        json.dump(l2_training_data, f, ensure_ascii=False, indent=2)
    print(f"生成 EvaModel 训练数据: {l2_output_path} ({len(l2_training_data)} 条)")
    
    print("\n训练数据生成完成!")
    print(f"  - RefModel (含 improved_summary): {l1_output_path}")
    print(f"  - EvaModel (不含 improved_summary): {l2_output_path}")
    
    return str(l1_output_path), str(l2_output_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据格式转换")
    parser.add_argument("--input", required=True, help="输入 JSONL 文件路径")
    parser.add_argument("--output", default=None, help="输出训练数据文件路径（单文件模式）")
    parser.add_argument("--output-dir", default="./data/output", help="输出目录（批量模式）")
    parser.add_argument(
        "--no-improved-summary",
        action="store_true",
        help="不包含 improved_summary（用于 EvaModel）",
    )
    parser.add_argument(
        "--generate-both",
        action="store_true",
        help="一次性生成 EvaModel 和 RefModel 两个训练数据文件",
    )
    
    args = parser.parse_args()
    
    if args.generate_both:
        # 批量生成两个文件
        generate_training_files(
            input_path=args.input,
            output_dir=args.output_dir,
        )
    else:
        # 单文件模式
        if not args.output:
            parser.error("单文件模式需要指定 --output 参数")
        convert_to_training_format(
            input_path=args.input,
            output_path=args.output,
            include_improved_summary=not args.no_improved_summary,
        )
