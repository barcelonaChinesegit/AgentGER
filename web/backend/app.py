"""
FastAPI 后端服务 - 使用 subprocess 调用命令行
"""
import os
import sys
import uuid
import json
import subprocess
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path
import threading

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 配置日志 - 过滤掉 Cursor 的请求
class EndpointFilter(logging.Filter):
    def filter(self, record):
        return "/v1/chat/completions" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import (
    create_record,
    update_record,
    get_record,
    get_all_records,
    get_total_count,
)

# 配置
UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MODEL_PATH = str(PROJECT_ROOT / "Qwen3-VL-8B-Instruct")
EVA_LORA_PATH = str(PROJECT_ROOT / "lora_weights" / "eva_model")
REF_LORA_PATH = str(PROJECT_ROOT / "lora_weights" / "ref_model_distill")
MAIN_PY = str(PROJECT_ROOT / "main.py")

app = FastAPI(title="图表总结评估系统")

# 任务锁 - 确保同一时间只有一个任务在执行
task_lock = threading.Lock()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（上传的图片）
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


class RunRequest(BaseModel):
    image_path: str
    summary: str
    pipeline: str


class HistoryResponse(BaseModel):
    total: int
    items: list


def parse_json_result(output: str) -> Optional[dict]:
    """从命令行输出中解析 JSON 结果"""
    try:
        # 找到 "最终结果:" 或 "评分结果:" 后的 JSON
        lines = output.split('\n')
        json_started = False
        json_lines = []
        brace_count = 0
        
        for line in lines:
            if '最终结果:' in line or '评分结果:' in line:
                json_started = True
                continue
            
            if json_started:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0 and json_lines:
                    break
        
        if json_lines:
            json_str = '\n'.join(json_lines)
            return json.loads(json_str)
    except Exception as e:
        print(f"解析 JSON 失败: {e}", flush=True)
    
    return None


def calculate_total_score(result: dict) -> float:
    """计算总分"""
    scores = result.get('scores', {})
    return sum(score for score in scores.values() if isinstance(score, (int, float)))


def run_pipeline_subprocess(record_id: int, image_path: str, summary: str, pipeline: str):
    """
    使用 subprocess 运行 pipeline 命令
    """
    print(f"\n[任务排队] record_id={record_id}, pipeline={pipeline}", flush=True)
    
    with task_lock:
        print(f"\n{'='*60}", flush=True)
        print(f"[任务开始] record_id={record_id}, pipeline={pipeline}", flush=True)
        print(f"图片路径: {image_path}", flush=True)
        print(f"Summary: {summary[:80]}...", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        try:
            # 更新状态为处理中
            update_record(record_id, {}, 0, "processing")
            
            # 构建命令
            command = "optimize" if pipeline == "optimize" else "direct-score"
            
            cmd = [
                sys.executable,  # 使用当前 Python 解释器
                MAIN_PY,
                command,
                "--image", image_path,
                "--summary", summary,
            ]

            if pipeline == "optimize":
                cmd.extend([
                    "--ref_lora_path", REF_LORA_PATH,
                    "--eva_lora_path", EVA_LORA_PATH,
                ])
            else:
                cmd.extend(["--lora_path", EVA_LORA_PATH])
            
            print(f"[执行命令] {' '.join(cmd[:6])}...", flush=True)
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=600,  # 10分钟超时
            )
            
            print(f"\n[命令输出]\n{result.stdout}", flush=True)
            
            if result.stderr:
                print(f"\n[错误输出]\n{result.stderr}", flush=True)
            
            if result.returncode == 0:
                # 解析结果
                parsed = parse_json_result(result.stdout)
                if parsed:
                    total_score = calculate_total_score(parsed)
                    update_record(record_id, parsed, total_score, "completed")
                    print(f"\n[任务完成] record_id={record_id}, 总分={total_score}", flush=True)
                else:
                    update_record(record_id, {"error": "无法解析输出结果", "raw_output": result.stdout[-1000:]}, 0, "failed")
                    print(f"\n[任务失败] record_id={record_id}, 无法解析输出", flush=True)
            else:
                error_msg = result.stderr or result.stdout or "命令执行失败"
                update_record(record_id, {"error": error_msg[-500:]}, 0, "failed")
                print(f"\n[任务失败] record_id={record_id}, 返回码={result.returncode}", flush=True)
                
        except subprocess.TimeoutExpired:
            update_record(record_id, {"error": "任务执行超时 (>10分钟)"}, 0, "failed")
            print(f"\n[任务超时] record_id={record_id}", flush=True)
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"\n[任务异常] record_id={record_id}\n{error_msg}", flush=True)
            update_record(record_id, {"error": str(e)}, 0, "failed")


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """上传图片"""
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    print(f"[上传成功] {file.filename} -> {file_path}", flush=True)

    return {
        "success": True,
        "filename": unique_filename,
        "original_name": file.filename,
        "path": str(file_path),
        "url": f"/uploads/{unique_filename}",
    }


