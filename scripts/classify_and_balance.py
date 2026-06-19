#!/usr/bin/env python3
"""
图片分类、平衡采样与重编号脚本

功能：
1. 使用 Qwen3-VL 模型对所有图片进行图表类型分类
2. 按照平衡采样策略精简到目标数量（单类别不超过34%）
3. 删除多余图片并重新编号
"""
import os
import sys
import json
import random
import shutil
import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tqdm import tqdm

# ============================================================
# 图表类型分类配置（复用 dataset_analysis.py）
# ============================================================

CHART_TYPE_CLASSIFY_PROMPT = """请观察这张图表，判断它的图表类型。只需要回答一个图表类型名称，从以下选项中选择：

- 垂直柱状图（垂直的柱形条，展示分类数据比较）
- 水平条形图（水平方向的条形，常用于排名展示）
- 堆叠柱状图（多个数据系列堆叠在一起的柱状图）
- 分组柱状图（多组柱子并排展示对比）
- 折线图（用线连接数据点，展示趋势变化）
- 多折线图（多条折线对比趋势）
- 面积图（折线图下方填充颜色，强调数量变化）
- 堆叠面积图（多个面积堆叠展示）
- 饼图（圆形分割展示各部分占比）
- 环形图（中间空心的饼图）
- 散点图（用点展示两个变量的关系）
- 气泡图（散点图的变体，点的大小表示第三个变量）
- 热力图（用颜色深浅表示数值大小的矩阵图）
- 雷达图（多维数据的蛛网状图）
- 树状图（用嵌套矩形展示层级数据）
- 漏斗图（展示流程各阶段转化率）
- 瀑布图（展示数值增减变化过程）
- 组合图（同时包含柱状图和折线图等多种类型）
- 地图（基于地理位置的数据可视化）
- 仪表盘（类似汽车仪表的进度指示图）
- 桑基图（展示流量和关系的流向图）
- 甘特图（项目时间进度图）
- 箱线图（展示数据分布的统计图）
- 表格图（以表格形式展示数据）
- 其他

请只回答一个图表类型名称，不要其他内容。"""

# 图表类型分类映射
CHART_TYPE_CATEGORIES = {
    '垂直柱状图': ['垂直柱状图', '柱状图', '柱形图', 'bar chart', 'bar', 'column', '垂直的柱形条'],
    '水平条形图': ['水平条形图', '水平柱状图', '横向条形图', 'horizontal bar', '条形图', '水平方向'],
    '堆叠柱状图': ['堆叠柱状图', '堆叠柱形图', '堆叠条形图', 'stacked bar', 'stacked column', '堆积柱状', '堆叠'],
    '分组柱状图': ['分组柱状图', '簇状柱状图', 'grouped bar', 'clustered', '并排'],
    '折线图': ['折线图', '线图', '曲线图', 'line chart', 'line', '趋势图', '走势图'],
    '多折线图': ['多折线图', '多线图', 'multiple line', '多条折线'],
    '面积图': ['面积图', 'area chart', 'area', '区域图'],
    '堆叠面积图': ['堆叠面积图', 'stacked area', '堆积面积'],
    '饼图': ['饼图', '圆饼图', 'pie chart', 'pie', '扇形图'],
    '环形图': ['环形图', '甜甜圈图', 'donut', 'doughnut', '圆环图'],
    '散点图': ['散点图', '点图', 'scatter', 'scatter plot', '离散点图'],
    '气泡图': ['气泡图', 'bubble', 'bubble chart', '气泡散点图'],
    '热力图': ['热力图', 'heatmap', 'heat map', '热图', '矩阵图', '色块图'],
    '雷达图': ['雷达图', 'radar', 'radar chart', '蜘蛛图', '蛛网图', '星形图'],
    '树状图': ['树状图', 'treemap', 'tree map', '矩形树图', '树图'],
    '漏斗图': ['漏斗图', 'funnel', 'funnel chart', '漏斗'],
    '瀑布图': ['瀑布图', 'waterfall', 'waterfall chart', '桥图'],
    '组合图': ['组合图', '混合图', '复合图', 'combo', 'combination', '双轴图', '多类型图'],
    '地图': ['地图', 'map', 'choropleth', '区域地图', '热力地图', '地理图'],
    '仪表盘': ['仪表盘', 'gauge', '仪表图', '刻度图', '进度表盘'],
    '桑基图': ['桑基图', 'sankey', '流量图', '流向图'],
    '甘特图': ['甘特图', 'gantt', '项目进度图', '时间线图'],
    '箱线图': ['箱线图', 'box plot', 'boxplot', '箱型图', '盒须图'],
    '表格图': ['表格图', '表格', 'table', '数据表'],
    '其他': ['其他', '未知', '未知类型', 'other', 'Others']
}


