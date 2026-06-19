#!/bin/bash
#
# 完整评估流程启动脚本
# 1. 模型推理（使用 RefModel KD/ER LoRA）
# 2. 计算评估指标
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 配置
INPUT_DATA="${INPUT_DATA:-./data/output/golden_test.jsonl}"
OUTPUT_MODEL="./data/output/dataset_model.jsonl"
EVAL_OUTPUT_DIR="./data/output/eval_results"
MODEL_PATH="./Qwen3-VL-8B-Instruct"
LORA_PATH="./lora_weights/ref_model_distill"

TMUX_SESSION="model_inference"

echo "============================================================"
echo "完整评估流程"
echo "============================================================"
echo ""
echo "项目路径: $PROJECT_ROOT"
echo "输入数据: $INPUT_DATA"
echo "模型输出: $OUTPUT_MODEL"
echo "LoRA 路径: $LORA_PATH"
echo ""
echo "============================================================"

# 检查是否已存在同名 tmux session
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "警告: tmux session '$TMUX_SESSION' 已存在"
    echo "请先运行: tmux kill-session -t $TMUX_SESSION"
    exit 1
fi

# 构建推理命令
INFERENCE_CMD="python scripts/run_model_inference.py \
    --input $INPUT_DATA \
    --output $OUTPUT_MODEL \
    --model_path $MODEL_PATH \
    --lora_path $LORA_PATH"

echo "创建 tmux session: $TMUX_SESSION"
echo "推理命令:"
echo "$INFERENCE_CMD"
echo ""

# 创建 tmux session 并启动
tmux new-session -d -s "$TMUX_SESSION" -c "$PROJECT_ROOT"
tmux send-keys -t "$TMUX_SESSION" "$INFERENCE_CMD" C-m

echo "============================================================"
echo "模型推理已在后台启动!"
echo ""
echo "查看进度:"
echo "  tmux attach -t $TMUX_SESSION"
echo ""
echo "推理完成后，可使用 scripts/eval_with_lora.py 或自定义评估脚本计算指标。"
echo "============================================================"
