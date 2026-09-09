'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from celery import Celery

app = FastAPI()
celery_app = Celery("tasks", broker="redis://redis:6379/0")

class TrainRequest(BaseModel):
    model_version: str
    scheduled_time: datetime  # ISO 8601 string เช่น 2026-09-03T14:30:00Z

@app.post("/train")
def schedule_training(req: TrainRequest):
    now = datetime.now(timezone.utc)
    if req.scheduled_time < now:
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")

    # ส่งงานเข้าคิว พร้อมระบุ eta (เวลาที่จะเริ่มทำจริง)
    task = celery_app.send_task(
        "tasks.train_model_task",
        args=[req.model_version],
        eta=req.scheduled_time
    )

    return {
        "status": "queued",
        "task_id": task.id,
        "scheduled_for": req.scheduled_time
    }
'''

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from celery import Celery
from celery.result import AsyncResult
import os

app = FastAPI()

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

class TrainRequest(BaseModel):
    model_version: str
    scheduled_time: datetime

class PredictRequest(BaseModel):
    text: str

@app.post("/train")
def schedule_training(req: TrainRequest):
    now = datetime.now(timezone.utc)
    if req.scheduled_time < now:
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")

    task = celery_app.send_task(
        "tasks.train_model_task",
        args=[req.model_version],
        eta=req.scheduled_time,
        queue="celery"
    )

    return {
        "status": "queued",
        "task_id": task.id,
        "scheduled_for": req.scheduled_time
    }

@app.post("/predict")
def predict_ner(req: PredictRequest):
    # ส่งข้อความไปที่ inference_queue
    task = celery_app.send_task(
        "tasks.predict_ner_task",
        args=[req.text],
        queue="inference_queue"
    )
    
    # รอดึงผลลัพธ์ตอบกลับ (timeout 30 วินาที)
    try:
        result = task.get(timeout=30)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")