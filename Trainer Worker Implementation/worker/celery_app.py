import os
import shutil
import tarfile
from celery import Celery
from minio import Minio
from train_utils import run_training

# รับ Broker URL จาก Environment Variable
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL)

# เชื่อมต่อ MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

@celery_app.task(name="tasks.train_model_task")
def train_model_task(model_version: str):
    work_dir = f"/tmp/train_{model_version}"
    os.makedirs(work_dir, exist_ok=True)

    dataset_archive = os.path.join(work_dir, "dataset.tar.gz")
    dataset_extracted = os.path.join(work_dir, "dataset")
    output_model_dir = os.path.join(work_dir, "model_output")
    log_dir = os.path.join(work_dir, "logs")

    try:
        print(f"[{model_version}] Fetching dataset from MinIO...")
        minio_client.fget_object("datasets", "conll2003.tar.gz", dataset_archive)

        with tarfile.open(dataset_archive, "r:gz") as tar:
            tar.extractall(path=dataset_extracted)

        print(f"[{model_version}] Running training loop on GPU...")
        metrics = run_training(
            dataset_path=dataset_extracted,
            output_dir=output_model_dir,
            log_dir=log_dir
        )
        print(f"[{model_version}] Training finished: {metrics}")

        # บีบอัด Model & Logs ส่งกลับ MinIO
        tar_model_name = f"model_{model_version}.tar.gz"
        local_tar_path = os.path.join(work_dir, tar_model_name)
        
        with tarfile.open(local_tar_path, "w:gz") as tar:
            tar.add(output_model_dir, arcname="model")
            if os.path.exists(log_dir):
                tar.add(log_dir, arcname="logs")

        if not minio_client.bucket_exists("models"):
            minio_client.make_bucket("models")

        minio_client.fput_object("models", tar_model_name, local_tar_path)
        print(f"[{model_version}] Model successfully uploaded to MinIO.")

        return {"status": "SUCCESS", "version": model_version, "metrics": metrics}

    except Exception as e:
        print(f"[{model_version}] Training failed: {e}")
        raise e
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)