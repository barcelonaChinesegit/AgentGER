#!/usr/bin/env python3
"""
数据集分析脚本 - 统计数据质量、得分分布，并对图片进行分类

功能：
1. 统计 quality_level 分布
2. 统计 scores（原始摘要得分）各维度情况
3. 统计 validation_scores（改进摘要得分）各维度情况
4. 使用 Qwen3-VL 模型对图片进行分类
   - topic 模式：按主题分类（经济、医疗、教育等）
   - chart_type 模式：按图表类型分类（柱状图、折线图、饼图等）
5. 生成统计表格和饼状图
"""
import os
import sys
import json
import argparse
from collections import Counter, defaultdict
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
# 尝试设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'SimHei', 'DejaVu Sans']
except:
    pass
plt.rcParams['axes.unicode_minus'] = False

from tqdm import tqdm


# ============================================================
# 分类配置
# ============================================================

# 主题分类配置
TOPIC_CLASSIFY_PROMPT = """请观察这张图表，判断它属于哪个主题领域。只需要回答一个主题类别名称，从以下选项中选择：

- 经济金融（GDP、收入、市场、投资、股票等）
- 人口统计（人口数量、年龄分布、性别比例等）
- 就业劳动（就业率、失业率、劳动力、工资等）
- 教育培训（学校、学生、教育支出、入学率等）
- 医疗健康（疾病、医院、健康指标、疫情等）
- 科技互联网（互联网用户、科技公司、数字化等）
- 能源环境（能源消耗、碳排放、环保、气候等）
- 交通运输（汽车、航空、铁路、物流等）
- 房地产（房价、房屋销售、建筑面积等）
- 农业食品（农产品、粮食、食品价格等）
- 旅游休闲（游客数量、旅游收入、酒店等）
- 体育运动（比赛成绩、运动员、体育赛事等）
- 媒体娱乐（电影、音乐、游戏、社交媒体等）
- 政府公共（政府支出、税收、公共服务等）
- 贸易进出口（进出口额、贸易伙伴、关税等）
- 消费零售（消费支出、零售额、品牌市场份额等）
- 社会民生（犯罪率、社会保障、生活质量等）
- 其他

请只回答一个类别名称，不要其他内容。"""

TOPIC_CATEGORIES = {
    '经济金融': ['经济金融', '经济', '金融', 'GDP', '收入', '市场', '投资', '股票', '财务', '营收', '利润', '资产'],
    '人口统计': ['人口统计', '人口', '人口数量', '年龄', '性别', '出生率', '死亡率', '人口增长'],
    '就业劳动': ['就业劳动', '就业', '劳动', '失业', '劳动力', '工资', '薪资', '工作'],
    '教育培训': ['教育培训', '教育', '培训', '学校', '学生', '入学', '毕业', '高校', '大学'],
    '医疗健康': ['医疗健康', '医疗', '健康', '疾病', '医院', '疫情', '病例', '死亡', '感染', '疫苗'],
    '科技互联网': ['科技互联网', '科技', '互联网', '技术', '数字', '网络', '用户', '软件', '硬件', 'IT'],
    '能源环境': ['能源环境', '能源', '环境', '碳排放', '电力', '石油', '天然气', '可再生', '气候', '污染'],
    '交通运输': ['交通运输', '交通', '运输', '汽车', '航空', '铁路', '物流', '航运', '机场', '公路'],
    '房地产': ['房地产', '房价', '房屋', '住房', '建筑', '地产', '楼市', '租房'],
    '农业食品': ['农业食品', '农业', '食品', '粮食', '农产品', '畜牧', '渔业', '种植'],
    '旅游休闲': ['旅游休闲', '旅游', '休闲', '游客', '酒店', '景区', '度假'],
    '体育运动': ['体育运动', '体育', '运动', '比赛', '运动员', '赛事', '奥运', '世界杯', '足球', '篮球'],
    '媒体娱乐': ['媒体娱乐', '媒体', '娱乐', '电影', '音乐', '游戏', '社交媒体', '电视', '视频'],
    '政府公共': ['政府公共', '政府', '公共', '税收', '财政', '预算', '公共服务', '政策'],
    '贸易进出口': ['贸易进出口', '贸易', '进出口', '出口', '进口', '关税', '国际贸易'],
    '消费零售': ['消费零售', '消费', '零售', '购物', '品牌', '市场份额', '销售额', '电商'],
    '社会民生': ['社会民生', '社会', '民生', '犯罪', '安全', '社会保障', '福利', '生活'],
    '其他': ['其他', '未知', '未知类型', 'other', 'Other']
}

