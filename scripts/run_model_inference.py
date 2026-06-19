#!/usr/bin/env python3
"""
模型推理脚本
使用 RefModel LoRA 对人工验证数据进行推理。
生成新的 improved_summary 和评分

使用方式:
  CUDA_VISIBLE_DEVICES=5 python scripts/run_model_inference.py --input ./data/output/golden_test.jsonl
或:
  python scripts/run_model_inference.py --input ./data/output/golden_test.jsonl --gpu 5
"""
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 检查是否需要自动选择 GPU（必须在导入 torch 之前完成）
def _auto_select_gpu():
    """在脚本最开始自动选择空闲 GPU"""
    # 如果已经设置了 CUDA_VISIBLE_DEVICES，不做处理
    if os.environ.get("CUDA_VISIBLE_DEVICES"):
        return
    
    # 检查命令行参数中是否有 --gpu
    for i, arg in enumerate(sys.argv):
        if arg == "--gpu" and i + 1 < len(sys.argv):
            gpu_id = sys.argv[i + 1]
            os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
            print(f"[预设置] CUDA_VISIBLE_DEVICES={gpu_id}")
            return
    
    # 自动选择最空闲的 GPU
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=True
        )
        
        best_gpu = None
        best_free_ratio = 0
        
        for line in result.stdout.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                idx = int(parts[0])
                mem_used = float(parts[1])
                mem_total = float(parts[2])
                util = float(parts[3])
                free_ratio = (mem_total - mem_used) / mem_total
                
                # 选择空闲内存比例最高且利用率低的 GPU
                if free_ratio > 0.5 and util < 50:
                    if free_ratio > best_free_ratio:
                        best_gpu = idx
                        best_free_ratio = free_ratio
        
        if best_gpu is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = str(best_gpu)
            print(f"[自动选择] CUDA_VISIBLE_DEVICES={best_gpu} (空闲 {best_free_ratio*100:.1f}%)")
        
    except Exception as e:
        print(f"[警告] 无法自动选择 GPU: {e}")

# 在任何 torch 相关导入之前执行
_auto_select_gpu()


