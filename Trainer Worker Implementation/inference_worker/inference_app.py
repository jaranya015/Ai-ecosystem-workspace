import os
import torch
import mlflow
from celery import Celery
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("inference_tasks", broker=REDIS_URL, backend=REDIS_URL)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

print("Downloading model from MLflow Model Registry...")
# โหลด Model Artifact จาก MLflow Registry
model_local_path = mlflow.artifacts.download_artifacts(artifact_uri="models:/ner_bert_model/1")

print(f"Loading NER pipeline from local path: {model_local_path}")
tokenizer = AutoTokenizer.from_pretrained(model_local_path)
model = AutoModelForTokenClassification.from_pretrained(model_local_path)

# สร้าง Hugging Face Token Classification Pipeline
ner_pipeline = pipeline(
    "token-classification",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple"
)
print("Inference Worker is ready to process predictions!")

@celery_app.task(name="tasks.predict_ner_task")
def predict_ner_task(text: str):
    results = ner_pipeline(text)
    # แปลง float32 (numpy/torch) เป็น standard float สำหรับ JSON serialization
    clean_results = []
    for entity in results:
        clean_results.append({
            "entity_group": entity["entity_group"],
            "score": float(entity["score"]),
            "word": entity["word"],
            "start": int(entity["start"]),
            "end": int(entity["end"])
        })
    return {"text": text, "entities": clean_results}