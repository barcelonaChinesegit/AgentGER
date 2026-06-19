# AgentGER Architecture

This document summarizes the repository architecture according to the EMNLP submission.

## Goal

AgentGER is not only a scoring model and not only a data-generation script. It is a closed-loop framework for figure-to-text summarization:

```text
Generation -> Evaluation -> Refinement
```

The framework uses a small amount of human-annotated seed data to train evaluation and refinement models, then uses the trained models to scale synthetic data construction and evaluate model alignment with human judgments.

## Model Roles

### GenModel

`src/gen_model.py`

GenModel generates initial figure summaries under quality-control instructions:

```text
q in {low, medium, high}
p_alpha(summary | figure, q)
```

It is model-agnostic and can use a base multimodal model such as Qwen3-VL-8B-Instruct.

### EvaModel

`src/eva_model.py`

EvaModel evaluates a figure-summary pair along five dimensions:

- Faithfulness
- Completeness
- Conciseness
- Logicality
- Analysis

It outputs discrete scores from `{0, 1, 2}` and a reasoning chain for each dimension. This corresponds to the paper's Chain-of-Evaluation mechanism.

### RefModel

`src/ref_model.py`

RefModel performs evaluation-guided refinement. It evaluates the original summary and generates an improved summary targeting weak dimensions while preserving correct content.

The paper trains RefModel with:

```text
L_total = L_refine + beta * L_distill + gamma * L_replay
```

- `L_refine`: learn to generate `improved_summary`
- `L_distill`: align RefModel/student token distributions with frozen EvaModel/teacher on evaluation outputs
- `L_replay`: continue training on evaluation data to reduce forgetting

## Dataset Flow

```text
1. Collect and filter figure images.
2. GenModel produces low/medium/high summaries.
3. Human annotators score 1,000 seed samples and refine them into golden summaries.
4. Train EvaModel on five-dimensional scores and reasoning chains.
5. Train RefModel on refinement targets, KD, and replay.
6. Use AgentGER to produce 10,000 synthetic candidates.
7. Select 1,000 candidates by stratified sampling for human verification and golden-test construction; the remaining 9,000 model-annotated samples form the synthetic training subset.
```

## Repository Entry Points

| Component | File |
| --- | --- |
| CLI | `main.py` |
| GenModel | `src/gen_model.py` |
| EvaModel | `src/eva_model.py` |
| RefModel | `src/ref_model.py` |
| End-to-end loop | `src/pipeline.py` |
| Prompt templates | `src/prompts.py` |
| LoRA training | `training/train_lora.py` |
| KD + ER training | `training/train_lora_distill.py` |