TOPIC_CN_TO_EN = {
    '经济金融': 'Economy & Finance',
    '人口统计': 'Demographics',
    '就业劳动': 'Employment & Labor',
    '教育培训': 'Education',
    '医疗健康': 'Healthcare',
    '科技互联网': 'Tech & Internet',
    '能源环境': 'Energy & Environment',
    '交通运输': 'Transportation',
    '房地产': 'Real Estate',
    '农业食品': 'Agriculture & Food',
    '旅游休闲': 'Tourism & Leisure',
    '体育运动': 'Sports',
    '媒体娱乐': 'Media & Entertainment',
    '政府公共': 'Government & Public',
    '贸易进出口': 'Trade & Import/Export',
    '消费零售': 'Consumer & Retail',
    '社会民生': 'Society & Livelihood',
    '其他': 'Others',
}

# 图表类型分类配置
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

# 图表类型分类映射 - 保持细分类型独立
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

CHART_TYPE_CN_TO_EN = {
    '垂直柱状图': 'Vertical Bar Chart',
    '水平条形图': 'Horizontal Bar Chart',
    '堆叠柱状图': 'Stacked Bar Chart',
    '分组柱状图': 'Grouped Bar Chart',
    '折线图': 'Line Chart',
    '多折线图': 'Multiple Line Chart',
    '面积图': 'Area Chart',
    '堆叠面积图': 'Stacked Area Chart',
    '饼图': 'Pie Chart',
    '环形图': 'Donut Chart',
    '散点图': 'Scatter Plot',
    '气泡图': 'Bubble Chart',
    '热力图': 'Heatmap',
    '雷达图': 'Radar Chart',
    '树状图': 'Treemap',
    '漏斗图': 'Funnel Chart',
    '瀑布图': 'Waterfall Chart',
    '组合图': 'Combo Chart',
    '地图': 'Map/Choropleth',
    '仪表盘': 'Gauge Chart',
    '桑基图': 'Sankey Diagram',
    '甘特图': 'Gantt Chart',
    '箱线图': 'Box Plot',
    '表格图': 'Table Chart',
    '其他': 'Others',
}


# ============================================================
# 数据加载和统计函数
# ============================================================

def load_dataset(jsonl_path: str) -> list:
    """加载 JSONL 数据集"""
    data = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def analyze_quality_levels(data: list) -> dict:
    """分析质量等级分布"""
    quality_counts = Counter()
    for item in data:
        quality = item.get('quality_level', 'unknown')
        quality_counts[quality] += 1
    
    total = len(data)
    quality_stats = {}
    for level in ['low', 'medium', 'high', 'unknown']:
        count = quality_counts.get(level, 0)
        percentage = (count / total * 100) if total > 0 else 0
        quality_stats[level] = {'count': count, 'percentage': percentage}
    
    return quality_stats


