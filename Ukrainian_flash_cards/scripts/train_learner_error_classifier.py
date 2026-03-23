import json
import os
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

MODEL_NAME = "xlm-roberta-base"
OUT_DIR = "models/learner_error_classifier"
DATA_FILE = "data/learner_errors.jsonl"

LABELS = ["correct", "grammar", "vocabulary", "translation", "pronunciation"]
label2id = {name: i for i, name in enumerate(LABELS)}
id2label = {i: name for name, i in label2id.items()}


def main():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"{DATA_FILE} not found. Create a JSONL dataset with fields: text, target, label."
        )

    ds = load_dataset("json", data_files=DATA_FILE)["train"]

    def normalize(example):
        text = example.get("text", "")
        target = example.get("target", "")
        label = example.get("label", "correct")
        return {
            "text": f"User: {text}\nTarget: {target}",
            "labels": label2id.get(label, 0),
        }

    ds = ds.map(normalize, remove_columns=ds.column_names)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tok(batch):
        return tokenizer(batch["text"], truncation=True, max_length=256)

    ds = ds.map(tok, batched=True)
    split = ds.train_test_split(test_size=0.15, seed=42)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABELS),
        label2id=label2id,
        id2label=id2label,
    )

    args = TrainingArguments(
        output_dir=OUT_DIR,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        logging_steps=20,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
    )

    trainer.train()
    trainer.save_model(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)

    print(f"Saved fine-tuned classifier to {OUT_DIR}")


if __name__ == "__main__":
    main()