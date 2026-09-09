import os
import torch

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

import mlflow
from celery import Celery
from transformers import AutoTokenizer, AutoModelForTokenClassification

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("inference_tasks", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_ignore_result=False,
    result_expires=3600,
)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

print("Downloading model from MLflow Model Registry...")
download_path = mlflow.artifacts.download_artifacts(artifact_uri="models:/ner_bert_model/1")

target_dir = download_path
for root, dirs, files in os.walk(download_path):
    if "config.json" in files:
        target_dir = root
        break

print(f"Loading NER model & tokenizer from: {target_dir}")
tokenizer = AutoTokenizer.from_pretrained(target_dir)
model = AutoModelForTokenClassification.from_pretrained(target_dir)

# Mapping มาตรฐานของ CoNLL-2003
label_list = ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-MISC", "I-MISC"]
model.config.id2label = {i: label for i, label in enumerate(label_list)}
model.config.label2id = {label: i for i, label in enumerate(label_list)}
model.eval()

print("Inference Worker is ready to process predictions!")

@celery_app.task(name="tasks.predict_ner_task")
def predict_ner_task(text: str):
    print(f"Processing inference for: {text}")
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits

        probabilities = torch.softmax(logits, dim=-1)
        predictions = torch.argmax(probabilities, dim=-1)[0].tolist()
        scores = torch.max(probabilities, dim=-1)[0][0].tolist()
        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        clean_results = []
        for token, pred_idx, score in zip(tokens, predictions, scores):
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            
            label = label_list[pred_idx] if pred_idx < len(label_list) else f"LABEL_{pred_idx}"
            # บันทึกเฉพาะ token ที่ไม่ได้ทำนายเป็น O (หรือถ้า O หมด ให้เก็บทุก token ที่มี score สูง)
            if label != "O":
                clean_results.append({
                    "entity_group": label.replace("B-", "").replace("I-", ""),
                    "score": round(float(score), 4),
                    "word": token,
                    "label": label
                })

        # Fallback กรณี 15 steps น้ำหนักยังเพี้ยนจนทาย O หมด: แสดง Token พร้อม Label สูงสุดออกมาให้เห็น
        if not clean_results:
            for token, pred_idx, score in zip(tokens, predictions, scores):
                if token not in ["[CLS]", "[SEP]", "[PAD]"]:
                    clean_results.append({
                        "entity_group": "TOKEN",
                        "score": round(float(score), 4),
                        "word": token,
                        "label": label_list[pred_idx] if pred_idx < len(label_list) else f"LABEL_{pred_idx}"
                    })

        print(f"Inference completed: {clean_results}")
        return {"text": text, "entities": clean_results}
    except Exception as e:
        print(f"Inference error: {e}")
        raise e