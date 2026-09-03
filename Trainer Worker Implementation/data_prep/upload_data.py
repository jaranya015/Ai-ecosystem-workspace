import os
import tarfile
import pandas as pd
from datasets import Dataset, DatasetDict, Features, Sequence, Value, ClassLabel
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

print("Downloading dataset directly from Hugging Face Parquet storage...")

ner_feature = ClassLabel(
    names=['O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-MISC', 'I-MISC']
)
features = Features({
    'tokens': Sequence(Value('string')),
    'ner_tags': Sequence(ner_feature)
})

# ดึง Parquet files
train_df = pd.read_parquet("https://huggingface.co/datasets/conll2003/resolve/refs%2Fconvert%2Fparquet/conll2003/train/0000.parquet")
validation_df = pd.read_parquet("https://huggingface.co/datasets/conll2003/resolve/refs%2Fconvert%2Fparquet/conll2003/validation/0000.parquet")

# กรองเอาเฉพาะ 2 คอลัมน์ที่โมเดลต้องใช้
train_df = train_df[['tokens', 'ner_tags']]
validation_df = validation_df[['tokens', 'ner_tags']]

# แปลงเป็น DatasetDict
dataset_dict = DatasetDict({
    'train': Dataset.from_pandas(train_df, features=features, preserve_index=False),
    'validation': Dataset.from_pandas(validation_df, features=features, preserve_index=False)
})

output_dir = "./conll2003_data"
dataset_dict.save_to_disk(output_dir)

# บีบอัดและอัปโหลดขึ้น MinIO
archive_name = "conll2003.tar.gz"
with tarfile.open(archive_name, "w:gz") as tar:
    tar.add(output_dir, arcname="")

client.fput_object(bucket_name, archive_name, archive_name)
print("Uploaded dataset to MinIO successfully.")