# Training Notes

This repository implements the two-stage training design described in the EMNLP AgentGER submission.

## Stage 1: EvaModel

EvaModel learns five-dimensional Chain-of-Evaluation scoring:

- Faithfulness
- Completeness
- Conciseness
- Logicality
- Analysis

Each dimension uses a discrete score from `{0, 1, 2}` and a dimension-specific reasoning chain.

```bash
python main.py train \
  --scheme eva \
  --data_path ./data/output/eva_training_data.json \
  --output_dir ./lora_weights/eva_model
```

## Stage 2: RefModel

RefModel performs evaluation-guided refinement. It predicts the same evaluation structure as EvaModel, then generates `improved_summary`.

The paper objective is:

```text
L_total = L_refine + beta * L_distill + gamma * L_replay
```

- `L_refine`: supervised refinement loss on improved summaries.
- `L_distill`: KL divergence from a frozen EvaModel teacher to preserve scoring behavior.
- `L_replay`: replay loss on evaluation samples to reduce forgetting.

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

## Data Conversion

Convert AgentGER JSONL records into Qwen3-VL chat-format training files:

```bash
python training/data_format.py \
  --input ./data/output/agentger_dataset.jsonl \
  --output-dir ./data/output \
  --generate-both
```

This generates:

```text
data/output/ref_training_data.json
data/output/eva_training_data.json
```

Large datasets, image folders, generated outputs, and LoRA adapters are intentionally ignored by git.
