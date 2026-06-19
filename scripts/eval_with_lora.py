"""
使用本地模型 + LoRA 权重对 improved_summary 重新打分
计算与人工标注的一致性（分维度 + 总分）
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import load_jsonl, save_to_jsonl, parse_final_json
from src.model_loader import get_model
from src.prompts import build_eva_prompt


def evaluate_with_local_model(
    human_data: List[Dict[str, Any]],
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: Optional[str] = None,
    output_file: str = "data/output/eval_results/scores_AgentGER_lora.jsonl",
    gpu_id: int = 0,
):
    """
    使用本地模型（可选 LoRA）对 improved_summary 打分
    """
    # 设置 GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    # 加载模型
    print(f"加载模型: {model_path}")
    if lora_path:
        print(f"加载 LoRA: {lora_path}")
    
    model = get_model(model_path=model_path, lora_path=lora_path)
    
    # 加载已有结果（断点续传）
    processed = set()
    if os.path.exists(output_file):
        existing = load_jsonl(output_file)
        processed = {item["image_path"] for item in existing}
        print(f"已有 {len(processed)} 条结果")
    
    # 评估
    total = len(human_data)
    for idx, item in enumerate(human_data):
        image_path = item.get("image_path", "")
        improved_summary = item.get("output", {}).get("improved_summary", "")
        
        if not image_path or not improved_summary:
            continue
        
        if image_path in processed:
            continue
        
        print(f"[{idx+1}/{total}] {image_path}")
        
        # 构建完整图片路径
        full_image_path = os.path.join(PROJECT_ROOT, image_path)
        if not os.path.exists(full_image_path):
            print(f"  警告: 图片不存在")
            continue
        
        # 构建提示词
        prompt = build_eva_prompt(improved_summary)
        
        # 生成
        try:
            output = model.generate(
                image_path=full_image_path,
                prompt=prompt,
                max_new_tokens=2048,
                temperature=0.3,
                do_sample=False,
            )
            
            # 解析结果
            result = parse_final_json(output)
            
            if result and "scores" in result:
                save_to_jsonl({
                    "image_path": image_path,
                    "scores": result["scores"]
                }, output_file)
                print(f"  分数: {result['scores']}")
            else:
                print(f"  解析失败: {output[:200]}...")
                
        except Exception as e:
            print(f"  错误: {e}")


def calculate_dimension_stats(
    human_data: List[Dict[str, Any]],
    model_scores_file: str,
):
    """
    计算各维度的统计指标
    """
    # 加载模型打分
    model_data = load_jsonl(model_scores_file)
    model_map = {item["image_path"]: item["scores"] for item in model_data}
    
    dims = ["faithfulness", "completeness", "conciseness", "logicality", "analysis"]
    
    # 收集分数
    human_dim_scores = {d: [] for d in dims}
    model_dim_scores = {d: [] for d in dims}
    
    for item in human_data:
        image_path = item.get("image_path", "")
        vs = item.get("validation_scores", {})
        
        if not vs or image_path not in model_map:
            continue
        
        ms = model_map[image_path]
        
        for d in dims:
            human_dim_scores[d].append(vs.get(d, 0))
            model_dim_scores[d].append(ms.get(d, 0))
    
    print(f"\n有效数据: {len(human_dim_scores['faithfulness'])} 条")
    print()
    
    # 计算各维度统计
    print("=" * 70)
    print(f"{'维度':<15} {'Pearson':>10} {'Spearman':>10} {'MAE':>10} {'MSE':>10}")
    print("-" * 70)
    
    results = []
    for d in dims:
        h = np.array(human_dim_scores[d])
        m = np.array(model_dim_scores[d])
        
        # 处理常量数组情况
        if np.std(h) == 0 or np.std(m) == 0:
            p, s = 0, 0
        else:
            p, _ = pearsonr(h, m)
            s, _ = spearmanr(h, m)
        
        mae = mean_absolute_error(h, m)
        mse = mean_squared_error(h, m)
        
        print(f"{d:<15} {p:>10.4f} {s:>10.4f} {mae:>10.4f} {mse:>10.4f}")
        results.append({"dimension": d, "pearson": p, "spearman": s, "mae": mae, "mse": mse})
    
    # 总分
    h_total = np.array([sum(human_dim_scores[d][i] for d in dims) for i in range(len(human_dim_scores['faithfulness']))])
    m_total = np.array([sum(model_dim_scores[d][i] for d in dims) for i in range(len(model_dim_scores['faithfulness']))])
    
    p, _ = pearsonr(h_total, m_total)
    s, _ = spearmanr(h_total, m_total)
    mae = mean_absolute_error(h_total, m_total)
    mse = mean_squared_error(h_total, m_total)
    
    print("-" * 70)
    print(f"{'总分':<15} {p:>10.4f} {s:>10.4f} {mae:>10.4f} {mse:>10.4f}")
    print("=" * 70)
    
    results.append({"dimension": "total", "pearson": p, "spearman": s, "mae": mae, "mse": mse})
    
    return results


def main():
    parser = argparse.ArgumentParser(description="使用本地模型+LoRA评估")
    parser.add_argument("--human_data", required=True, help="人工标注数据 JSONL")
    parser.add_argument("--model_path", default="./Qwen3-VL-8B-Instruct", help="基础模型路径")
    parser.add_argument("--lora_path", default="lora_weights/eva_model", help="EvaModel LoRA权重路径")
    parser.add_argument("--output_file", default="data/output/eval_results/scores_AgentGER_lora.jsonl", help="输出文件")
    parser.add_argument("--gpu", type=int, default=0, help="GPU ID")
    parser.add_argument("--skip_eval", action="store_true", help="跳过评估，仅计算统计")
    args = parser.parse_args()
    
    # 加载人工数据
    print("加载人工标注数据...")
    human_data_path = os.path.join(PROJECT_ROOT, args.human_data)
    human_data = load_jsonl(human_data_path)
    
    # 筛选有效数据
    valid_data = [item for item in human_data if item.get("validation_scores") and item.get("output", {}).get("improved_summary")]
    print(f"有效数据: {len(valid_data)} 条")
    
    if not args.skip_eval:
        # 使用本地模型评估
        output_path = os.path.join(PROJECT_ROOT, args.output_file)
        lora_path = os.path.join(PROJECT_ROOT, args.lora_path) if args.lora_path else None
        
        evaluate_with_local_model(
            human_data=valid_data,
            model_path=args.model_path,
            lora_path=lora_path,
            output_file=output_path,
            gpu_id=args.gpu,
        )
    
    # 计算统计指标
    output_path = os.path.join(PROJECT_ROOT, args.output_file)
    if os.path.exists(output_path):
        print("\n=== AgentGER (LoRA) 各维度统计 ===")
        results = calculate_dimension_stats(valid_data, output_path)
        
        # 保存结果
        result_file = output_path.replace(".jsonl", "_stats.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n统计结果已保存到: {result_file}")


if __name__ == "__main__":
    main()
