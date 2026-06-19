#!/bin/bash
#
# 知识蒸馏 LoRA 微调启动脚本
# 使用 tmux 在后台运行训练任务
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 训练配置
BASE_MODEL_PATH="./Qwen3-VL-8B-Instruct"
TEACHER_LORA_PATH="./lora_weights/eva_model"
SCORE_DATA_PATH="./data/output/eva_training_data.json"
REFINE_DATA_PATH="./data/output/ref_training_data.json"
OUTPUT_DIR="./lora_weights/ref_model_distill"

# LoRA 配置
LORA_R=64
LORA_ALPHA=128
LORA_DROPOUT=0.05

# 训练超参数
LEARNING_RATE=1e-4
NUM_EPOCHS=3
BATCH_SIZE=1
GRADIENT_ACCUMULATION_STEPS=8
MAX_PIXELS=$((1280 * 28 * 28))
SAVE_STEPS=100

# 蒸馏配置
DISTILL_BETA=0.5      # 蒸馏损失权重
REPLAY_GAMMA=0.3      # 经验回放损失权重
TEMPERATURE=2.0       # 蒸馏温度
SCORE_RATIO=0.3       # 打分数据比例

# GPU 配置（可选，设置使用的 GPU）
# export CUDA_VISIBLE_DEVICES=0,1

# tmux session 名称
TMUX_SESSION="distill_training"

# 构建训练命令
TRAIN_CMD="python training/train_lora_distill.py \
    --base_model_path $BASE_MODEL_PATH \
    --teacher_lora_path $TEACHER_LORA_PATH \
    --score_data_path $SCORE_DATA_PATH \
    --refine_data_path $REFINE_DATA_PATH \
    --output_dir $OUTPUT_DIR \
    --lora_r $LORA_R \
    --lora_alpha $LORA_ALPHA \
    --lora_dropout $LORA_DROPOUT \
    --learning_rate $LEARNING_RATE \
    --num_epochs $NUM_EPOCHS \
    --batch_size $BATCH_SIZE \
    --gradient_accumulation_steps $GRADIENT_ACCUMULATION_STEPS \
    --max_pixels $MAX_PIXELS \
    --save_steps $SAVE_STEPS \
    --distill_beta $DISTILL_BETA \
    --replay_gamma $REPLAY_GAMMA \
    --temperature $TEMPERATURE \
    --score_ratio $SCORE_RATIO"

# 可选：添加 Flash Attention 2
# TRAIN_CMD="$TRAIN_CMD --flash_attn"

# 可选：从现有 LoRA 继续训练
# TRAIN_CMD="$TRAIN_CMD --student_lora_path ./lora_weights/eva_model"

echo "============================================================"
echo "知识蒸馏 LoRA 微调"
echo "============================================================"
echo ""
echo "项目路径: $PROJECT_ROOT"
echo "教师模型: $TEACHER_LORA_PATH"
echo "输出目录: $OUTPUT_DIR"
echo ""
echo "蒸馏配置:"
echo "  - distill_beta: $DISTILL_BETA"
echo "  - replay_gamma: $REPLAY_GAMMA"
echo "  - temperature: $TEMPERATURE"
echo "  - score_ratio: $SCORE_RATIO"
echo ""
echo "============================================================"

# 检查是否已存在同名 tmux session
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "警告: tmux session '$TMUX_SESSION' 已存在"
    echo "请先运行: tmux kill-session -t $TMUX_SESSION"
    echo "或使用: tmux attach -t $TMUX_SESSION 查看现有训练"
    exit 1
fi

# 创建 tmux session 并启动训练
echo "创建 tmux session: $TMUX_SESSION"
echo "训练命令:"
echo "$TRAIN_CMD"
echo ""

tmux new-session -d -s "$TMUX_SESSION" -c "$PROJECT_ROOT"
tmux send-keys -t "$TMUX_SESSION" "$TRAIN_CMD" C-m

echo "============================================================"
echo "训练已在后台启动!"
echo ""
echo "查看训练进度:"
echo "  tmux attach -t $TMUX_SESSION"
echo ""
echo "后台运行时退出查看:"
echo "  按 Ctrl+B 然后按 D"
echo ""
echo "停止训练:"
echo "  tmux kill-session -t $TMUX_SESSION"
echo "============================================================"
