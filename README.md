# AgentGER

English | [简体中文](README-zh.md)

AgentGER is a multimodal agent framework for figure-to-text summarization. It follows a Generation-Evaluation-Refinement paradigm: a generation model produces figure summaries at controlled quality levels, an evaluation model scores them with human-aligned reasoning, and a refinement model improves weak summaries using evaluation feedback.

This repository is organized as a clean research prototype for code review, portfolio presentation, and future reproduction of the EMNLP submission: [AgentGER_EMNLP_Submission.pdf](docs/paper/AgentGER_EMNLP_Submission.pdf).

## Highlights

- **Paper-aligned framework**: implements GenModel, EvaModel, and RefModel as separate, readable modules.
- **Human-aligned evaluation**: uses five dimensions from the paper: Faithfulness, Completeness, Conciseness, Logicality, and Analysis.
- **Interpretable Chain-of-Evaluation**: returns dimension-wise scores plus reasoning chains instead of a single opaque score.
- **Evaluation-guided refinement**: RefModel generates an improved summary based on weak dimensions identified during evaluation.
- **Training support**: includes LoRA fine-tuning, knowledge distillation, and experience replay code for preserving evaluation ability during refinement training.
- **Portfolio-friendly layout**: large datasets, generated outputs, model checkpoints, uploads, and runtime databases are excluded from git.

## Method Overview

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

The core output schema is:

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

AgentGER intentionally uses five discrete scores and reasoning chains. It does not rely on a learned weighted-score field.

## Repository Structure

```text
.
├── main.py                     # CLI entry point for generation, evaluation, refinement, and training
├── src/                        # Core AgentGER implementation
│   ├── gen_model.py            # GenModel: quality-controlled summary generation
│   ├── eva_model.py            # EvaModel: five-dimensional Chain-of-Evaluation scoring
│   ├── ref_model.py            # RefModel: evaluation-guided refinement
│   ├── pipeline.py             # End-to-end AgentGER loops
│   ├── prompts.py              # Paper-aligned prompt templates and scoring dimensions
│   ├── model_loader.py         # Qwen3-VL and LoRA loading utilities
│   └── utils.py                # JSON parsing, validation, JSONL helpers
├── training/                   # Fine-tuning and distillation
│   ├── data_format.py          # Convert AgentGER JSONL records to Qwen3-VL chat data
│   ├── train_lora.py           # LoRA training for EvaModel / RefModel
│   ├── train_lora_distill.py   # RefModel training with KD + experience replay
│   └── mixed_dataset.py        # Mixed score/refine dataset for distillation
├── scripts/                    # Dataset analysis, scoring, and batch experiment helpers
├── api_pipeline/               # Optional external multimodal API implementation
├── web/                        # Optional FastAPI + React demo
├── start_frontend_demo.sh       # One-command local web demo launcher
├── data/                       # Lightweight placeholders only; real data is git-ignored
├── lora_weights/               # Placeholder for local LoRA adapters; weights are git-ignored
└── docs/                       # Architecture, data, training notes, and paper PDF
```

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Download or place the base model and LoRA adapters locally:

```text
Qwen3-VL-8B-Instruct/
lora_weights/
├── eva_model/
├── ref_model/
└── ref_model_distill/
```

Put local figure images in:

```text
data/images/
```

Evaluate a summary with EvaModel:

```bash
python main.py evaluate \
  --image ./data/images/example.png \
  --summary "A short figure summary." \
  --lora_path ./lora_weights/eva_model
```

Refine a summary with RefModel:

```bash
python main.py refine \
  --image ./data/images/example.png \
  --summary "A short figure summary." \
  --lora_path ./lora_weights/ref_model_distill
```

Run the full user-facing refinement loop:

```bash
python main.py optimize \
  --image ./data/images/example.png \
  --summary "A short figure summary." \
  --ref_lora_path ./lora_weights/ref_model_distill \
  --eva_lora_path ./lora_weights/eva_model
```

Build synthetic AgentGER records from a folder of figures:

