"""AgentGER pipeline: Generation -> Evaluation -> Refinement."""
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from tqdm import tqdm

from .gen_model import batch_generate_summaries
from .ref_model import refine_summary
from .eva_model import evaluate_summary
from .utils import (
    validate_scores,
    get_total_score,
    save_to_jsonl,
    format_result_for_training,
    get_processed_images,
)


def pipeline1_build_dataset(
    image_folder: str,
    output_path: str,
    low_ratio: float = 0.3,
    medium_ratio: float = 0.3,
    high_ratio: float = 0.4,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: Optional[str] = None,
    lora_path_feature2: Optional[str] = None,
    lora_path_feature3: Optional[str] = None,
    max_retries: int = 3,
    resume: bool = True,
) -> Tuple[int, int]:
    """Build synthetic FigGER-style samples with the AgentGER loop.
    
    流程：
    1. GenModel: generate low/medium/high quality summaries.
    2. RefModel: evaluate and refine each generated summary.
    3. EvaModel: verify the improved summary.
    4. 验证不通过则重试（最多3次）
    5. 通过则保存，失败则丢弃
    
    Args:
        image_folder: 图片文件夹路径
        output_path: 输出 JSONL 文件路径
        low_ratio: 低质量比例
        medium_ratio: 中质量比例
        high_ratio: 高质量比例
        model_path: 模型路径
        lora_path: LoRA 权重路径（已废弃，请使用 lora_path_ref/eva）
        lora_path_feature2: RefModel LoRA 权重路径（兼容旧参数名）
        lora_path_feature3: EvaModel LoRA 权重路径（兼容旧参数名）
        max_retries: 最大重试次数
        resume: 是否从断点续传
        
    Returns:
        (成功数量, 总数量)
    """
    print("=" * 60)
    print("AgentGER: 构建数据集")
    print("=" * 60)
    
    # 创建输出目录
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # GenModel 的中间结果路径
    step1_output = output_path.replace(".jsonl", "_step1.jsonl")
    
    # 步骤1：GenModel - 批量生成摘要
    print("\n[步骤1] GenModel: 批量生成图表摘要...")
    summaries = batch_generate_summaries(
        image_folder=image_folder,
        low_ratio=low_ratio,
        medium_ratio=medium_ratio,
        high_ratio=high_ratio,
        model_path=model_path,
        lora_path=None,  # GenModel 不使用 LoRA
        output_path=step1_output,  # 保存中间结果
        resume=resume,
    )
    
    if not summaries:
        print("错误：没有生成任何总结")
        return 0, 0
    
    # 检查已完成的图片（步骤2-3的断点续传）
    processed_images = set()
    if resume:
        processed_images = get_processed_images(output_path)
        if processed_images:
            print(f"\n发现 {len(processed_images)} 条已完成的最终结果，将跳过这些图片")
    
    # 过滤待处理的项目
    pending_summaries = [
        item for item in summaries 
        if item["image_path"] not in processed_images
    ]
    
    total_count = len(summaries)
    already_done = len(processed_images)
    
    if not pending_summaries:
        print("所有图片已处理完成")
        return already_done, total_count
        
    print(f"\n[步骤2-3] RefModel 改进 + EvaModel 验证...")
    print(f"待处理: {len(pending_summaries)} 张 | 已完成: {already_done} 张 | 总计: {total_count} 张")
    
    success_count = already_done
    fail_count = 0
    
    # 带进度条处理
    pbar = tqdm(
        pending_summaries,
        desc="评估验证中",
        unit="张",
        ncols=100,
    )
    
    for item in pbar:
        image_path = item["image_path"]
        original_summary = item["summary"]
        quality_level = item["quality_level"]
        
        # 重试逻辑
        temperatures = [0.7, 0.8, 0.9]
        passed = False
        
        for retry in range(max_retries):
            temp = temperatures[retry] if retry < len(temperatures) else 0.7 + 0.1 * retry
            
            # 步骤2：RefModel - 评价引导改进
            result2 = refine_summary(
                image_path=image_path,
                summary=original_summary,
                model_path=model_path,
                lora_path=lora_path_feature2 or lora_path,
                temperature=temp,
                top_p=0.9,
                do_sample=True,
            )
            
            if result2 is None:
                continue
                
            improved_summary = result2.get("improved_summary", "")
            if not improved_summary:
                continue
                
            # 步骤3：EvaModel - 验证改进后的摘要
            result3 = evaluate_summary(
                image_path=image_path,
                summary=improved_summary,
                model_path=model_path,
                lora_path=lora_path_feature3 or lora_path,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
            )
            
            if result3 is None:
                continue
                
            # 验证分数
            is_valid, total_score, reason = validate_scores(result3)
            
            if is_valid:
                # 保存结果
                training_data = format_result_for_training(
                    image_path=image_path,
                    original_summary=original_summary,
                    result=result2,
                    include_improved_summary=True,
                )
                training_data["quality_level"] = quality_level
                training_data["validation_scores"] = result3.get("scores", {})
                
                save_to_jsonl(training_data, output_path)
                success_count += 1
                passed = True
                break
                
        if not passed:
            fail_count += 1
            
        # 更新进度条
        pbar.set_postfix({
            "成功": success_count,
            "失败": fail_count,
            "通过率": f"{success_count/(success_count+fail_count)*100:.1f}%" if (success_count+fail_count) > 0 else "N/A",
        })
    
    pbar.close()
    
    print("\n" + "=" * 60)
    print(f"AgentGER 数据构建完成:")
    print(f"  - 成功: {success_count}")
    print(f"  - 失败: {fail_count}")
    print(f"  - 总计: {total_count}")
    print(f"  - 通过率: {success_count/total_count*100:.1f}%")
    print(f"输出文件: {output_path}")
    print("=" * 60)
    
    return success_count, total_count


