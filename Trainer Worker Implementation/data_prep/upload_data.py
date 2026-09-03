import os
import tarfile
from datasets import load_dataset
from minio import Minio

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadminpassword",
    secure=False
)

bucket_name = "datasets"
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)

print("Downloading dataset from Hugging Face...")
dataset = load_dataset("conll2003")
dataset.save_to_disk("./conll2003_data")

archive_name = "conll2003.tar.gz"
with tarfile.open(archive_name, "w:gz") as tar:
    tar.add("./conll2003_data", arcname="")

client.fput_object(bucket_name, archive_name, archive_name)
print("Uploaded dataset to MinIO successfully.")