from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from celery import Celery
import os

app = FastAPI()

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
# เพิ่ม backend เข้าไปด้วยเพื่อให้ FastAPI อ่านค่าผลลัพธ์กลับมาได้
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
    task = celery_app.send_task(
        "tasks.predict_ner_task",
        args=[req.text],
        queue="inference_queue"
    )
    
    try:
        result = task.get(timeout=30)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")