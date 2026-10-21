#!/usr/bin/env bash
# ==============================================================================
# run_lstm_training.sh - Setup Virtual Environment & Train LSTM Malware Classifier
# ==============================================================================
# This script:
#  1. Detects Python (prefers Python 3.13 for CUDA 12.4 wheel compatibility)
#  2. Creates and activates a dedicated virtual environment (.venv_lstm)
#  3. Installs PyTorch (with CUDA 12.4 support) and all data-science dependencies
#  4. Runs the LSTM training pipeline for 25 epochs (configurable)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv_lstm"

echo "================================================================="
echo "       IsoLens - LSTM Malware Sequence Classifier Setup         "
echo "================================================================="
echo "[*] Script Directory:  ${SCRIPT_DIR}"
echo "[*] Project Root:      ${PROJECT_ROOT}"
echo "[*] Virtualenv Path:   ${VENV_DIR}"

# 1. Detect Python interpreter (prefer python3.13)
PYTHON_BIN=""
if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[-] Error: Python 3 was not found on your system."
    exit 1
fi
echo "[+] Using Python interpreter: $($PYTHON_BIN --version) ($PYTHON_BIN)"

# 2. Create virtual environment if not present
if [ ! -d "${VENV_DIR}" ]; then
    echo "[*] Creating dedicated virtual environment at ${VENV_DIR}..."
    "$PYTHON_BIN" -m venv "${VENV_DIR}"
    echo "[+] Virtual environment successfully created."
else
    echo "[+] Existing virtual environment detected at ${VENV_DIR}."
fi

# 3. Activate virtual environment
echo "[*] Activating virtual environment..."
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

# 4. Check and install dependencies
echo "[*] Verifying package dependencies..."
python -m pip install --upgrade pip setuptools wheel --quiet

# Check if PyTorch is already installed
if ! python -c "import torch" >/dev/null 2>&1; then
    echo "[*] Installing PyTorch with CUDA 12.4 support..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
else
    echo "[+] PyTorch is already installed."
fi

# Install data science dependencies
echo "[*] Installing required data-science packages..."
pip install pandas numpy scikit-learn matplotlib seaborn tqdm --quiet
echo "[+] All dependencies verified."

# 5. Check Hardware & CUDA Acceleration
echo "-----------------------------------------------------------------"
python -c "
import torch
cuda_avail = torch.cuda.is_available()
print(f'[*] PyTorch version: {torch.__version__}')
print(f'[*] CUDA Accelerated: {cuda_avail}')
if cuda_avail:
    print(f'[*] Active GPU:       {torch.cuda.get_device_name(0)}')
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**2)
    print(f'[*] Total VRAM:       {vram:.0f} MiB')
else:
    print('[!] Note: Running on CPU mode.')
"
echo "-----------------------------------------------------------------"

# 6. Execute Training Process
cd "${PROJECT_ROOT}"
echo "[*] Launching LSTM training process..."
echo "[*] Command: python ${SCRIPT_DIR}/train_lstm.py --epochs 25 $@"
echo "================================================================="

python "${SCRIPT_DIR}/train_lstm.py" --epochs 25 "$@"
