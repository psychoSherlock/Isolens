#!/usr/bin/env python3
"""
train_lstm.py - Train an LSTM model on Windows API call sequences for malware classification.

Based on the architecture from Laboratory 2 (AI and Cybersecurity, Politecnico di Torino).
Dataset: Sequential Windows API call traces (up to 100 calls) labeled as Malware (1) or Benign (0).
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence, pad_sequence
from torch.utils.data import DataLoader, Dataset


def set_seed(seed: int = 111):
    """Seed random generators for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


class SequenceDataset(Dataset):
    """PyTorch Dataset for variable-length API call sequences."""

    def __init__(self, sequences, labels):
        self.sequences = sequences
        self.labels = labels

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def collate_fn(batch):
    """
    Collate function to sort sequences by length (descending)
    and pad them for efficient packed RNN processing.
    """
    sequences, labels = zip(*batch)
    lengths = torch.tensor([len(seq) for seq in sequences], dtype=torch.long)

    sorted_indices = lengths.argsort(descending=True)
    sequences = [sequences[i] for i in sorted_indices]
    labels = torch.stack([labels[i] for i in sorted_indices])
    lengths = lengths[sorted_indices]

    padded_sequences = pad_sequence(sequences, batch_first=True, padding_value=0)
    return padded_sequences, lengths, labels


