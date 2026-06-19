# AgentGER

AgentGER is a multimodal Generation-Evaluation-Refinement framework for figure-to-text summarization. The project follows the EMNLP submission architecture in `2565_AgentGER_Toward_a_Human_A.pdf`: a GenModel generates quality-controlled figure summaries, an EvaModel performs five-dimensional Chain-of-Evaluation scoring, and a RefModel refines weak summaries while preserving evaluation consistency through knowledge distillation and experience replay.

## What This Repository Contains

This repository is organized for code review and graduate application portfolio use. It keeps the runnable research prototype, training scripts, evaluation utilities, and web demo structure, while large local data/model artifacts are excluded from version control.

```text
.
├── main.py                    # CLI entry point
├── src/
│   ├── gen_model.py           # GenModel: low/medium/high summary generation
│   ├── eva_model.py           # EvaModel: five-dimensional CoE evaluation
│   ├── ref_model.py           # RefModel: evaluation-guided refinement
│   ├── prompts.py             # Paper-aligned prompt templates
│   ├── pipeline.py            # AgentGER end-to-end pipeline
│   ├── model_loader.py        # Qwen3-VL + LoRA loading
│   └── utils.py               # JSON parsing, validation, JSONL helpers
├── training/
│   ├── data_format.py         # Convert JSONL into Qwen3-VL chat training data
│   ├── train_lora.py          # LoRA training for EvaModel / RefModel
│   ├── train_lora_distill.py  # RefModel KD + experience replay training
│   └── mixed_dataset.py       # Mixed evaluation/refinement dataset
├── scripts/                   # Evaluation, statistics, and batch utilities
├── web/                       # Optional FastAPI + React demo
└── docs/                      # Architecture and data notes
```

## Paper-Aligned Architecture

```text
Figure image
    |
    v
GenModel
    Generates low / medium / high quality initial summaries.
    |
    v
EvaModel
    Produces five-dimensional scores and reasoning chains:
    Faithfulness, Completeness, Conciseness, Logicality, Analysis.
    |
    v
RefModel
    Uses evaluation feedback to generate an improved summary.
    Training uses L_refine + beta * L_distill + gamma * L_replay.
```

The core output schema follows the EMNLP paper:

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
  "improved_summary": "Only returned by RefModel."
}
```

The paper does not require a learned weighted score field; this repo keeps the main pipeline aligned with five discrete scores plus reasoning chains.

## Installation

```bash
pip install -r requirements.txt
```

Model weights are not included. Place the base model and LoRA adapters locally:

```text
Qwen3-VL-8B-Instruct/
lora_weights/
├── eva_model/
├── ref_model/
└── ref_model_distill/
```

## CLI Usage

Generate low/medium/high quality summaries with GenModel:

```bash
python main.py generate \
  --image_folder ./data/images \
  --output ./outputs/generated_summaries.jsonl
```

Evaluate a summary with EvaModel:

```bash
python main.py evaluate \
  --image ./examples/example.png \
  --summary "A short figure summary." \
  --lora_path ./lora_weights/eva_model
```

Refine a summary with RefModel:

```bash
python main.py refine \
  --image ./examples/example.png \
  --summary "A short figure summary." \
  --lora_path ./lora_weights/ref_model_distill
```

Refine a user-provided summary and verify the improvement with EvaModel:

```bash
python main.py optimize \
  --image ./examples/example.png \
  --summary "A short figure summary." \
  --ref_lora_path ./lora_weights/ref_model_distill \
  --eva_lora_path ./lora_weights/eva_model
```

Run the AgentGER data-building loop:

```bash
python main.py build-dataset \
  --image_folder ./data/images \
  --output ./outputs/agentger_dataset.jsonl \
  --ref_lora_path ./lora_weights/ref_model_distill \
  --eva_lora_path ./lora_weights/eva_model
```

Legacy command aliases are still supported for older scripts:

```text
feature1 -> generate
feature2 -> refine
feature3 -> evaluate
pipeline1 -> build-dataset
pipeline2 -> optimize
pipeline3 -> direct-score
```

## Training

Stage 1 trains EvaModel on human-annotated evaluation data:

```bash
python main.py train \
  --scheme eva \
  --data_path ./data/output/eva_training_data.json \
  --output_dir ./lora_weights/eva_model
```

Stage 2 trains RefModel on evaluation-guided refinement data:

```bash
python main.py train \
  --scheme ref \
  --data_path ./data/output/ref_training_data.json \
  --output_dir ./lora_weights/ref_model
```

KD + experience replay training keeps RefModel aligned with the frozen EvaModel:

```bash
python training/train_lora_distill.py \
  --base_model_path ./Qwen3-VL-8B-Instruct \
  --teacher_lora_path ./lora_weights/eva_model \
  --score_data_path ./data/output/eva_training_data.json \
  --refine_data_path ./data/output/ref_training_data.json \
  --output_dir ./lora_weights/ref_model_distill \
  --distill_beta 0.5 \
  --replay_gamma 0.3
```

See `docs/TRAINING.md` for the paper-aligned loss decomposition and training-file flow.

## Data Policy

Large image folders, generated outputs, checkpoints, uploads, and runtime databases are excluded from GitHub. See `docs/DATA.md` for the expected data formats and directory placeholders.

The public repository should keep only code, docs, schemas, and lightweight placeholders. Full FigGER images, local verification subsets, generated scores, and LoRA adapters should stay local or be released through a separate dataset/model hosting channel.

## API Mode

The optional `api_pipeline/` path calls an external multimodal API. It never stores keys in code; set the key through the environment before use:

```bash
export ZHIZENGZENG_API_KEY="your-api-key"
```

## Notes

- The repository is structured around the EMNLP version of AgentGER.
- The codebase is not meant to rerun training automatically; it exposes the architecture, data formats, and runnable entry points.
- The web demo is optional and uses the same CLI backend commands.