@app.post("/api/run")
async def run_pipeline(
    image_path: str = Form(...),
    summary: str = Form(...),
    pipeline: str = Form(...),
):
    """运行 pipeline"""
    print(f"\n[收到请求] /api/run", flush=True)
    print(f"  image_path: {image_path}", flush=True)
    print(f"  summary: {summary[:50]}...", flush=True)
    print(f"  pipeline: {pipeline}", flush=True)
    
    legacy_map = {"pipeline2": "optimize", "pipeline3": "direct-score"}
    pipeline = legacy_map.get(pipeline, pipeline)

    if pipeline not in ["optimize", "direct-score"]:
        raise HTTPException(status_code=400, detail="无效的 pipeline 选择")

    if not os.path.exists(image_path):
        raise HTTPException(status_code=400, detail=f"图片文件不存在: {image_path}")

    image_filename = Path(image_path).name
    record_id = create_record(
        image_path=image_path,
        image_filename=image_filename,
        summary=summary,
        pipeline=pipeline,
    )
    
    print(f"[记录创建] record_id={record_id}", flush=True)

    # 启动后台线程执行 subprocess
    thread = threading.Thread(
        target=run_pipeline_subprocess,
        args=(record_id, image_path, summary, pipeline),
        daemon=True,
        name=f"pipeline-{record_id}"
    )
    thread.start()
    
    print(f"[线程启动] {thread.name}", flush=True)

    return {
        "success": True,
        "record_id": record_id,
        "message": "任务已提交，正在处理中...",
    }


@app.get("/api/history")
async def get_history(limit: int = 50, offset: int = 0):
    """获取历史记录列表"""
    items = get_all_records(limit=limit, offset=offset)
    total = get_total_count()
    return {"total": total, "items": items}


@app.get("/api/history/{record_id}")
async def get_history_detail(record_id: int):
    """获取单条记录详情"""
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@app.get("/api/status/{record_id}")
async def get_task_status(record_id: int):
    """获取任务状态"""
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {
        "id": record["id"],
        "status": record["status"],
        "result": record.get("result"),
        "total_score": record.get("total_score"),
    }


@app.get("/api/image/{filename}")
async def get_image(filename: str):
    """获取上传的图片"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(file_path)


@app.on_event("startup")
async def cleanup_pending():
    """启动时清理卡住的记录"""
    from database import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE history SET status = 'failed' WHERE status IN ('pending', 'processing')")
        affected = cursor.rowcount
        conn.commit()
        if affected > 0:
            print(f"[清理] 将 {affected} 条未完成记录标记为 failed", flush=True)


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}", flush=True)
    print("图表总结评估系统 - 后端服务", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"模型路径: {MODEL_PATH}", flush=True)
    print(f"EvaModel LoRA: {EVA_LORA_PATH}", flush=True)
    print(f"RefModel LoRA: {REF_LORA_PATH}", flush=True)
    print(f"上传目录: {UPLOAD_DIR}", flush=True)
    print(f"主程序: {MAIN_PY}", flush=True)
    print(f"{'='*60}\n", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
