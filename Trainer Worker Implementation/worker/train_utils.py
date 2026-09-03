import os
import evaluate
import numpy as np
from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer
)

# โหลด metric seqeval สำหรับประเมินผล NER / Token classification
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
                # Special tokens เช่น [CLS], [SEP] ให้ใส่ -100 (PyTorch Loss จะเพิกเฉย)
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                # Token ตัวแรกของคำ ให้ใส่ label จริง
                label_ids.append(label[word_idx])
            else:
                # Token ย่อยที่ตามมา
                label_ids.append(label[word_idx] if label_all_tokens else -100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

def compute_metrics(p, label_list):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # ลบ -100 ออกก่อนคำนวณ Precision, Recall, F1
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

def run_training(dataset_path: str, output_dir: str, log_dir: str):
    # 1. โหลด Dataset ที่แตกไฟล์มาจาก MinIO
    raw_datasets = load_from_disk(dataset_path)
    label_list = raw_datasets["train"].features["ner_tags"].feature.names
    
    # 2. โหลด Pretrained Tokenizer และ Model
    model_checkpoint = "bert-base-cased"
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    
    # Map tokens และ align labels
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

    # 3. กำหนด Hyperparameters และการบันทึก Log
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=2,  # ปรับจำนวน epoch ตามเหมาะสม
        weight_decay=0.01,
        logging_dir=log_dir,
        logging_steps=10,
        save_total_limit=1,
        fp16=False  # เปิดใช้งาน GPU Mixed Precision เพื่อความเร็ว
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)

    # 4. เรียก Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=lambda p: compute_metrics(p, label_list)
    )

    # เริ่มเทรน (จะใช้ GPU อัตโนมัติหาก Container มองเห็น CUDA)
    train_result = trainer.train()

    # บันทึก Model, Tokenizer และ Log Metrics
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)

    return metrics