#!/bin/bash
cd "$(dirname "$0")"  # 루트 위치로 이동
echo "🚀 Training DET model..."

python3 -m paddleocr.tools.train \
  -c ./training/configs/det_config.yml \
  --use_gpu=True \
  --save_model_dir ./models/det_model/ \
  --save_log_path ./training/logs/det_log/

echo "✅ DET training finished."