def get_free_gpu() -> Tuple[int, float]:
    """
    查询并选择最空闲的 GPU
    
    Returns:
        (gpu_id, free_memory_ratio): GPU ID 和空闲内存比例
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=True
        )
        
        gpus = []
        for line in result.stdout.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                idx = int(parts[0])
                mem_used = float(parts[1])
                mem_total = float(parts[2])
                util = float(parts[3])
                free_ratio = (mem_total - mem_used) / mem_total
                gpus.append((idx, mem_used, mem_total, util, free_ratio))
        
        if not gpus:
            return 0, 0.0
        
        # 选择空闲内存比例最高且利用率最低的 GPU
        # 优先考虑空闲内存比例 > 50% 且利用率 < 50% 的 GPU
        best_gpu = None
        for gpu in gpus:
            idx, mem_used, mem_total, util, free_ratio = gpu
            if free_ratio > 0.5 and util < 50:
                if best_gpu is None or free_ratio > best_gpu[4]:
                    best_gpu = gpu
        
        # 如果没有找到理想的 GPU，选择空闲内存最多的
        if best_gpu is None:
            best_gpu = max(gpus, key=lambda x: x[4])
        
        print(f"\nGPU 状态:")
        for gpu in gpus:
            idx, mem_used, mem_total, util, free_ratio = gpu
            marker = " <-- 选择" if gpu == best_gpu else ""
            print(f"  GPU {idx}: {mem_used:.0f}/{mem_total:.0f} MiB ({free_ratio*100:.1f}% 空闲), 利用率 {util:.0f}%{marker}")
        
        return best_gpu[0], best_gpu[4]
        
    except Exception as e:
        print(f"警告: 无法查询 GPU 状态: {e}")
        return 0, 0.0


def load_jsonl(file_path: str) -> List[Dict]:
    """加载 JSONL 文件"""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def run_inference(
    input_path: str,
    output_path: str,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: str = "./lora_weights/ref_model_distill",
    resume: bool = True,
    gpu_id: Optional[int] = None,
):
    """
    运行模型推理
    
    Args:
        input_path: 输入数据集路径
        output_path: 输出结果路径
        model_path: 基础模型路径
        lora_path: LoRA 权重路径
        resume: 是否断点续传
        gpu_id: 指定使用的 GPU ID，None 表示自动选择
    """
    print("=" * 60)
    print("模型推理 - 使用 LoRA 生成 improved_summary")
    print("=" * 60)
    
    # 显示当前 CUDA 设置
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "未设置")
    print(f"CUDA_VISIBLE_DEVICES: {cuda_devices}")
    
    # 导入需要 torch 的模块（此时 CUDA_VISIBLE_DEVICES 已在脚本开始时设置）
    # 添加项目根目录到路径
    PROJECT_ROOT = Path(__file__).parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    from tqdm import tqdm
    from src.ref_model import refine_summary
    from src.utils import save_to_jsonl, get_processed_images
    
    print(f"\n输入: {input_path}")
    print(f"输出: {output_path}")
    print(f"模型: {model_path}")
    print(f"LoRA: {lora_path}")
    
    # 检查 LoRA 是否存在
    if not os.path.exists(lora_path):
        print(f"\n警告: LoRA 路径不存在 {lora_path}")
        print("将使用基础模型进行推理")
        lora_path = None
    
    # 创建输出目录
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 加载数据集
    print("\n加载数据集...")
    data = load_jsonl(input_path)
    print(f"共 {len(data)} 条记录")
    
    # 检查已处理的图片（断点续传）
    processed_images = set()
    if resume and os.path.exists(output_path):
        processed_images = get_processed_images(output_path)
        print(f"发现 {len(processed_images)} 条已处理记录，将跳过")
    
    # 过滤待处理数据
    pending_data = [
        item for item in data
        if item.get("image_path", "") not in processed_images
    ]
    
    if not pending_data:
        print("所有数据已处理完成")
        return
    
    print(f"待处理: {len(pending_data)} 条")
    
    # 开始推理
    success_count = len(processed_images)
    fail_count = 0
    
    pbar = tqdm(pending_data, desc="推理中", unit="条", ncols=100)
    
    for item in pbar:
        image_path = item.get("image_path", "")
        original_summary = item.get("original_summary", "")
        
        # 人工标注数据
        human_output = item.get("output", {})
        human_validation_scores = item.get("validation_scores", {})
        human_improved_summary = human_output.get("improved_summary", "")
        
        # 调用模型
        try:
            result = refine_summary(
                image_path=image_path,
                summary=original_summary,
                model_path=model_path,
                lora_path=lora_path,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
            )
            
            if result is None:
                fail_count += 1
                pbar.set_postfix({"成功": success_count, "失败": fail_count})
                continue
            
            # 构建输出数据
            output_data = {
                "image_path": image_path,
                "original_summary": original_summary,
                "model_output": {
                    "scores": result.get("scores", {}),
                    "reasons": result.get("reasons", {}),
                    "improved_summary": result.get("improved_summary", ""),
                },
                "human_reference": {
                    "scores": human_validation_scores,
                    "improved_summary": human_improved_summary,
                },
                "quality_level": item.get("quality_level", ""),
            }
            
            # 保存结果
            save_to_jsonl(output_data, output_path)
            success_count += 1
            
        except Exception as e:
            fail_count += 1
            tqdm.write(f"错误 {image_path}: {e}")
        
        pbar.set_postfix({"成功": success_count, "失败": fail_count})
    
    pbar.close()
    
    print("\n" + "=" * 60)
    print("推理完成")
    print("=" * 60)
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  输出: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="模型推理脚本")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入数据集路径（JSONL）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./data/output/dataset_model.jsonl",
        help="输出结果路径",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default="./Qwen3-VL-8B-Instruct",
        help="基础模型路径",
    )
    parser.add_argument(
        "--lora_path",
        type=str,
        default="./lora_weights/ref_model_distill",
        help="LoRA 权重路径",
    )
    parser.add_argument(
        "--no_resume",
        action="store_true",
        help="不使用断点续传",
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=None,
        help="指定使用的 GPU ID，不指定则自动选择空闲 GPU",
    )
    
    args = parser.parse_args()
    
    run_inference(
        input_path=args.input,
        output_path=args.output,
        model_path=args.model_path,
        lora_path=args.lora_path,
        resume=not args.no_resume,
        gpu_id=args.gpu,
    )


if __name__ == "__main__":
    main()
