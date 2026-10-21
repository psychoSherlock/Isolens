#!/usr/bin/env python3
"""
augment_dataset.py - Domain-Aware Synthetic API Sequence Augmentation for Benign Traces.

This script mitigates extreme class imbalance in malware/benign sequential API datasets
by generating realistic, semantically valid synthetic benign sequences using:
 1. Sliding Window Sub-sequence Extraction
 2. System Telemetry & Low-Impact Query Interleaving
 3. Functional API Synonym Substitution
"""

import argparse
import json
import os
import random
from pathlib import Path
from typing import List, Dict, Any


# Safe functional synonym mapping for Windows APIs
API_SYNONYMS = {
    "RegOpenKeyExW": "RegOpenKeyExA",
    "RegOpenKeyExA": "RegOpenKeyExW",
    "RegQueryValueExW": "RegQueryValueExA",
    "RegQueryValueExA": "RegQueryValueExW",
    "RegSetValueExW": "RegSetValueExA",
    "RegSetValueExA": "RegSetValueExW",
    "LdrGetDllHandle": "GetModuleHandleW",
    "GetModuleHandleW": "LdrGetDllHandle",
    "NtClose": "CloseHandle",
    "CloseHandle": "NtClose",
    "NtAllocateVirtualMemory": "VirtualAlloc",
    "VirtualAlloc": "NtAllocateVirtualMemory",
    "FindResourceExW": "FindResourceExA",
    "FindResourceExA": "FindResourceExW",
    "LoadStringW": "LoadStringA",
    "LoadStringA": "LoadStringW",
}

# Safe system telemetry & informational queries that Windows apps invoke routinely
SAFE_TELEMETRY_APIS = [
    "GetTickCount",
    "GetSystemMetrics",
    "GetCursorPos",
    "GetLocalTime",
    "NtQuerySystemInformation",
    "GetCurrentProcessId",
    "GetSystemTimeAsFileTime",
    "GetVersionExW",
    "Sleep",
]


def sliding_window_slice(sequence: List[str], min_len: int = 45, max_len: int = 75) -> List[str]:
    """Extract a valid sub-sequence window preserving chronological execution."""
    seq_len = len(sequence)
    if seq_len <= min_len:
        return list(sequence)

    window_size = random.randint(min_len, min(max_len, seq_len))
    max_start = seq_len - window_size
    start_idx = random.randint(0, max_start)
    return sequence[start_idx : start_idx + window_size]


def substitute_synonyms(sequence: List[str], swap_prob: float = 0.20) -> List[str]:
    """Substitute interchangeable API calls with their functional equivalents."""
    new_seq = []
    for api in sequence:
        if api in API_SYNONYMS and random.random() < swap_prob:
            new_seq.append(API_SYNONYMS[api])
        else:
            new_seq.append(api)
    return new_seq


def inject_telemetry_noise(sequence: List[str], inject_prob: float = 0.10) -> List[str]:
    """Interleave harmless system telemetry queries between operations."""
    new_seq = []
    for api in sequence:
        new_seq.append(api)
        if random.random() < inject_prob:
            new_seq.append(random.choice(SAFE_TELEMETRY_APIS))
    return new_seq