def analyze_scores(data: list, score_key: str = 'scores') -> dict:
    """
    分析得分情况
    
    Args:
        data: 数据列表
        score_key: 得分字段名 ('scores' 或 'validation_scores')
    
    Returns:
        各维度得分统计
    """
    dimensions = ['faithfulness', 'completeness', 'conciseness', 'logicality', 'analysis']
    score_stats = {dim: {'values': [], 'distribution': Counter()} for dim in dimensions}
    
    for item in data:
        # scores 字段在 output 内部
        if score_key == 'scores':
            scores = item.get('output', {}).get('scores', {})
        else:
            scores = item.get(score_key, {})
        
        for dim in dimensions:
            value = scores.get(dim)
            if value is not None:
                score_stats[dim]['values'].append(value)
                score_stats[dim]['distribution'][value] += 1
    
    # 计算统计量
    for dim in dimensions:
        values = score_stats[dim]['values']
        if values:
            score_stats[dim]['mean'] = sum(values) / len(values)
            score_stats[dim]['min'] = min(values)
            score_stats[dim]['max'] = max(values)
            score_stats[dim]['count'] = len(values)
        else:
            score_stats[dim]['mean'] = 0
            score_stats[dim]['min'] = 0
            score_stats[dim]['max'] = 0
            score_stats[dim]['count'] = 0
    
    return score_stats


def generate_stats_report(data: list, output_path: str = None) -> str:
    """生成统计报告"""
    total = len(data)
    
    # 1. 质量等级统计
    quality_stats = analyze_quality_levels(data)
    
    # 2. 原始摘要得分统计
    original_scores = analyze_scores(data, 'scores')
    
    # 3. 改进摘要得分统计
    improved_scores = analyze_scores(data, 'validation_scores')
    
    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("数据集统计报告")
    report_lines.append("=" * 80)
    report_lines.append(f"\n总样本数: {total}\n")
    
    # 质量等级表格
    report_lines.append("-" * 60)
    report_lines.append("1. 原始摘要质量等级分布 (quality_level)")
    report_lines.append("-" * 60)
    report_lines.append(f"{'等级':<15} {'数量':>10} {'占比':>15}")
    report_lines.append("-" * 60)
    for level in ['low', 'medium', 'high']:
        stats = quality_stats.get(level, {'count': 0, 'percentage': 0})
        report_lines.append(f"{level:<15} {stats['count']:>10} {stats['percentage']:>14.2f}%")
    report_lines.append("-" * 60)
    
    # 原始摘要得分表格
    report_lines.append("\n" + "-" * 80)
    report_lines.append("2. 原始摘要各维度得分统计 (scores)")
    report_lines.append("-" * 80)
    report_lines.append(f"{'维度':<20} {'均值':>10} {'最小值':>10} {'最大值':>10} {'样本数':>10}")
    report_lines.append("-" * 80)
    dimensions = ['faithfulness', 'completeness', 'conciseness', 'logicality', 'analysis']
    for dim in dimensions:
        stats = original_scores[dim]
        report_lines.append(
            f"{dim:<20} {stats['mean']:>10.3f} {stats['min']:>10} {stats['max']:>10} {stats['count']:>10}"
        )
    report_lines.append("-" * 80)
    
    # 原始摘要得分分布
    report_lines.append("\n原始摘要得分分布 (0/1/2 各有多少):")
    report_lines.append(f"{'维度':<20} {'得分0':>12} {'得分1':>12} {'得分2':>12}")
    report_lines.append("-" * 60)
    for dim in dimensions:
        dist = original_scores[dim]['distribution']
        report_lines.append(
            f"{dim:<20} {dist.get(0, 0):>12} {dist.get(1, 0):>12} {dist.get(2, 0):>12}"
        )
    report_lines.append("-" * 60)
    
    # 改进摘要得分表格
    report_lines.append("\n" + "-" * 80)
    report_lines.append("3. 改进摘要各维度得分统计 (validation_scores)")
    report_lines.append("-" * 80)
    report_lines.append(f"{'维度':<20} {'均值':>10} {'最小值':>10} {'最大值':>10} {'样本数':>10}")
    report_lines.append("-" * 80)
    for dim in dimensions:
        stats = improved_scores[dim]
        report_lines.append(
            f"{dim:<20} {stats['mean']:>10.3f} {stats['min']:>10} {stats['max']:>10} {stats['count']:>10}"
        )
    report_lines.append("-" * 80)
    
    # 改进摘要得分分布
    report_lines.append("\n改进摘要得分分布 (0/1/2 各有多少):")
    report_lines.append(f"{'维度':<20} {'得分0':>12} {'得分1':>12} {'得分2':>12}")
    report_lines.append("-" * 60)
    for dim in dimensions:
        dist = improved_scores[dim]['distribution']
        report_lines.append(
            f"{dim:<20} {dist.get(0, 0):>12} {dist.get(1, 0):>12} {dist.get(2, 0):>12}"
        )
    report_lines.append("-" * 60)
    
    # 对比表格
    report_lines.append("\n" + "-" * 80)
    report_lines.append("4. 原始摘要 vs 改进摘要 得分对比")
    report_lines.append("-" * 80)
    report_lines.append(f"{'维度':<20} {'原始均分':>12} {'改进均分':>12} {'提升':>12}")
    report_lines.append("-" * 80)
    for dim in dimensions:
        orig = original_scores[dim]['mean']
        impr = improved_scores[dim]['mean']
        diff = impr - orig
        report_lines.append(f"{dim:<20} {orig:>12.3f} {impr:>12.3f} {diff:>+12.3f}")
    report_lines.append("-" * 80)
    
    report = "\n".join(report_lines)
    
    # 保存报告
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"统计报告已保存到: {output_path}")
    
    return report


