# AgentGER Frontend Demo Video Script

This script is designed for a 90-120 second screen-recorded demo of the current AgentGER web frontend. It focuses on what a reviewer or portfolio viewer should understand quickly: the project goal, the web workflow, mock-mode local execution, and how the same UI can connect to server-side local model inference.

## Recording Setup

Start the local demo from the repository root:

```bash
./start_frontend_demo.sh
```

Open:

```text
http://127.0.0.1:3000
```

The launcher starts both services:

- Frontend: Vite + React at `http://127.0.0.1:3000`
- Backend: FastAPI at `http://127.0.0.1:8000`
- Inference mode: `mock` by default, so local Mac demos do not load or download the large vision-language model.

Prepare one chart image and one short imperfect summary before recording. Example narration input:

```text
Revenue fluctuates across the chart but ends higher than it started, with the strongest rise near the final period.
```

## Shot List

### 1. Opening: Project And Interface

**Visual action**

- Show the browser at `http://127.0.0.1:3000`.
- Keep the full page visible: left sidebar, orange New Analysis button, workflow stepper, upload card, and evaluation setup card.

**Narration**

AgentGER is a multimodal figure-summary evaluation and refinement system. The web interface exposes the paper pipeline in a reviewer-friendly workflow: upload a figure, provide an existing summary, evaluate it across five dimensions, and optionally refine the summary using evaluation feedback.

### 2. Local Demo Mode

**Visual action**

- Briefly show the terminal where `./start_frontend_demo.sh` is running.
- Point out the line showing `推理模式: mock`.

**Narration**

For local frontend demonstration, the app runs in mock inference mode. This keeps the Mac demo lightweight and avoids downloading or loading the large Qwen3-VL model. On a server with model weights available, the same backend can be switched to local inference mode.

### 3. Upload Figure

**Visual action**

- Return to the browser.
- Click the upload card and select a chart image, or drag the image into the upload area.
- Pause after the image preview appears.

**Narration**

The first step is figure parsing. The interface accepts common image formats and keeps uploaded files local under the ignored runtime upload directory. The image preview lets users verify that the correct chart is being evaluated.

### 4. Enter Summary And Choose Pipeline

**Visual action**

- Paste the prepared summary into the text area.
- Keep `RefModel 优化` selected.
- Briefly hover or click `EvaModel 评价` and then return to `RefModel 优化` if you want to show both modes.

**Narration**

The user provides a candidate figure summary. EvaModel mode returns direct five-dimensional evaluation, while RefModel mode performs evaluation-guided refinement and returns both scores and an improved summary.

### 5. Run Analysis

**Visual action**

- Click `开始分析`.
- Show the title changing to `Analyzing the figure...`.
- Show the stepper and running task cards.

**Narration**

When the analysis starts, the UI mirrors the project pipeline: figure parsing, summary evaluation, guided refinement, and report generation. In mock mode the result is generated quickly, while server-side local inference follows the same API contract.

### 6. Review Final Report

**Visual action**

- Wait for the completed report.
- Scroll through the score ring, dimension bars, reasons, and improved summary.

**Narration**

The final report follows AgentGER's paper-aligned scoring dimensions: Faithfulness, Completeness, Conciseness, Logicality, and Analysis. The interface shows the total score, dimension-level scores, reasoning text, and the RefModel improved summary.

### 7. History And Repeatability

**Visual action**

- Click the history item in the left sidebar.
- Show that the uploaded image, input summary, selected pipeline, and result reload into the workspace.
- Click `New Analysis` to clear the workspace.

**Narration**

Each run is saved to a local history database so reviewers can revisit previous analyses without rerunning the pipeline. The New Analysis button resets the workspace for another figure.

### 8. Server Deployment Note

**Visual action**

- End on the UI or briefly show the README section with server inference environment variables.

**Narration**

For deployment, place the base model and LoRA adapters on the server and set the backend to local inference mode. The frontend remains unchanged; only the backend inference mode and model paths need to be configured.

## Optional Closing Caption

```text
AgentGER Web Demo
Generation - Evaluation - Refinement for figure summaries
Local mock demo now; server-side local model inference ready.
```

## Commands To Mention In The Video Description

```bash
# Local frontend demo without loading large model weights
./start_frontend_demo.sh

# Server/local-model inference
AGENTGER_INFERENCE_MODE=local \
AGENTGER_MODEL_PATH=/path/to/Qwen3-VL-8B-Instruct \
AGENTGER_EVA_LORA_PATH=/path/to/eva_model \
AGENTGER_REF_LORA_PATH=/path/to/ref_model_distill \
./web/start.sh
```
