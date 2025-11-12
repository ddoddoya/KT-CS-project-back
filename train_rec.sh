#!/bin/bash
cd "$(dirname "$0")"  # 루트 위치로 이동
echo "🚀 Training REC model..."

python3 -m paddleocr.tools.train \
  -c ./training/configs/rec_config.yml \
  --use_gpu=True \
  --save_model_dir ./models/rec_model/ \
  --save_log_path ./training/logs/rec_log/

echo "✅ REC training finished."