# ============================================================
# 图片分类函数
# ============================================================

def classify_images_with_model(
    data: list,
    model_path: str = "./Qwen3-VL-8B-Instruct",
    classify_mode: str = "topic",
    gpu_id: int = None,
) -> dict:
    """
    使用 Qwen3-VL 模型对图片进行分类
    
    Args:
        data: 数据列表
        model_path: 模型路径
        classify_mode: 分类模式 ('topic' 或 'chart_type')
        gpu_id: GPU 设备 ID
    
    Returns:
        分类结果 {category: [image_paths]}
    """
    from src.model_loader import Qwen3VLModel
    
    # 根据分类模式选择配置
    if classify_mode == "chart_type":
        classify_prompt = CHART_TYPE_CLASSIFY_PROMPT
        standard_categories = CHART_TYPE_CATEGORIES
        mode_desc = "图表类型"
    else:
        classify_prompt = TOPIC_CLASSIFY_PROMPT
        standard_categories = TOPIC_CATEGORIES
        mode_desc = "主题"
    
    # 初始化模型
    print(f"正在加载模型: {model_path}")
    model = Qwen3VLModel(model_path=model_path, device_id=gpu_id)
    model.load_model()
    
    # 收集所有图片路径
    image_paths = []
    for item in data:
        img_path = item.get('image_path', '')
        if img_path and os.path.exists(img_path):
            image_paths.append(img_path)
    
    print(f"共有 {len(image_paths)} 张图片需要分类")
    print(f"分类模式: {mode_desc}")
    
    # 第一阶段：对图片进行初步分类描述
    print(f"\n[阶段1] 对图片进行{mode_desc}分类...")
    initial_descriptions = []
    
    for img_path in tqdm(image_paths, desc=f"识别{mode_desc}"):
        try:
            response = model.generate(
                image_path=img_path,
                prompt=classify_prompt,
                max_new_tokens=50,
                temperature=0.3,
                do_sample=True,
            )
            # 清理响应
            response = response.strip().split('\n')[0].strip()
            initial_descriptions.append((img_path, response))
        except Exception as e:
            print(f"处理图片 {img_path} 时出错: {e}")
            initial_descriptions.append((img_path, "未知类型"))
    
    # 统计初步分类结果
    type_counter = Counter([desc for _, desc in initial_descriptions])
    print(f"\n初步{mode_desc}分类结果:")
    for t, c in type_counter.most_common():
        print(f"  {t}: {c}")
    
    # 第二阶段：整理为标准类别
    print(f"\n[阶段2] 整理为标准{mode_desc}类别...")
    
    def normalize_category(desc: str) -> str:
        """将描述归类到标准类别"""
        desc_lower = desc.lower()
        for category, keywords in standard_categories.items():
            for kw in keywords:
                if kw.lower() in desc_lower or desc_lower in kw.lower():
                    return category
        return '其他'
    
    # 归类到标准类别
    category_images = defaultdict(list)
    for img_path, desc in initial_descriptions:
        category = normalize_category(desc)
        category_images[category].append(img_path)
    
    # 保留所有识别出的类别（不合并小类别，以满足15+类型的要求）
    final_categories = dict(category_images)
    
    return final_categories


