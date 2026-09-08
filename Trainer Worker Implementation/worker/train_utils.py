import os
import glob
import evaluate
import numpy as np
import pyarrow as pa
import mlflow
import mlflow.transformers
from datasets import Dataset, DatasetDict, Features, Sequence, Value, ClassLabel
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer
)

seqeval = evaluate.load("seqeval")

def tokenize_and_align_labels(examples, tokenizer, label_all_tokens=False):
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            else:
                label_ids.append(label[word_idx] if label_all_tokens else -100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

def compute_metrics(p, label_list):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = seqeval.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

def run_training(dataset_path: str, output_dir: str, log_dir: str, model_version: str = "v1.0"):
    # 1. เชื่อมต่อ MLflow Tracking Server
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("NER_BERT_Training")

    # 2. โหลดข้อมูลจาก Arrow Files
    label_list = ['O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-MISC', 'I-MISC']
    features = Features({
        'tokens': Sequence(Value('string')),
        'ner_tags': Sequence(ClassLabel(names=label_list))
    })

    train_file = glob.glob(os.path.join(dataset_path, "train", "*.arrow"))[0]
    val_file = glob.glob(os.path.join(dataset_path, "validation", "*.arrow"))[0]

    with pa.memory_map(train_file, 'r') as source:
        train_dict = pa.ipc.open_stream(source).read_all().to_pydict()
    with pa.memory_map(val_file, 'r') as source:
        val_dict = pa.ipc.open_stream(source).read_all().to_pydict()

    raw_datasets = DatasetDict({
        "train": Dataset.from_dict({"tokens": train_dict["tokens"], "ner_tags": train_dict["ner_tags"]}, features=features),
        "validation": Dataset.from_dict({"tokens": val_dict["tokens"], "ner_tags": val_dict["ner_tags"]}, features=features)
    })
    
    # 3. โหลด Pretrained Tokenizer และ Model
    model_checkpoint = "bert-base-cased"
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    
    tokenized_datasets = raw_datasets.map(
        lambda x: tokenize_and_align_labels(x, tokenizer),
        batched=True,
        remove_columns=raw_datasets["train"].column_names
    )

    model = AutoModelForTokenClassification.from_pretrained(
        model_checkpoint,
        num_labels=len(label_list),
        id2label={i: l for i, l in enumerate(label_list)},
        label2id={l: i for i, l in enumerate(label_list)}
    )

    # 4. Hyperparameters (15 steps เพื่อความรวดเร็วและไม่เปลือง RAM)
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="no",
        save_strategy="no",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        max_steps=15,
        weight_decay=0.01,
        logging_dir=log_dir,
        logging_steps=5,
        fp16=False
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=lambda p: compute_metrics(p, label_list)
    )

    # 5. เริ่ม Track ด้วย MLflow
    with mlflow.start_run(run_name=f"Run_{model_version}"):
        mlflow.log_param("model_checkpoint", model_checkpoint)
        mlflow.log_param("learning_rate", 2e-5)
        mlflow.log_param("batch_size", 8)
        mlflow.log_param("max_steps", 15)

        train_result = trainer.train()

        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        metrics = train_result.metrics
        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)

        # Log Metrics เข้า MLflow
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)

        # บันทึก Model ลง MLflow พร้อม Register ในชื่อ "ner_bert_model"
        print(f"[{model_version}] Logging and registering model to MLflow...")
        mlflow.transformers.log_model(
            transformers_model={"model": model, "tokenizer": tokenizer},
            artifact_path="model",
            registered_model_name="ner_bert_model"
        )

    return metrics