def generate_synthetic_benign(
    original_benign: List[Dict[str, Any]], target_count: int
) -> List[Dict[str, Any]]:
    """Generate synthetic benign traces until target_count is reached."""
    synthetic = []
    current_count = len(original_benign)
    needed = target_count - current_count

    print(f"[*] Generating {needed:,} synthetic benign samples from {current_count} seeds...")

    strategies = ["window_only", "synonym_window", "noise_window", "combined"]

    while len(synthetic) < needed:
        seed_sample = random.choice(original_benign)
        base_seq = seed_sample["api_call_sequence"]
        strategy = random.choice(strategies)

        if strategy == "window_only":
            new_seq = sliding_window_slice(base_seq)
        elif strategy == "synonym_window":
            sliced = sliding_window_slice(base_seq)
            new_seq = substitute_synonyms(sliced, swap_prob=random.uniform(0.15, 0.30))
        elif strategy == "noise_window":
            sliced = sliding_window_slice(base_seq)
            new_seq = inject_telemetry_noise(sliced, inject_prob=random.uniform(0.08, 0.15))
        elif strategy == "combined":
            sliced = sliding_window_slice(base_seq)
            with_synonyms = substitute_synonyms(sliced, swap_prob=0.20)
            new_seq = inject_telemetry_noise(with_synonyms, inject_prob=0.10)
        else:
            new_seq = list(base_seq)

        # Ensure valid length
        if len(new_seq) >= 20:
            synthetic.append({
                "api_call_sequence": new_seq,
                "is_malware": 0,
                "is_synthetic": True,
            })

    return synthetic


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic benign API sequences to balance dataset.")
    parser.add_argument(
        "--input_train",
        type=str,
        default="ai-implementation/Laboratory2/lab/data/jsons/train.json",
        help="Path to original train.json",
    )
    parser.add_argument(
        "--output_train",
        type=str,
        default="ai-implementation/synthetic-augmentation/data/train_augmented.json",
        help="Path to output augmented dataset",
    )
    parser.add_argument(
        "--target_benign",
        type=int,
        default=12000,
        help="Target total benign samples after augmentation (default: 12000)",
    )
    parser.add_argument("--seed", type=int, default=111, help="Random seed for reproducibility")

    args = parser.parse_args()
    random.seed(args.seed)

    print("=" * 65)
    print("      IsoLens - Synthetic API Sequence Augmentation Pipeline    ")
    print("=" * 65)
    print(f"Input Dataset:       {args.input_train}")
    print(f"Output Dataset:      {args.output_train}")
    print(f"Target Benign Count: {args.target_benign:,}")
    print("=" * 65)

    # 1. Load Original Train Dataset
    print(f"[*] Reading {args.input_train}...")
    with open(args.input_train, "r") as f:
        data = json.load(f)

    malware_samples = [s for s in data if s["is_malware"] == 1]
    benign_samples = [s for s in data if s["is_malware"] == 0]

    orig_mal_count = len(malware_samples)
    orig_ben_count = len(benign_samples)
    orig_total = len(data)

    print(f"[*] Original Distribution:")
    print(f"    - Malware: {orig_mal_count:,} ({orig_mal_count/orig_total*100:.2f}%)")
    print(f"    - Benign:  {orig_ben_count:,} ({orig_ben_count/orig_total*100:.2f}%)")
    print(f"    - Ratio:   {orig_mal_count/orig_ben_count:.1f} : 1")

    # 2. Generate Synthetic Benign Sequences
    synthetic_benign = generate_synthetic_benign(benign_samples, target_count=args.target_benign)

    # 3. Combine All Samples
    # Tag original samples with is_synthetic: False
    all_combined = []
    for s in malware_samples:
        all_combined.append({
            "api_call_sequence": s["api_call_sequence"],
            "is_malware": 1,
            "is_synthetic": False,
        })
    for s in benign_samples:
        all_combined.append({
            "api_call_sequence": s["api_call_sequence"],
            "is_malware": 0,
            "is_synthetic": False,
        })
    all_combined.extend(synthetic_benign)

    # 4. Shuffle combined dataset thoroughly
    random.shuffle(all_combined)

    new_total = len(all_combined)
    new_ben_count = sum(1 for s in all_combined if s["is_malware"] == 0)
    new_mal_count = sum(1 for s in all_combined if s["is_malware"] == 1)

    print("\n[*] Augmented Distribution:")
    print(f"    - Malware: {new_mal_count:,} ({new_mal_count/new_total*100:.2f}%)")
    print(f"    - Benign:  {new_ben_count:,} ({new_ben_count/new_total*100:.2f}%) "
          f"[{orig_ben_count} original + {len(synthetic_benign):,} synthetic]")
    print(f"    - Ratio:   {new_mal_count/new_ben_count:.2f} : 1 (Near balanced!)")
    print(f"    - Total:   {new_total:,} samples")

    # 5. Save Output
    output_path = Path(args.output_train)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[*] Writing augmented dataset to: {output_path}...")
    with open(output_path, "w") as f:
        json.dump(all_combined, f)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[+] Successfully saved augmented dataset ({file_size_mb:.2f} MB).")

    # Save summary metadata
    summary_path = output_path.parent / "augmentation_stats.json"
    stats = {
        "original_total": orig_total,
        "original_malware": orig_mal_count,
        "original_benign": orig_ben_count,
        "synthetic_benign_added": len(synthetic_benign),
        "augmented_total": new_total,
        "augmented_malware": new_mal_count,
        "augmented_benign": new_ben_count,
        "new_ratio_mal_to_ben": round(new_mal_count / new_ben_count, 2),
    }
    with open(summary_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[+] Augmentation summary written to: {summary_path}")


if __name__ == "__main__":
    main()