def pipeline2_user_optimize(
    image_path: str,
    summary: str,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: Optional[str] = None,
    ref_lora_path: Optional[str] = None,
    eva_lora_path: Optional[str] = None,
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Refine a user-provided summary with RefModel and verify with EvaModel.
    
    流程：
    1. RefModel: evaluate and generate an improved summary.
    2. EvaModel: verify the improved summary.
    3. 验证不通过则重试（最多3次）
    4. 3次均不通过则选择总分最高的结果
    
    Args:
        image_path: 图片路径
        summary: 用户提供的原始总结
        model_path: 模型路径
        lora_path: 兼容旧命令的 LoRA 权重路径
        ref_lora_path: RefModel LoRA 权重路径
        eva_lora_path: EvaModel LoRA 权重路径
        max_retries: 最大重试次数
        
    Returns:
        最终结果（包含 scores, reasons, improved_summary）
    """
    print("=" * 60)
    print("AgentGER: 用户摘要优化")
    print("=" * 60)
    
    temperatures = [0.7, 0.8, 0.9]
    all_results = []  # 保存所有尝试的结果和分数
    
    pbar = tqdm(range(max_retries), desc="优化尝试", unit="次", ncols=100)
    
    for retry in pbar:
        temp = temperatures[retry] if retry < len(temperatures) else 0.7 + 0.1 * retry
        pbar.set_postfix({"temperature": f"{temp:.2f}"})
        
        # 步骤1：RefModel - 评价引导改进
        result2 = refine_summary(
            image_path=image_path,
            summary=summary,
            model_path=model_path,
            lora_path=ref_lora_path or lora_path,
            temperature=temp,
            top_p=0.9,
            do_sample=True,
        )
        
        if result2 is None:
            tqdm.write(f"  尝试 {retry+1}: RefModel 失败")
            continue
            
        improved_summary = result2.get("improved_summary", "")
        if not improved_summary:
            tqdm.write(f"  尝试 {retry+1}: 未生成 improved_summary")
            continue
            
        # 步骤2：EvaModel - 验证改进后的摘要
        result3 = evaluate_summary(
            image_path=image_path,
            summary=improved_summary,
            model_path=model_path,
            lora_path=eva_lora_path or lora_path,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
        
        if result3 is None:
            tqdm.write(f"  尝试 {retry+1}: EvaModel 失败")
            all_results.append((result2, 0))
            continue
            
        # 验证分数
        is_valid, total_score, reason = validate_scores(result3)
        all_results.append((result2, total_score))
        
        if is_valid:
            pbar.close()
            print(f"\n验证通过！总分: {total_score}")
            print("\n" + "=" * 60)
            print("用户摘要优化完成")
            print("=" * 60)
            return result2
        else:
            tqdm.write(f"  尝试 {retry+1}: 验证失败 - {reason} (总分: {total_score})")
    
    pbar.close()
            
    # 所有尝试均未通过，选择总分最高的结果
    if all_results:
        best_result, best_score = max(all_results, key=lambda x: x[1])
        print(f"\n所有尝试均未通过验证，选择总分最高的结果 (分数: {best_score})")
        print("\n" + "=" * 60)
        print("用户摘要优化完成（选择最佳结果）")
        print("=" * 60)
        return best_result
    else:
        print("\n所有尝试均失败")
        print("\n" + "=" * 60)
        print("用户摘要优化失败")
        print("=" * 60)
        return None


def pipeline3_direct_score(
    image_path: str,
    summary: str,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    lora_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Direct EvaModel scoring.
    
    流程：
    1. EvaModel: output five-dimensional scores and reasoning chains.
    
    Args:
        image_path: 图片路径
        summary: 用户提供的总结
        model_path: 模型路径
        lora_path: LoRA 权重路径
        
    Returns:
        评分结果（包含 scores, reasons）
    """
    print("=" * 60)
    print("AgentGER: EvaModel 直接评价")
    print("=" * 60)
    
    result = evaluate_summary(
        image_path=image_path,
        summary=summary,
        model_path=model_path,
        lora_path=lora_path,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
    )
    
    if result is not None:
        total_score = get_total_score(result)
        print(f"\n评分完成，总分: {total_score}")
        print(f"各维度分数: {result.get('scores', {})}")
    else:
        print("\n评分失败")
        
    print("\n" + "=" * 60)
    print("EvaModel 直接评价完成")
    print("=" * 60)
    
    return result
