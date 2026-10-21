#!/usr/bin/env bash
# ==============================================================================
# run_experiment.sh - Synthetic Augmentation & LSTM Re-training Pipeline
# ==============================================================================
# 1. Generates balanced synthetic benign dataset (train_augmented.json)
# 2. Trains the LSTM on the augmented training set
# 3. Evaluates on the UNTOUCHED, pristine hold-out test set (test.json)
# 4. Saves checkpoints, plots, and metrics to output/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${AI_DIR}/.." && pwd)"

VENV_DIR="${AI_DIR}/.venv_lstm"
DATA_DIR="${SCRIPT_DIR}/data"
OUTPUT_DIR="${SCRIPT_DIR}/output"
AUGMENTED_JSON="${DATA_DIR}/train_augmented.json"
ORIGINAL_TRAIN="${AI_DIR}/Laboratory2/lab/data/jsons/train.json"
ORIGINAL_TEST="${AI_DIR}/Laboratory2/lab/data/jsons/test.json"

echo "================================================================="
echo "       IsoLens - Synthetic Augmentation Experiment Runner        "
echo "================================================================="
echo "[*] Augmentation Directory: ${SCRIPT_DIR}"
echo "[*] Virtualenv Path:        ${VENV_DIR}"
echo "[*] Augmented Data Path:    ${AUGMENTED_JSON}"
echo "[*] Output Path:            ${OUTPUT_DIR}"

# 1. Ensure virtual environment exists and is activated
if [ ! -d "${VENV_DIR}" ]; then
    echo "[!] Virtual environment not found at ${VENV_DIR}."
    echo "[*] Running initial environment setup via run_lstm_training.sh..."
    bash "${AI_DIR}/run_lstm_training.sh" --help >/dev/null 2>&1 || true
fi

echo "[*] Activating virtual environment..."
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

# 2. Generate augmented dataset if not present
if [ ! -f "${AUGMENTED_JSON}" ]; then
    echo "[*] Generating synthetic benign sequences to balance the dataset..."
    python3 "${SCRIPT_DIR}/augment_dataset.py" \
        --input_train "${ORIGINAL_TRAIN}" \
        --output_train "${AUGMENTED_JSON}" \
        --target_benign 12000
    echo "[+] Augmentation complete."
else
    echo "[+] Existing augmented dataset detected at ${AUGMENTED_JSON}."
fi

# 3. Launch training on augmented data
echo "-----------------------------------------------------------------"
echo "[*] Launching LSTM training on AUGMENTED dataset..."
echo "[*] Evaluating against UNTOUCHED hold-out test set: ${ORIGINAL_TEST}"
echo "-----------------------------------------------------------------"

cd "${PROJECT_ROOT}"
python3 "${AI_DIR}/train_lstm.py" \
    --train_json "${AUGMENTED_JSON}" \
    --test_json "${ORIGINAL_TEST}" \
    --output_dir "${OUTPUT_DIR}" \
    --epochs 30 \
    --batch_size 64 \
    --lr 0.00015 \
    "$@"

echo "================================================================="
echo "[+] Experiment run completed."
echo "[*] Best Model:      ${OUTPUT_DIR}/best_lstm_model.pt"
echo "[*] Curves Plot:     ${OUTPUT_DIR}/training_curves.png"
echo "[*] Metrics History: ${OUTPUT_DIR}/training_history.csv"
echo "================================================================="
