# Data And Artifacts

Large local artifacts are intentionally excluded from this GitHub-ready repository.

## Expected Local Layout

```text
data/
├── images/                  # local figure images, ignored by git
├── output/                  # generated JSONL and metrics, ignored by git
└── README.md                # data format notes

lora_weights/
├── eva_model/               # EvaModel LoRA adapter, ignored by git
├── ref_model/               # RefModel LoRA adapter, ignored by git
└── ref_model_distill/       # RefModel trained with KD + ER, ignored by git
```

## Generated Summary Record

```json
{
  "image_path": "data/images/example.png",
  "quality_level": "medium",
  "summary": "Generated figure summary."
}
```

## Evaluation / Refinement Record

```json
{
  "image_path": "data/images/example.png",
  "original_summary": "Initial figure summary.",
  "output": {
    "scores": {
      "faithfulness": 2,
      "completeness": 1,
      "conciseness": 2,
      "logicality": 2,
      "analysis": 1
    },
    "reasons": {
      "faithfulness": "Reasoning grounded in the figure.",
      "completeness": "Reasoning grounded in the figure.",
      "conciseness": "Reasoning grounded in the figure.",
      "logicality": "Reasoning grounded in the figure.",
      "analysis": "Reasoning grounded in the figure."
    },
    "improved_summary": "Refined figure summary."
  },
  "quality_level": "medium",
  "validation_scores": {
    "faithfulness": 2,
    "completeness": 2,
    "conciseness": 2,
    "logicality": 2,
    "analysis": 2
  }
}
```

## Training Files

Use `training/data_format.py` to convert JSONL records into Qwen3-VL chat-format JSON.

```bash
python training/data_format.py \
  --input ./data/output/agentger_dataset.jsonl \
  --output-dir ./data/output \
  --generate-both
```

This produces:

```text
data/output/eva_training_data.json
data/output/ref_training_data.json
```

## Why Large Data Is Excluded

The local workspace previously contained thousands of images and generated outputs. They are useful for experiments but make a public repository harder to inspect. For a portfolio repository, the code structure, documentation, sample schema, and reproducible commands are more useful than uploading hundreds of megabytes of local artifacts.

Keep human-verified benchmark files and full image folders outside git unless they are explicitly anonymized and prepared for public release. If you later publish FigGER separately, link the dataset card from `README.md` instead of committing the raw images here.