```bash
python main.py build-dataset \
  --image_folder ./data/images \
  --output ./data/output/agentger_dataset.jsonl \
  --ref_lora_path ./lora_weights/ref_model_distill \
  --eva_lora_path ./lora_weights/eva_model
```

## Training Pipeline

Convert JSONL records to Qwen3-VL chat-format data:

```bash
python training/data_format.py \
  --input ./data/output/agentger_dataset.jsonl \
  --output-dir ./data/output \
  --generate-both
```

Train EvaModel:

```bash
python main.py train \
  --scheme eva \
  --data_path ./data/output/eva_training_data.json \
  --output_dir ./lora_weights/eva_model
```

Train RefModel:

```bash
python main.py train \
  --scheme ref \
  --data_path ./data/output/ref_training_data.json \
  --output_dir ./lora_weights/ref_model
```

Train RefModel with knowledge distillation and experience replay:

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

More details are available in [docs/TRAINING.md](docs/TRAINING.md).

## Optional API Mode

`api_pipeline/` provides an API-backed version of EvaModel and RefModel. API keys are never stored in code:

```bash
export ZHIZENGZENG_API_KEY="your-api-key"
python api_pipeline/main.py direct-score \
  --image ./data/images/example.png \
  --summary "A short figure summary."
```

## Optional Web Demo

The web demo wraps the AgentGER evaluation/refinement workflow with a FastAPI backend and a React/Vite frontend. The current UI is designed as a light, reviewer-facing analysis workspace with a left project sidebar, centered pipeline progress, upload card, pipeline selector, score report, and local history.

For a Mac/local frontend demo without loading model weights:

```bash
./start_frontend_demo.sh
```

Then open:

```text
http://127.0.0.1:3000
```

The launcher starts:

- Frontend: `http://127.0.0.1:3000`
- Backend API: `http://127.0.0.1:8000`
- Inference mode: `mock` by default, so the local demo does not download or load the large Qwen3-VL model.
- Recording behavior: the current frontend is pinned to a fixed 2020-2024 growth-rate sample. Any uploaded image will display the same demo evaluation, reasons, weights, and improved summary. This is intentional for stable video recording and can be replaced when model inference is connected.

Stop both services with `Ctrl+C`.

For server-side local inference, place the base model and LoRA adapters on the server and run:

```bash
AGENTGER_INFERENCE_MODE=local \
AGENTGER_MODEL_PATH=/path/to/Qwen3-VL-8B-Instruct \
AGENTGER_EVA_LORA_PATH=/path/to/eva_model \
AGENTGER_REF_LORA_PATH=/path/to/ref_model_distill \
./web/start.sh
```

The same frontend will call the FastAPI backend, while the backend uses the server-local model through `main.py`.

The demo stores uploaded images and history locally. These runtime artifacts are ignored by git.

## Demo Video Script

Use [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) as a ready-to-record walkthrough for the current frontend. It includes:

- a 90-120 second shot list,
- suggested narration,
- local mock-mode explanation,
- upload / evaluation / refinement / history workflow,
- server deployment notes.

## Legacy Web Commands

You can still start the web services from inside `web/`:

```bash
cd web
bash start.sh
```

## Data And Model Policy

This repository is intentionally lightweight:

- Full figure images are not committed.
- Generated JSONL outputs and metrics are not committed.
- LoRA adapters and base model weights are not committed.
- Runtime uploads and local databases are not committed.

See [docs/DATA.md](docs/DATA.md) for expected record schemas and local directory conventions.

## Key Files For Reviewers

- [src/pipeline.py](src/pipeline.py): end-to-end AgentGER loops.
- [src/prompts.py](src/prompts.py): scoring dimensions and output schemas.
- [src/eva_model.py](src/eva_model.py): Chain-of-Evaluation scoring.
- [src/ref_model.py](src/ref_model.py): evaluation-guided refinement.
- [training/train_lora_distill.py](training/train_lora_distill.py): KD + experience replay training.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): compact architecture summary.

## Notes

This repository is a research prototype built around the EMNLP AgentGER submission. It is designed to make the model architecture, pipeline, training strategy, and implementation choices easy to inspect without uploading large private/local experiment artifacts.
