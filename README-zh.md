# AgentGER

[English](README.md) | 简体中文

AgentGER 是一个面向图表到文本摘要任务的多模态智能体框架。它遵循 Generation-Evaluation-Refinement 范式：生成模型先生成不同质量等级的图表摘要，评价模型以人类对齐的标准进行可解释评分，精修模型再根据评价反馈改进低质量摘要。

本仓库被整理为一个适合代码审阅、研究生申请作品集展示和后续复现的研究原型。论文版本见：[AgentGER_EMNLP_Submission.pdf](docs/paper/AgentGER_EMNLP_Submission.pdf)。

## 项目亮点

- **论文架构对齐**：将 GenModel、EvaModel、RefModel 拆分为清晰可读的独立模块。
- **人类对齐评价**：使用论文中的五个评价维度：Faithfulness、Completeness、Conciseness、Logicality、Analysis。
- **可解释 Chain-of-Evaluation**：输出每个维度的分数和 reasoning chain，而不是单一黑盒总分。
- **评价引导精修**：RefModel 根据 EvaModel 发现的弱项生成 improved summary。
- **训练流程完整**：包含 LoRA 微调、知识蒸馏和经验回放代码，用于在学习精修能力时保持评价能力。
- **适合 GitHub 展示**：大规模数据、生成结果、模型权重、上传文件和运行时数据库都已排除在版本控制之外。

## 方法概览

```text
Figure image
    |
    v
GenModel
    Generate low / medium / high quality candidate summaries.
    |
    v
EvaModel
    Score each summary with five-dimensional Chain-of-Evaluation.
    |
    v
RefModel
    Refine the summary with evaluation feedback.
```

核心输出格式如下：

```json
{
  "scores": {
    "faithfulness": 2,
    "completeness": 2,
    "conciseness": 1,
    "logicality": 2,
    "analysis": 2
  },
  "reasons": {
    "faithfulness": "Reasoning grounded in the figure.",
    "completeness": "Reasoning grounded in the figure.",
    "conciseness": "Reasoning grounded in the figure.",
    "logicality": "Reasoning grounded in the figure.",
    "analysis": "Reasoning grounded in the figure."
  },
  "improved_summary": "Returned by RefModel."
}
```

AgentGER 使用五个离散维度分数和 reasoning chains，不依赖额外的 learned weighted-score 字段。

## 仓库结构

```text
.
├── main.py                     # CLI 入口：生成、评价、精修、训练
├── src/                        # AgentGER 核心实现
│   ├── gen_model.py            # GenModel：质量可控摘要生成
│   ├── eva_model.py            # EvaModel：五维 Chain-of-Evaluation 评分
│   ├── ref_model.py            # RefModel：评价引导摘要精修
│   ├── pipeline.py             # AgentGER 端到端流程
│   ├── prompts.py              # 与论文对齐的 prompt 和评分维度
│   ├── model_loader.py         # Qwen3-VL 与 LoRA 加载工具
│   └── utils.py                # JSON 解析、分数验证、JSONL 工具
├── training/                   # 微调与蒸馏训练
│   ├── data_format.py          # 将 AgentGER JSONL 转换为 Qwen3-VL chat 格式
│   ├── train_lora.py           # EvaModel / RefModel 的 LoRA 训练
│   ├── train_lora_distill.py   # KD + experience replay 的 RefModel 训练
│   └── mixed_dataset.py        # 蒸馏训练使用的 score/refine 混合数据集
├── scripts/                    # 数据分析、评分和批量实验工具
├── api_pipeline/               # 可选：外部多模态 API 版本
├── web/                        # 可选：FastAPI + React 演示界面
├── start_frontend_demo.sh       # 本地 Web Demo 一键启动脚本
├── data/                       # 仅保留轻量占位；真实数据已 git-ignore
├── lora_weights/               # 本地 LoRA adapter 占位；权重已 git-ignore
└── docs/                       # 架构、数据、训练说明和论文 PDF
```

## 快速开始

安装依赖：

```bash
pip install -r requirements.txt
```

在本地放置基础模型和 LoRA 权重：

```text
Qwen3-VL-8B-Instruct/
lora_weights/
├── eva_model/
├── ref_model/
└── ref_model_distill/
```

将本地图表图片放入：

```text
data/images/
```

使用 EvaModel 评价摘要：

```bash
python main.py evaluate \
  --image ./data/images/example.png \
  --summary "A short figure summary." \
  --lora_path ./lora_weights/eva_model
```

使用 RefModel 精修摘要：

```bash
python main.py refine \
  --image ./data/images/example.png \
  --summary "A short figure summary." \
  --lora_path ./lora_weights/ref_model_distill
```

运行面向用户的完整精修流程：

```bash
python main.py optimize \
  --image ./data/images/example.png \
  --summary "A short figure summary." \
  --ref_lora_path ./lora_weights/ref_model_distill \
  --eva_lora_path ./lora_weights/eva_model
```