def normalize_category(desc: str) -> str:
    """将描述归类到标准类别"""
    desc_lower = desc.lower()
    for category, keywords in CHART_TYPE_CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in desc_lower or desc_lower in kw.lower():
                return category
    return '其他'


def get_all_images(image_dir: str) -> List[str]:
    """获取目录下所有图片文件"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    image_dir = Path(image_dir)
    images = []
    
    for f in image_dir.iterdir():
        if f.is_file() and f.suffix.lower() in image_extensions:
            images.append(str(f))
    
    return sorted(images)


def classify_images(
    image_paths: List[str],
    model_path: str = "./Qwen3-VL-8B-Instruct",
    gpu_id: int = None,
    cache_file: str = None,
) -> Dict[str, List[str]]:
    """
    使用 Qwen3-VL 模型对图片进行分类
    
    Args:
        image_paths: 图片路径列表
        model_path: 模型路径
        gpu_id: GPU 设备 ID
        cache_file: 分类结果缓存文件路径
    
    Returns:
        分类结果 {category: [image_paths]}
    """
    # 如果有缓存文件，直接加载
    if cache_file and os.path.exists(cache_file):
        print(f"从缓存文件加载分类结果: {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    from src.model_loader import Qwen3VLModel
    
    # 初始化模型
    print(f"正在加载模型: {model_path}")
    model = Qwen3VLModel(model_path=model_path, device_id=gpu_id)
    model.load_model()
    
    print(f"共有 {len(image_paths)} 张图片需要分类")
    
    # 对图片进行分类
    category_images = defaultdict(list)
    
    for img_path in tqdm(image_paths, desc="分类图片"):
        try:
            response = model.generate(
                image_path=img_path,
                prompt=CHART_TYPE_CLASSIFY_PROMPT,
                max_new_tokens=50,
                temperature=0.3,
                do_sample=True,
            )
            # 清理响应
            response = response.strip().split('\n')[0].strip()
            category = normalize_category(response)
            category_images[category].append(img_path)
        except Exception as e:
            print(f"处理图片 {img_path} 时出错: {e}")
            category_images['其他'].append(img_path)
    
    result = dict(category_images)
    
    # 保存缓存
    if cache_file:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"分类结果已保存到: {cache_file}")
    
    return result


def balance_sample(
    category_images: Dict[str, List[str]],
    target_total: int = 11000,
    max_ratio: float = 0.34,
    min_categories: int = 10,
    random_seed: int = 42,
) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """
    平衡采样，确保单类别不超过指定比例
    
    Args:
        category_images: 分类结果 {category: [image_paths]}
        target_total: 目标总数
        max_ratio: 单类别最大占比
        min_categories: 最少类别数
        random_seed: 随机种子
    
    Returns:
        (采样后的分类结果, 统计信息)
    """
    random.seed(random_seed)
    
    # 统计原始数据
    total_images = sum(len(imgs) for imgs in category_images.values())
    print(f"\n原始图片总数: {total_images}")
    print(f"原始类别数: {len(category_images)}")
    print(f"目标总数: {target_total}")
    print(f"单类别最大占比: {max_ratio * 100:.1f}%")
    
    # 计算单类别最大数量
    max_per_category = int(target_total * max_ratio)
    print(f"单类别最大数量: {max_per_category}")
    
    # 按数量排序
    sorted_categories = sorted(
        category_images.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    print("\n原始分布:")
    for cat, imgs in sorted_categories:
        pct = len(imgs) / total_images * 100
        print(f"  {cat}: {len(imgs)} ({pct:.1f}%)")
    
    # 第一轮：裁剪超过上限的类别
    sampled = {}
    remaining_quota = target_total
    
    for cat, imgs in sorted_categories:
        if len(imgs) > max_per_category:
            # 随机采样
            sampled[cat] = random.sample(imgs, max_per_category)
            remaining_quota -= max_per_category
        else:
            sampled[cat] = imgs.copy()
            remaining_quota -= len(imgs)
    
    current_total = sum(len(imgs) for imgs in sampled.values())
    print(f"\n第一轮裁剪后总数: {current_total}")
    
    # 如果总数超过目标，需要进一步裁剪（从大类别开始）
    if current_total > target_total:
        excess = current_total - target_total
        print(f"需要额外裁剪: {excess} 张")
        
        # 按当前数量排序
        sorted_sampled = sorted(
            sampled.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for cat, imgs in sorted_sampled:
            if excess <= 0:
                break
            # 可以裁剪的数量（保留至少1张）
            can_remove = min(excess, len(imgs) - 1)
            if can_remove > 0:
                sampled[cat] = random.sample(imgs, len(imgs) - can_remove)
                excess -= can_remove
    
    # 如果总数不足目标，从原始数据中补充
    current_total = sum(len(imgs) for imgs in sampled.values())
    if current_total < target_total:
        shortage = target_total - current_total
        print(f"需要补充: {shortage} 张")
        
        # 从尚未被选中的图片中补充
        for cat, imgs in sorted_categories:
            if shortage <= 0:
                break
            # 已选中的图片
            selected = set(sampled.get(cat, []))
            # 可以补充的图片
            available = [img for img in imgs if img not in selected]
            # 补充数量（不超过上限）
            current_count = len(sampled.get(cat, []))
            can_add = min(shortage, len(available), max_per_category - current_count)
            if can_add > 0:
                additional = random.sample(available, can_add)
                if cat in sampled:
                    sampled[cat].extend(additional)
                else:
                    sampled[cat] = additional
                shortage -= can_add
    
    # 过滤掉空类别
    sampled = {k: v for k, v in sampled.items() if v}
    
    # 统计最终结果
    final_total = sum(len(imgs) for imgs in sampled.values())
    stats = {
        'original_total': total_images,
        'original_categories': len(category_images),
        'sampled_total': final_total,
        'sampled_categories': len(sampled),
        'max_ratio_target': max_ratio,
    }
    
    print(f"\n最终采样结果:")
    print(f"总图片数: {final_total}")
    print(f"类别数: {len(sampled)}")
    
    sorted_sampled = sorted(
        sampled.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    for cat, imgs in sorted_sampled:
        pct = len(imgs) / final_total * 100
        status = "✓" if pct <= max_ratio * 100 else "✗"
        print(f"  {status} {cat}: {len(imgs)} ({pct:.1f}%)")
    
    # 检查约束
    if len(sampled) < min_categories:
        print(f"\n警告: 类别数 ({len(sampled)}) 少于目标 ({min_categories})")
    
    max_pct = max(len(imgs) / final_total for imgs in sampled.values())
    if max_pct > max_ratio:
        print(f"\n警告: 最大类别占比 ({max_pct*100:.1f}%) 超过目标 ({max_ratio*100:.1f}%)")
    
    return sampled, stats


def execute_cleanup_and_renumber(
    sampled_images: Dict[str, List[str]],
    image_dir: str,
    dry_run: bool = True,
    backup_dir: str = None,
) -> Dict[str, str]:
    """
    执行删除和重编号操作
    
    Args:
        sampled_images: 采样后的分类结果
        image_dir: 图片目录
        dry_run: 是否只预览不执行
        backup_dir: 备份目录（可选）
    
    Returns:
        重编号映射 {old_path: new_path}
    """
    image_dir = Path(image_dir)
    
    # 收集所有保留的图片
    kept_images = []
    for imgs in sampled_images.values():
        kept_images.extend(imgs)
    kept_set = set(kept_images)
    
    # 获取目录中所有图片
    all_images = get_all_images(str(image_dir))
    all_set = set(all_images)
    
    # 计算要删除的图片
    to_delete = all_set - kept_set
    
    print(f"\n执行清理和重编号:")
    print(f"  保留图片: {len(kept_set)}")
    print(f"  删除图片: {len(to_delete)}")
    
    if dry_run:
        print("\n[预览模式] 不会实际执行操作")
    
    # 备份（如果指定）
    if backup_dir and not dry_run:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        print(f"\n正在备份到: {backup_path}")
        for img in tqdm(to_delete, desc="备份删除的图片"):
            src = Path(img)
            dst = backup_path / src.name
            shutil.copy2(src, dst)
    
    # 删除图片
    if not dry_run:
        print("\n正在删除图片...")
        for img in tqdm(to_delete, desc="删除"):
            try:
                os.remove(img)
            except Exception as e:
                print(f"删除失败 {img}: {e}")
    
    # 重编号
    # 按类别分组，然后按原文件名排序
    kept_sorted = sorted(kept_images)
    
    rename_map = {}
    
    if not dry_run:
        # 先重命名为临时文件名（避免冲突）
        print("\n正在重编号...")
        temp_names = {}
        for i, old_path in enumerate(tqdm(kept_sorted, desc="临时重命名"), 1):
            old = Path(old_path)
            temp_name = old.parent / f"__temp_{i}__.png"
            if old.exists():
                os.rename(old, temp_name)
                temp_names[temp_name] = i
        
        # 再重命名为最终文件名
        for temp_path, num in tqdm(temp_names.items(), desc="最终重命名"):
            new_name = temp_path.parent / f"{num}.png"
            os.rename(temp_path, new_name)
            rename_map[str(kept_sorted[num-1])] = str(new_name)
    else:
        # 预览模式，只生成映射
        for i, old_path in enumerate(kept_sorted, 1):
            old = Path(old_path)
            new_name = old.parent / f"{i}.png"
            rename_map[old_path] = str(new_name)
    
    return rename_map


def save_final_classification(
    sampled_images: Dict[str, List[str]],
    rename_map: Dict[str, str],
    output_path: str,
):
    """保存最终分类结果（使用新文件名）"""
    final_classification = {}
    for cat, imgs in sampled_images.items():
        final_classification[cat] = [rename_map.get(img, img) for img in imgs]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_classification, f, ensure_ascii=False, indent=2)
    print(f"最终分类结果已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="图片分类、平衡采样与重编号工具")
    parser.add_argument(
        "--image_dir",
        type=str,
        default="data/images",
        help="图片目录",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/output",
        help="输出目录",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default="./Qwen3-VL-8B-Instruct",
        help="模型路径",
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=None,
        help="GPU ID",
    )
    parser.add_argument(
        "--target_total",
        type=int,
        default=11000,
        help="目标图片总数",
    )
    parser.add_argument(
        "--max_ratio",
        type=float,
        default=0.34,
        help="单类别最大占比",
    )
    parser.add_argument(
        "--min_categories",
        type=int,
        default=10,
        help="最少类别数",
    )
    parser.add_argument(
        "--random_seed",
        type=int,
        default=42,
        help="随机种子",
    )
    parser.add_argument(
        "--use_cache",
        action="store_true",
        help="使用缓存的分类结果（如果存在）",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="预览模式，不执行实际操作",
    )
    parser.add_argument(
        "--backup_dir",
        type=str,
        default=None,
        help="删除图片的备份目录",
    )
    parser.add_argument(
        "--skip_classification",
        action="store_true",
        help="跳过分类步骤（必须配合 --use_cache 使用）",
    )
    
    args = parser.parse_args()
    
    # 切换到项目根目录
    os.chdir(PROJECT_ROOT)
    
    # 缓存文件路径
    cache_file = os.path.join(args.output_dir, "all_image_chart_types.json")
    
    # 1. 获取所有图片
    print(f"正在扫描图片目录: {args.image_dir}")
    image_paths = get_all_images(args.image_dir)
    print(f"共发现 {len(image_paths)} 张图片")
    
    if len(image_paths) == 0:
        print("错误: 未找到任何图片")
        return
    
    # 2. 分类图片
    if args.skip_classification:
        if not os.path.exists(cache_file):
            print(f"错误: 缓存文件不存在 {cache_file}")
            print("请先运行分类或不使用 --skip_classification")
            return
        print(f"跳过分类，从缓存加载: {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            category_images = json.load(f)
    else:
        category_images = classify_images(
            image_paths=image_paths,
            model_path=args.model_path,
            gpu_id=args.gpu,
            cache_file=cache_file if args.use_cache else None,
        )
    
    # 3. 平衡采样
    sampled_images, stats = balance_sample(
        category_images=category_images,
        target_total=args.target_total,
        max_ratio=args.max_ratio,
        min_categories=args.min_categories,
        random_seed=args.random_seed,
    )
    
    # 4. 执行清理和重编号
    rename_map = execute_cleanup_and_renumber(
        sampled_images=sampled_images,
        image_dir=args.image_dir,
        dry_run=args.dry_run,
        backup_dir=args.backup_dir,
    )
    
    # 5. 保存最终分类结果
    final_output = os.path.join(args.output_dir, "balanced_chart_types.json")
    save_final_classification(sampled_images, rename_map, final_output)
    
    # 6. 保存统计信息
    stats_output = os.path.join(args.output_dir, "balance_stats.json")
    with open(stats_output, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"统计信息已保存到: {stats_output}")
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print("预览完成！使用 --dry_run=false 执行实际操作")
    else:
        print("操作完成！")
    print("=" * 60)
    
    # 提示验证命令
    print(f"\n验证命令:")
    print(f"python scripts/dataset_analysis.py --data_path {final_output} --classify_mode chart_type --gpu {args.gpu or 0}")


if __name__ == "__main__":
    main()

