"""predict_lstm.py - LSTM Inference Engine for API Call Sequences.

Loads the trained IsoLens LSTM model and vocabulary, processes chronological
API sequences (directly or via the Procmon bridge), and outputs classification
verdicts with probability confidence scores.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


# ---------------------------------------------------------------------------
# Default Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DEFAULT_MODEL_PATH = BASE_DIR / "ai-implementation" / "synthetic-augmentation" / "output" / "best_lstm_model.pt"
DEFAULT_VOCAB_PATH = BASE_DIR / "ai-implementation" / "synthetic-augmentation" / "output" / "vocab.json"



# ---------------------------------------------------------------------------
# Model Architecture
# ---------------------------------------------------------------------------
class LSTMClassifier(nn.Module):
    """2-Layer LSTM Classifier for API call sequence classification."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 32,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 2,
        dropout: float = 0.0,
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

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        embedded = self.dropout(self.embedding(x))
        packed_x = pack_padded_sequence(
            embedded, lengths.cpu(), batch_first=True, enforce_sorted=True
        )
        packed_out, (hidden, cell) = self.lstm(packed_x)
        logits = self.fc(hidden[-1])
        return logits


class LSTMInferenceEngine:
    """Inference wrapper for loading checkpoints and predicting on sequences."""

    def __init__(
        self,
        model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
        vocab_path: Union[str, Path] = DEFAULT_VOCAB_PATH,
        device: Optional[str] = None,
    ):
        self.model_path = Path(model_path)
        self.vocab_path = Path(vocab_path)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        self.vocab: Dict[str, int] = {}
        self.model: Optional[LSTMClassifier] = None
        self._load()

    def _load(self) -> None:
        if not self.vocab_path.is_file():
            raise FileNotFoundError(f"Vocabulary file not found at: {self.vocab_path}")
        with open(self.vocab_path, "r", encoding="utf-8") as fh:
            self.vocab = json.load(fh)

        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model checkpoint not found at: {self.model_path}")
        checkpoint = torch.load(self.model_path, map_location=self.device)

        args = checkpoint.get("args", {})
        embedding_dim = args.get("embedding_dim", 32)
        hidden_size = args.get("hidden_size", 128)
        num_layers = args.get("num_layers", 2)

        self.model = LSTMClassifier(
            vocab_size=len(self.vocab),
            embedding_dim=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            num_classes=2,
            dropout=0.0,
        ).to(self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def predict_sequence(self, api_sequence: List[str]) -> Dict[str, Any]:
        """Classify a list of API call name strings."""
        if not api_sequence:
            return {
                "verdict": "UNKNOWN",
                "confidence": 0.0,
                "p_malware": 0.5,
                "p_benign": 0.5,
                "sequence_length": 0,
                "recognized_apis_count": 0,
            }

        # Tokenize: map API names to IDs (unknowns map to 0 / <PAD>)
        token_ids = [self.vocab.get(api, 0) for api in api_sequence]
        recognized = sum(1 for tid in token_ids if tid != 0)

        input_tensor = torch.tensor([token_ids], dtype=torch.long, device=self.device)
        lengths = torch.tensor([len(token_ids)], dtype=torch.long)

        with torch.no_grad():
            logits = self.model(input_tensor, lengths)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        p_benign = float(probs[0])
        p_malware = float(probs[1])
        verdict = "MALICIOUS" if p_malware >= p_benign else "BENIGN"
        confidence = float(max(p_malware, p_benign))

        return {
            "verdict": verdict,
            "confidence": round(confidence * 100, 2),
            "p_malware": round(p_malware, 4),
            "p_benign": round(p_benign, 4),
            "sequence_length": len(api_sequence),
            "recognized_apis_count": recognized,
            "recognized_ratio": round(recognized / len(api_sequence), 3) if api_sequence else 0.0,
        }

    def predict_procmon(
        self,
        source: Union[str, Dict[str, Any]],
        sample_proc: str = "",
        max_length: int = 100,
        filter_loader_noise: bool = True,
    ) -> Dict[str, Any]:
        """Classify a Procmon artifact (summary JSON or CSV)."""
        from core.modules.procmon_lstm_bridge import procmon_to_lstm_payload

        payload = procmon_to_lstm_payload(
            source,
            sample_proc=sample_proc,
            max_length=max_length,
            filter_loader_noise=filter_loader_noise,
        )
        result = self.predict_sequence(payload["api_call_sequence"])
        result["sample_process"] = payload.get("sample_process", "unknown")
        result["source_type"] = payload.get("source_type", "unknown")
        result["unique_apis"] = payload.get("unique_apis", [])
        return result

    def predict_procmon_sliding_window(
        self,
        source: Union[str, Dict[str, Any]],
        sample_proc: str = "",
        window_size: int = 100,
        step: int = 25,
        filter_loader_noise: bool = True,
    ) -> Dict[str, Any]:
        """Classify a Procmon artifact using sliding windows to detect peak malicious behavior."""
        from core.modules.procmon_lstm_bridge import (
            extract_sequence_from_procmon_csv,
            get_sliding_windows,
            procmon_to_lstm_payload,
        )

        if isinstance(source, (str, Path)) and str(source).endswith(".csv"):
            full_seq = extract_sequence_from_procmon_csv(
                str(source),
                sample_proc=sample_proc,
                max_length=0,
                filter_loader_noise=filter_loader_noise,
            )
            sample_name = sample_proc or "unknown"
            source_type = "csv"
        else:
            payload = procmon_to_lstm_payload(source, sample_proc=sample_proc, max_length=100)
            full_seq = payload["api_call_sequence"]
            sample_name = payload.get("sample_process", sample_proc or "unknown")
            source_type = payload.get("source_type", "summary_json")

        if not full_seq:
            return {
                "verdict": "UNKNOWN",
                "confidence": 0.0,
                "p_malware": 0.5,
                "p_benign": 0.5,
                "windows_evaluated": 0,
                "sample_process": sample_name,
                "source_type": source_type,
                "sequence_length": 0,
            }

        windows = get_sliding_windows(full_seq, window_size=window_size, step=step)
        best_result = None
        max_p_malware = -1.0
        peak_idx = 0

        for idx, w in enumerate(windows):
            res = self.predict_sequence(w)
            if res["p_malware"] > max_p_malware:
                max_p_malware = res["p_malware"]
                best_result = res
                peak_idx = idx

        start_offset = peak_idx * step
        end_offset = min(start_offset + window_size, len(full_seq))

        best_result["windows_evaluated"] = len(windows)
        best_result["peak_window_range"] = [start_offset, end_offset]
        best_result["sample_process"] = sample_name
        best_result["source_type"] = source_type
        best_result["total_sequence_length"] = len(full_seq)
        best_result["unique_apis"] = sorted(list(set(full_seq)))

        return best_result


def main():
    parser = argparse.ArgumentParser(description="Predict Malware vs Benign using trained LSTM.")
    parser.add_argument("--report", type=str, help="Path to report folder or procmon_summary.json")
    parser.add_argument("--csv", type=str, help="Path to raw procmon.csv")
    parser.add_argument("--apis", type=str, help="Comma-separated API call sequence")
    parser.add_argument("--sample_proc", type=str, default="", help="Target process filter for CSV mode")
    parser.add_argument("--sliding_window", action="store_true", help="Use sliding-window scanning for peak risk")
    parser.add_argument("--no_filter_loader", action="store_true", help="Disable PE loader noise filtering")
    parser.add_argument("--model", type=str, default=str(DEFAULT_MODEL_PATH), help="Path to best_lstm_model.pt")
    parser.add_argument("--vocab", type=str, default=str(DEFAULT_VOCAB_PATH), help="Path to vocab.json")

    args = parser.parse_args()

    engine = LSTMInferenceEngine(model_path=args.model, vocab_path=args.vocab)
    filter_loader = not args.no_filter_loader

    if args.apis:
        sequence = [a.strip() for a in args.apis.split(",") if a.strip()]
        result = engine.predict_sequence(sequence)
        print("\n=== Direct API Sequence Prediction ===")
        print(f"Sequence:   {sequence[:5]} ... ({len(sequence)} calls total)")
        print(f"Verdict:    {result['verdict']} ({result['confidence']}%)")
        print(f"P(Malware): {result['p_malware']} | P(Benign): {result['p_benign']}")
    elif args.report:
        report_path = Path(args.report)
        if report_path.is_dir():
            target = report_path / "artifacts" / "procmon" / "procmon_summary.json"
        else:
            target = report_path
        if args.sliding_window:
            result = engine.predict_procmon_sliding_window(str(target), sample_proc=args.sample_proc, filter_loader_noise=filter_loader)
        else:
            result = engine.predict_procmon(str(target), sample_proc=args.sample_proc, filter_loader_noise=filter_loader)
        print("\n=== Procmon Report Prediction ===")
        print(f"Process:    {result.get('sample_process')}")
        print(f"Sequence:   {result['sequence_length']} calls evaluated")
        print(f"Verdict:    {result['verdict']} ({result['confidence']}%)")
        print(f"P(Malware): {result['p_malware']} | P(Benign): {result['p_benign']}")
        print(f"Unique APIs: {result.get('unique_apis')}")
    elif args.csv:
        if args.sliding_window:
            result = engine.predict_procmon_sliding_window(args.csv, sample_proc=args.sample_proc, filter_loader_noise=filter_loader)
            print("\n=== Procmon CSV Sliding-Window Prediction ===")
            print(f"Process:       {result.get('sample_process')}")
            print(f"Total Calls:   {result.get('total_sequence_length')}")
            print(f"Windows Run:   {result.get('windows_evaluated')}")
            print(f"Peak Window:   {result.get('peak_window_range')}")
            print(f"Verdict:       {result['verdict']} ({result['confidence']}%)")
            print(f"P(Malware):    {result['p_malware']} | P(Benign): {result['p_benign']}")
        else:
            result = engine.predict_procmon(args.csv, sample_proc=args.sample_proc, filter_loader_noise=filter_loader)
            print("\n=== Procmon CSV Prediction ===")
            print(f"Process:    {result.get('sample_process')}")
            print(f"Sequence:   {result['sequence_length']} calls extracted")
            print(f"Verdict:    {result['verdict']} ({result['confidence']}%)")
            print(f"P(Malware): {result['p_malware']} | P(Benign): {result['p_benign']}")
    else:
        print("Please provide --report, --csv, or --apis. Run with --help for details.")


if __name__ == "__main__":
    main()