def plot_pie_chart(category_stats: dict, output_path: str, classify_mode: str = "topic"):
    """绘制饼状图"""
    # 根据分类模式选择中英文映射
    if classify_mode == "chart_type":
        cn_to_en = CHART_TYPE_CN_TO_EN
        title = "Chart Type Distribution"
    else:
        cn_to_en = TOPIC_CN_TO_EN
        title = "Image Topic Distribution"
    
    # 按数量排序
    sorted_items = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    labels_cn = [item[0] for item in sorted_items]
    labels_en = [cn_to_en.get(l, l) for l in labels_cn]
    sizes = [item[1] for item in sorted_items]
    total = sum(sizes)
    
    # 设置颜色
    colors = plt.cm.Set3(range(len(labels_en)))
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # 只显示占比大于3%的扇区标签
    threshold = 3
    
    def make_autopct(threshold):
        def autopct(pct):
            if pct > threshold:
                return f'{pct:.1f}%\n({int(pct/100*total)})'
            return ''
        return autopct
    
    # 绘制饼图 - 小扇区不显示外部标签
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=[l if s/total*100 > threshold else '' for l, s in zip(labels_en, sizes)],
        autopct=make_autopct(threshold),
        colors=colors,
        startangle=90,
        pctdistance=0.75,
        labeldistance=1.1,
        explode=[0.02] * len(sizes),
    )
    
    # 设置字体大小
    for text in texts:
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_fontsize(8)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=30)
    
    # 图例显示所有类别（包含数量和百分比）
    legend_labels = [f'{en}: {s} ({s/total*100:.1f}%)' for en, s in zip(labels_en, sizes)]
    ax.legend(
        wedges, 
        legend_labels,
        title="Categories",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9
    )
    
    plt.tight_layout()
    
    # 保存图表
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"饼状图已保存到: {output_path}")