class LSTMClassifier(nn.Module):
    """
    2-Layer LSTM Classifier for API call sequence classification.

    Architecture:
      Embedding -> Dropout -> 2-layer LSTM -> Linear Head (Logits)
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 32,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 2,
        dropout: float = 0.2,
        padding_idx: int = 0,
    ):
        super().__init__()
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=padding_idx,
        )
        self.dropout = nn.Dropout(dropout)
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x, lengths):
        # x: (batch_size, max_seq_len)
        embedded = self.dropout(self.embedding(x))

        # Pack padded sequence for LSTM (lengths must be on CPU)
        packed_x = pack_padded_sequence(
            embedded, lengths.cpu(), batch_first=True, enforce_sorted=True
        )
        packed_out, (hidden, cell) = self.lstm(packed_x)

        # hidden[-1] is the final hidden state of the top LSTM layer
        logits = self.fc(hidden[-1])
        return logits


def load_and_preprocess_data(train_json_path: str, test_json_path: str, val_split: float = 0.3, seed: int = 42):
    """Load train/test JSONs, build vocabulary, and encode sequences."""
    print(f"[*] Loading training data from: {train_json_path}")
    df_train = pd.read_json(train_json_path)

    print(f"[*] Loading test data from: {test_json_path}")
    df_test = pd.read_json(test_json_path)

    print(f"    Raw train count: {len(df_train)}, test count: {len(df_test)}")

    # Split train into train / validation (stratified)
    X_train_val = df_train["api_call_sequence"].values
    y_train_val = df_train["is_malware"].values

    X_train_raw, X_val_raw, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=val_split,
        random_state=seed,
        stratify=y_train_val,
    )

    X_test_raw = df_test["api_call_sequence"].values
    y_test = df_test["is_malware"].values

    print(f"    Train split: {len(X_train_raw)} | Val split: {len(X_val_raw)} | Test: {len(X_test_raw)}")

    # Build vocabulary from training sequences only
    all_apis_train = [api for seq in X_train_raw for api in seq]
    unique_apis = sorted(list(set(all_apis_train)))

    api_to_id = {api: idx + 1 for idx, api in enumerate(unique_apis)}
    api_to_id["<PAD>"] = 0
    vocab_size = len(api_to_id)
    print(f"[*] Vocabulary size: {vocab_size} tokens (including <PAD>=0)")

    # Encode sequences to integer IDs
    def encode(sequences):
        return [
            torch.tensor([api_to_id.get(api, 0) for api in seq], dtype=torch.long)
            for seq in sequences
        ]

    X_train_tensors = encode(X_train_raw)
    y_train_tensor = torch.tensor(y_train, dtype=torch.long)

    X_val_tensors = encode(X_val_raw)
    y_val_tensor = torch.tensor(y_val, dtype=torch.long)

    X_test_tensors = encode(X_test_raw)
    y_test_tensor = torch.tensor(y_test, dtype=torch.long)

    return (
        X_train_tensors,
        y_train_tensor,
        X_val_tensors,
        y_val_tensor,
        X_test_tensors,
        y_test_tensor,
        api_to_id,
    )


def train_epoch(model, loader, criterion, optimizer, device):
    """Run one training epoch."""
    model.train()
    total_loss = 0.0
    total_samples = 0

    for batch_X, lengths, batch_y in loader:
        batch_X = batch_X.to(device)
        batch_y = batch_y.to(device)

        optimizer.zero_grad()
        outputs = model(batch_X, lengths)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

        batch_sz = batch_X.size(0)
        total_loss += loss.item() * batch_sz
        total_samples += batch_sz

    return total_loss / total_samples


def evaluate(model, loader, criterion, device):
    """Evaluate model on a dataset, returning average loss, accuracy, and macro F1."""
    model.eval()
    total_loss = 0.0
    total_samples = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch_X, lengths, batch_y in loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)

            outputs = model(batch_X, lengths)
            loss = criterion(outputs, batch_y)

            batch_sz = batch_X.size(0)
            total_loss += loss.item() * batch_sz
            total_samples += batch_sz

            preds = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.cpu().numpy())

    avg_loss = total_loss / total_samples
    acc = accuracy_score(all_targets, all_preds)
    f1 = f1_score(all_targets, all_preds, average="macro")
    return avg_loss, acc, f1, np.array(all_preds), np.array(all_targets)


def main():
    parser = argparse.ArgumentParser(description="Train an LSTM malware classifier on API sequences.")
    parser.add_argument(
        "--train_json",
        type=str,
        default="ai-implementation/Laboratory2/lab/data/jsons/train.json",
        help="Path to train.json",
    )
    parser.add_argument(
        "--test_json",
        type=str,
        default="ai-implementation/Laboratory2/lab/data/jsons/test.json",
        help="Path to test.json",
    )
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs (default: 25)")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size (default: 64)")
    parser.add_argument("--lr", type=float, default=1.5e-4, help="Learning rate (default: 1.5e-4)")
    parser.add_argument("--embedding_dim", type=int, default=32, help="Embedding dimension (default: 32)")
    parser.add_argument("--hidden_size", type=int, default=128, help="LSTM hidden state dimension (default: 128)")
    parser.add_argument("--num_layers", type=int, default=2, help="Number of LSTM layers (default: 2)")
    parser.add_argument("--dropout", type=float, default=0.2, help="Dropout probability (default: 0.2)")
    parser.add_argument("--seed", type=int, default=111, help="Random seed for reproducibility")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="ai-implementation/output",
        help="Directory to save model checkpoints and training logs",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to use ('cuda' or 'cpu')",
    )

    args = parser.parse_args()
    set_seed(args.seed)

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device(args.device)
    print("=" * 65)
    print(f" IsoLens - API Sequence Malware Classifier (LSTM)")
    print("=" * 65)
    print(f"Device:           {device}")
    if device.type == "cuda":
        print(f"GPU Name:         {torch.cuda.get_device_name(0)}")
        print(f"VRAM Available:   {torch.cuda.get_device_properties(0).total_memory / (1024**2):.0f} MiB")
    print(f"Batch Size:       {args.batch_size}")
    print(f"Epochs:           {args.epochs}")
    print(f"Learning Rate:    {args.lr}")
    print(f"Hidden Dim:       {args.hidden_size} (layers: {args.num_layers})")
    print(f"Embedding Dim:    {args.embedding_dim}")
    print("=" * 65)

    # 1. Load Data
    (
        X_train_tensors,
        y_train_tensor,
        X_val_tensors,
        y_val_tensor,
        X_test_tensors,
        y_test_tensor,
        api_to_id,
    ) = load_and_preprocess_data(args.train_json, args.test_json, val_split=0.3, seed=args.seed)

    # Save vocabulary
    vocab_file = output_path / "vocab.json"
    with open(vocab_file, "w") as f:
        json.dump(api_to_id, f, indent=2)
    print(f"[*] Vocabulary saved to: {vocab_file}")

    # 2. DataLoaders
    train_dataset = SequenceDataset(X_train_tensors, y_train_tensor)
    val_dataset = SequenceDataset(X_val_tensors, y_val_tensor)
    test_dataset = SequenceDataset(X_test_tensors, y_test_tensor)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,
    )

    # 3. Model Architecture
    model = LSTMClassifier(
        vocab_size=len(api_to_id),
        embedding_dim=args.embedding_dim,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        num_classes=2,
        dropout=args.dropout,
        padding_idx=0,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[*] LSTM initialized with {total_params:,} trainable parameters.")

    # 4. Loss & Optimizer (class weight [0.8, 0.2] to handle class imbalance as in Lab 2)
    weights = torch.tensor([0.8, 0.2], dtype=torch.float).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # 5. Training Loop
    history = {
        "epoch": [],
        "train_loss": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": [],
    }

    best_val_f1 = 0.0
    best_model_path = output_path / "best_lstm_model.pt"

    print("\n[*] Starting Training...")
    start_total = time.time()

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_f1, _, _ = evaluate(model, val_loader, criterion, device)
        elapsed = time.time() - t0

        history["epoch"].append(epoch)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_f1"].append(val_f1)

        is_best = val_f1 > best_val_f1
        if is_best:
            best_val_f1 = val_f1
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_f1": val_f1,
                    "vocab_size": len(api_to_id),
                    "args": vars(args),
                },
                best_model_path,
            )

        star = " ★ (Best)" if is_best else ""
        print(
            f"Epoch [{epoch:02d}/{args.epochs:02d}] "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc*100:.2f}% | "
            f"Val Macro F1: {val_f1:.4f} "
            f"({elapsed:.1f}s){star}"
        )

    total_time = time.time() - start_total
    print(f"\n[+] Training completed in {total_time:.1f}s. Best Val Macro F1: {best_val_f1:.4f}")
    print(f"[+] Best checkpoint saved to: {best_model_path}")

    # 6. Save Training History to CSV
    history_df = pd.DataFrame(history)
    history_csv = output_path / "training_history.csv"
    history_df.to_csv(history_csv, index=False)
    print(f"[*] Training history saved to: {history_csv}")

    # 7. Plot Curves
    try:
        sns.set_theme(style="whitegrid")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Loss curve
        axes[0].plot(history["epoch"], history["train_loss"], label="Train Loss", color="#1f77b4", lw=2)
        axes[0].plot(history["epoch"], history["val_loss"], label="Val Loss", color="#ff7f0e", lw=2)
        axes[0].set_title("Cross-Entropy Loss Across Epochs", fontsize=14)
        axes[0].set_xlabel("Epoch", fontsize=12)
        axes[0].set_ylabel("Loss", fontsize=12)
        axes[0].legend(fontsize=12)

        # F1 and Accuracy curve
        axes[1].plot(history["epoch"], history["val_f1"], label="Val Macro F1", color="#2ca02c", lw=2)
        axes[1].plot(history["epoch"], history["val_acc"], label="Val Accuracy", color="#d62728", lw=2, linestyle="--")
        axes[1].set_title("Validation Macro F1 & Accuracy", fontsize=14)
        axes[1].set_xlabel("Epoch", fontsize=12)
        axes[1].set_ylabel("Score", fontsize=12)
        axes[1].legend(fontsize=12)

        plt.tight_layout()
        plot_path = output_path / "training_curves.png"
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"[*] Training curve plot saved to: {plot_path}")
    except Exception as e:
        print(f"[!] Warning: Could not save plot: {e}")

    # 8. Final Test Set Evaluation
    print("\n" + "=" * 65)
    print(" Hold-Out Test Set Evaluation (Unseen Samples)")
    print("=" * 65)
    checkpoint = torch.load(best_model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_loss, test_acc, test_f1, test_preds, test_targets = evaluate(
        model, test_loader, criterion, device
    )

    print(f"Test Loss:     {test_loss:.4f}")
    print(f"Test Accuracy: {test_acc*100:.2f}%")
    print(f"Test Macro F1: {test_f1:.4f}")
    print("-" * 65)
    print("Classification Report:")
    print(
        classification_report(
            test_targets,
            test_preds,
            target_names=["Benign (0)", "Malware (1)"],
            digits=4,
        )
    )

    cm = confusion_matrix(test_targets, test_preds)
    print("Confusion Matrix:")
    print(f"  [[TN={cm[0,0]:5d}, FP={cm[0,1]:5d}]")
    print(f"   [FN={cm[1,0]:5d}, TP={cm[1,1]:5d}]]")
    print("=" * 65)


if __name__ == "__main__":
    main()