从图表文件夹构建 AgentGER 合成记录：

```bash
python main.py build-dataset \
  --image_folder ./data/images \
  --output ./data/output/agentger_dataset.jsonl \
  --ref_lora_path ./lora_weights/ref_model_distill \
  --eva_lora_path ./lora_weights/eva_model
```

## 训练流程

将 JSONL 记录转换为 Qwen3-VL chat-format 训练数据：

```bash
python training/data_format.py \
  --input ./data/output/agentger_dataset.jsonl \
  --output-dir ./data/output \
  --generate-both
```

训练 EvaModel：

```bash
python main.py train \
  --scheme eva \
  --data_path ./data/output/eva_training_data.json \
  --output_dir ./lora_weights/eva_model
```

训练 RefModel：

```bash
python main.py train \
  --scheme ref \
  --data_path ./data/output/ref_training_data.json \
  --output_dir ./lora_weights/ref_model
```

使用知识蒸馏和经验回放训练 RefModel：

```bash
python training/train_lora_distill.py \
  --base_model_path ./Qwen3-VL-8B-Instruct \
  --teacher_lora_path ./lora_weights/eva_model \
  --score_data_path ./data/output/eva_training_data.json \
  --refine_data_path ./data/output/ref_training_data.json \
  --output_dir ./lora_weights/ref_model_distill \
  --distill_beta 0.5 \
  --replay_gamma 0.3 \
  --temperature 2.0
```

更多训练细节见：[docs/TRAINING.md](docs/TRAINING.md)。

## 可选 API 模式

`api_pipeline/` 提供基于外部多模态 API 的 EvaModel 和 RefModel 实现。API key 不会写入代码：

```bash
export ZHIZENGZENG_API_KEY="your-api-key"
python api_pipeline/main.py direct-score \
  --image ./data/images/example.png \
  --summary "A short figure summary."
```

## 可选 Web Demo

Web demo 使用 FastAPI 后端和 React/Vite 前端封装 AgentGER 的评价与精修流程。当前界面被设计为轻量、适合展示的分析工作台：左侧项目栏、居中的 pipeline 进度条、上传卡片、处理方式选择、评分报告和本地历史记录。

如果只想在 Mac 本地展示前端效果，并且不加载大模型：

```bash
./start_frontend_demo.sh
```

然后打开：

```text
http://127.0.0.1:3000
```

该脚本会同时启动：

- 前端页面：`http://127.0.0.1:3000`
- 后端 API：`http://127.0.0.1:8000`
- 推理模式：默认 `mock`，因此本地演示不会下载或加载 Qwen3-VL 大模型。

按 `Ctrl+C` 可以同时停止前后端服务。

如果部署到服务器，并希望使用服务器本地模型推理：

```bash
AGENTGER_INFERENCE_MODE=local \
AGENTGER_MODEL_PATH=/path/to/Qwen3-VL-8B-Instruct \
AGENTGER_EVA_LORA_PATH=/path/to/eva_model \
AGENTGER_REF_LORA_PATH=/path/to/ref_model_distill \
./web/start.sh
```

此时前端不需要改动，仍然调用同一个 FastAPI 后端；后端会通过 `main.py` 使用服务器本地模型和 LoRA 权重。

演示界面产生的上传图片和历史记录只保存在本地，并已被 git 忽略。

## 展示视频脚本

当前前端的录屏脚本见：[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)。其中包含：

- 90-120 秒展示视频镜头清单；
- 推荐旁白；
- 本地 mock 模式解释；
- 上传、评价、精修、历史记录完整流程；
- 服务器部署时如何切换到本地模型推理。

## 旧版 Web 启动方式

也可以从 `web/` 目录启动服务：

```bash
cd web
bash start.sh
```

## 数据与模型策略

本仓库刻意保持轻量：

- 不提交完整图表图片。
- 不提交生成的 JSONL 输出和指标结果。
- 不提交 LoRA adapter 和基础模型权重。
- 不提交运行时上传文件和本地数据库。

数据格式和本地目录约定见：[docs/DATA.md](docs/DATA.md)。

## 推荐审阅入口

- [src/pipeline.py](src/pipeline.py)：AgentGER 端到端流程。
- [src/prompts.py](src/prompts.py)：评价维度和输出格式。
- [src/eva_model.py](src/eva_model.py)：Chain-of-Evaluation 评分。
- [src/ref_model.py](src/ref_model.py)：评价引导精修。
- [training/train_lora_distill.py](training/train_lora_distill.py)：知识蒸馏 + 经验回放训练。
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：简洁架构说明。

## 说明

本仓库是围绕 EMNLP AgentGER 投稿版本整理的研究原型，目标是让读者能快速理解模型架构、pipeline、训练策略和关键实现，而不被大型本地实验文件干扰。
