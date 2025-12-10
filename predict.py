import cv2, json
import numpy as np
import re
from paddleocr import PaddleOCR
import os
from typing import Dict, Any

# from fuzzywuzzy import fuzz  # 디버그 모드에서는 사용하지 않으므로 주석 처리(필요시 다시 사용)

# =========================================================================
# 1. OCR 초기화 및 한국어 모델 사용 (필수)
# =========================================================================
try:
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang='korean',
        use_gpu=True,
        show_log=False
    )
except Exception as e:
    print(f"경고: 한국어 모델 로드 실패. 기본 모델로 대체합니다. 에러: {e}")
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

# -------------------------------------------------------------------------
# 파일 경로 설정 (사용자 환경에 맞게 조정 필요)
image_path = "/home/elicer/KT-CS-project-back/신청서1.jpeg"
label_path = "/home/elicer/KT-CS-project-back/통합신청서_KT유선신청서_v1.36_2511월.json"
output_path = "/home/elicer/KT-CS-project-back/output/raw_text.json"

# 출력 디렉토리 확인 및 생성
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir) and output_dir:
    os.makedirs(output_dir)

# 이미지 및 JSON 데이터 로드
img = cv2.imread(image_path)
if img is None:
    raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

try:
    with open(label_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"JSON 라벨 파일을 찾을 수 없습니다: {label_path}")

raw_results: Dict[str, Any] = {}

# =========================================================================
# 2. 전처리 함수 (Preprocessing) - 단순화 버전
# =========================================================================
def preprocess(crop: np.ndarray) -> np.ndarray:
    if crop.size == 0:
        return np.zeros((10, 10), dtype=np.uint8)

    # 1) 살짝 확대 (2~2.5배 정도)
    crop = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 2) 그레이스케일만 적용
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # 필요하면 아주 약한 blur 정도만
    # gray = cv2.medianBlur(gray, 3)

    return gray

# =========================================================================
# 3. 후처리 함수 (Post-processing)
#    → 디버그 모드: 일단 전부 비활성화(순수 OCR 결과를 보기 위함)
# =========================================================================
# def postprocess(label: str, text: str) -> str:
#     ...
# =========================================================================
# 4. 메인 루프 (Main Loop) 실행 및 결과 출력
# =========================================================================
print("-" * 70)
print("       ✅ KT 신청서 맞춤형 OCR 시작 (디버그 모드: 후처리/라벨치환 OFF)        ")
print("-" * 70)

# JSON 구조 검증
if 'shapes' not in data or not isinstance(data.get('shapes'), list):
    raise ValueError("JSON 파일에 'shapes' 키가 없거나 리스트 형식이 아닙니다.")

for shape in data["shapes"]:
    label = shape["label"]

    # --- 좌표 추출 ---
    try:
        x1_f, y1_f = shape["points"][0]
        x2_f, y2_f = shape["points"][1]

        x1, y1, x2, y2 = int(x1_f), int(y1_f), int(x2_f), int(y2_f)
    except Exception as e:
        print(f"❌ 오류: {label} 필드의 좌표 추출/변환 실패. (에러: {e})")
        raw_results[label] = {"text": "COORD_ERROR", "points": shape.get("points", [])}
        continue

    # Bounding Box 유효성 검사
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)

    if x2 <= x1 or y2 <= y1:
        print(f"⚠️ 경고: {label} 필드의 Bounding Box가 유효하지 않아 스킵.")
        raw_results[label] = {"text": "", "points": shape["points"]}
        continue

    crop = img[y1:y2, x1:x2]
    pre = preprocess(crop)

    raw_text = ""
    post_processed_text = ""

    try:
        # OCR 수행
        result = ocr.ocr(pre, cls=True)

        if result and len(result[0]) > 0:
            # 1. OCR 결과가 있을 경우 → 디버그 모드에서는 순수 결과만 사용
            raw_text = " ".join([r[1][0] for r in result[0]])
            # post_processed_text = postprocess(label, raw_text)
            post_processed_text = raw_text  # 후처리 없이 그대로 사용

        else:
            # 2. OCR이 텍스트를 인식하지 못한 경우
            #    디버그 모드에서는 라벨로 대체하지 않고 빈 문자열로 남겨둠
            post_processed_text = ""
            print(f"   ⚠️ 인식 실패: '{label}' 영역에서 텍스트를 찾지 못했습니다.")

    except Exception as e:
        print(f"❌ OCR 처리 중 오류 발생 (필드: {label}): {e}")
        post_processed_text = f"[OCR Error: {e}]"

    raw_results[label] = {
        "text": post_processed_text,
        "points": shape["points"]
    }

    # 디버깅을 위한 결과 출력
    if raw_text and (raw_text != post_processed_text):
        print(f"[{label:<15}] Raw: '{raw_text}' -> **Fixed**: '{post_processed_text}'")
    elif post_processed_text:
        print(f"[{label:<15}] Result: '{post_processed_text}'")
    else:
        print(f"[{label:<15}] Result: (empty)")

print("-" * 70)

try:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)

    print(f"✅ OCR 완료: {len(raw_results)}개 필드 처리됨")
    print(f"→ 결과 파일: {output_path} 생성됨")

except Exception as e:
    print(f"❌ 결과 JSON 파일 저장 중 오류 발생: {e}")
