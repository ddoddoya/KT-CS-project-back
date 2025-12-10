# ocr_engine.py
"""
KT 유선 신청서 OCR 엔진 모듈

- 서버 내부에 고정된 라벨 JSON(유선신청서_v1.json)을 사용한다.
- 사용자/클라이언트는 이미지 파일만 보내면 된다.
- 외부에서 쓸 함수는 run_ocr(image_bytes) 하나만 노출한다.
"""

from typing import Dict, Any
import json
import os

import cv2
import numpy as np
from paddleocr import PaddleOCR


# =========================================================
# 0. 라벨 템플릿 JSON 고정 로딩
#    - 서버 시작 시 한 번만 읽어서 메모리에 올려놓고 계속 재사용
# =========================================================

# ✅ 이 경로를 네 실제 JSON 위치에 맞게 수정해줘
TEMPLATE_PATH = "/home/elicer/KT-CS-project-back/통합신청서_KT유선신청서_v1.36_2511월.json"

if not os.path.exists(TEMPLATE_PATH):
    raise FileNotFoundError(f"라벨 템플릿 JSON을 찾을 수 없습니다: {TEMPLATE_PATH}")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    TEMPLATE_LABEL_DATA: Dict[str, Any] = json.load(f)

if "shapes" not in TEMPLATE_LABEL_DATA:
    raise ValueError("라벨 템플릿 JSON에 'shapes' 키가 없습니다. Labelme 형식인지 확인하세요.")


# =========================================================
# 1. PaddleOCR 전역 초기화
# =========================================================
try:
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="korean",   # 현재 사용하는 언어
        use_gpu=True,    # GPU 환경 아니면 False로 변경
        show_log=False,
    )
except Exception as e:
    print(f"[WARN] PaddleOCR 한국어 모델 로드 실패, 영어 모델로 대체: {e}")
    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


# =========================================================
# 2. 전처리 함수
#    - 지금 네 predict.py에서 쓰는 방식에 맞게 내부만 조정하면 됨
# =========================================================
def preprocess(crop: np.ndarray) -> np.ndarray:
    """
    개별 필드 영역 전처리.

    기본:
    - 2배 확대
    - 그레이스케일 변환

    필요하면 이 함수만 네 전처리 로직에 맞게 수정.
    """
    if crop.size == 0:
        return np.zeros((10, 10), dtype=np.uint8)

    # 크기 확대 (배율은 너가 쓰던 값으로 조정)
    crop = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 그레이스케일
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    return gray


# =========================================================
# 3. 메인 OCR 함수 (외부에서 쓸 공개 함수)

# =========================================================
def run_ocr(image_bytes: bytes) -> Dict[str, Any]:

    # ---------- 1) 이미지 디코딩 ----------
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지 디코딩 실패: image_bytes가 올바른 이미지가 아닙니다.")

    h, w = img.shape[:2]
    label_data = TEMPLATE_LABEL_DATA  # ✅ 항상 고정 템플릿 사용

    raw_results: Dict[str, Any] = {}

    print("-" * 70)
    print("  ✅ run_ocr 시작 (이미지 bytes + 고정 유선신청서_v1 템플릿)  ")
    print("-" * 70)

    # ---------- 2) 각 shape(필드)별로 OCR ----------
    for shape in label_data["shapes"]:
        label = shape.get("label", "")

        # 좌표 추출
        try:
            x1_f, y1_f = shape["points"][0]
            x2_f, y2_f = shape["points"][1]
            x1, y1 = int(x1_f), int(y1_f)
            x2, y2 = int(x2_f), int(y2_f)
        except Exception as e:
            print(f"❌ 좌표 변환 실패 (라벨: {label}): {e}")
            raw_results[label] = {
                "text": "COORD_ERROR",
                "points": shape.get("points", []),
            }
            continue

        # 경계 보정
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))

        if x2 <= x1 or y2 <= y1:
            print(f"⚠️ 무효한 Bounding Box, 스킵 (라벨: {label})")
            raw_results[label] = {
                "text": "",
                "points": shape.get("points", []),
            }
            continue

        crop = img[y1:y2, x1:x2]
        pre = preprocess(crop)

        # ---------- OCR 실행 ----------
        raw_text = ""
        final_text = ""

        try:
            result = ocr.ocr(pre, cls=True)

            if result and len(result[0]) > 0:
                raw_text = " ".join([r[1][0] for r in result[0]])
                final_text = raw_text
            else:
                final_text = ""
                print(f"   ⚠️ 인식 실패 (라벨: {label})")

        except Exception as e:
            print(f"❌ OCR 처리 중 오류 (라벨: {label}): {e}")
            final_text = f"[OCR Error: {e}]"

        # ---------- 결과 저장 ----------
        raw_results[label] = {
            "text": final_text,
            "points": shape.get("points", []),
        }

        if final_text:
            print(f"[{label:<20}] '{final_text}'")
        else:
            print(f"[{label:<20}] (empty)")

    print("-" * 70)
    print(f"✅ run_ocr 완료: {len(raw_results)}개 필드 처리됨")

    return raw_results