def generate_category_report(category_images: dict, classify_mode: str = "topic") -> str:
    """生成图片分类统计报告"""
    total = sum(len(imgs) for imgs in category_images.values())
    
    if classify_mode == "chart_type":
        cn_to_en = CHART_TYPE_CN_TO_EN
        title = "图表类型分类统计"
    else:
        cn_to_en = TOPIC_CN_TO_EN
        title = "图片主题分类统计"
    
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append(title)
    lines.append("=" * 80)
    lines.append(f"\n总图片数: {total}")
    lines.append(f"类别数: {len(category_images)}\n")
    
    lines.append("-" * 80)
    lines.append(f"{'类别(中文)':<15} {'Category(English)':<25} {'数量':>8} {'占比':>10}")
    lines.append("-" * 80)
    
    # 按数量排序
    sorted_items = sorted(category_images.items(), key=lambda x: len(x[1]), reverse=True)
    for cat, imgs in sorted_items:
        count = len(imgs)
        pct = count / total * 100 if total > 0 else 0
        cat_en = cn_to_en.get(cat, cat)
        lines.append(f"{cat:<15} {cat_en:<25} {count:>8} {pct:>9.2f}%")
    
    lines.append("-" * 80)
    lines.append(f"{'总计':<15} {'Total':<25} {total:>8} {'100.00':>9}%")
    lines.append("-" * 80)
    
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="数据集分析工具")
    parser.add_argument(
        "--data_path",
        type=str,
        default="data/output/dataset.jsonl",
        help="数据集路径",
    )
    parser.add_argument(
        "--image_dir",
        type=str,
        default=None,
        help="直接指定图片目录（如果指定，则忽略 data_path，直接对目录中的图片进行分类）",
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
        "--skip_classification",
        action="store_true",
        help="跳过图片分类（仅统计得分）",
    )
    parser.add_argument(
        "--classify_mode",
        type=str,
        choices=["topic", "chart_type", "all"],
        default="topic",
        help="分类模式: topic=按主题分类, chart_type=按图表类型分类, all=两者都执行",
    )
    
    args = parser.parse_args()
    
    # 切换到项目根目录
    os.chdir(PROJECT_ROOT)
    
    # 检查是否直接使用图片目录模式
    if args.image_dir:
        # 直接处理图片目录模式
        image_dir = Path(args.image_dir)
        if not image_dir.exists():
            print(f"错误: 图片目录不存在: {args.image_dir}")
            return
        
        # 收集所有图片文件
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        image_files = [
            f for f in image_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        # 创建虚拟数据列表（只包含 image_path）
        data = [{'image_path': str(f)} for f in sorted(image_files)]
        print(f"从目录 {args.image_dir} 加载了 {len(data)} 张图片\n")
        
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 跳过统计报告（因为没有完整的数据集）
        report_path = os.path.join(args.output_dir, "analysis_report.txt")
        # 创建空的报告文件以便后续追加
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"图片目录分析报告\n来源目录: {args.image_dir}\n总图片数: {len(data)}\n")
    else:
        # 加载数据
        print(f"正在加载数据: {args.data_path}")
        data = load_dataset(args.data_path)
        print(f"共加载 {len(data)} 条数据\n")
        
        # 生成统计报告
        report_path = os.path.join(args.output_dir, "analysis_report.txt")
        report = generate_stats_report(data, report_path)
        print(report)
    
    # 图片分类
    if not args.skip_classification:
        # 确定要执行的分类模式
        if args.classify_mode == "all":
            modes_to_run = ["topic", "chart_type"]
        else:
            modes_to_run = [args.classify_mode]
        
        for mode in modes_to_run:
            print(f"\n{'='*60}")
            print(f"开始 {'主题' if mode == 'topic' else '图表类型'} 分类...")
            print(f"{'='*60}")
            
            category_images = classify_images_with_model(
                data=data,
                model_path=args.model_path,
                classify_mode=mode,
                gpu_id=args.gpu,
            )
            
            # 生成分类统计
            category_stats = {cat: len(imgs) for cat, imgs in category_images.items()}
            category_report = generate_category_report(category_images, mode)
            print(category_report)
            
            # 追加到报告文件
            with open(report_path, 'a', encoding='utf-8') as f:
                f.write(category_report)
            
            # 根据分类模式设置输出文件名
            if mode == "chart_type":
                pie_filename = "image_chart_type_pie.png"
                json_filename = "image_chart_types.json"
            else:
                pie_filename = "image_topic_pie.png"
                json_filename = "image_topics.json"
            
            # 绘制饼状图
            pie_path = os.path.join(args.output_dir, pie_filename)
            plot_pie_chart(category_stats, pie_path, mode)
            
            # 保存详细分类结果
            category_detail_path = os.path.join(args.output_dir, json_filename)
            with open(category_detail_path, 'w', encoding='utf-8') as f:
                json.dump(category_images, f, ensure_ascii=False, indent=2)
            print(f"\n分类详情已保存到: {category_detail_path}")
    
    print("\n分析完成！")


if __name__ == "__main__":
    main()
