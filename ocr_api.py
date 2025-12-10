# ocr_api.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from ocr_engine import run_ocr
from parsing import build_structure_from_raw


app = FastAPI(
    title="KT CS OCR API",
    description="유선 신청서 고정 템플릿 기반 OCR + 구조화 API",
    version="1.0.0",
)


# --------------------------------------------------------
# 1. 단순 OCR 결과만 보고 싶을 때 (디버그용)
# --------------------------------------------------------
@app.post("/ocr/raw")
async def ocr_raw(file: UploadFile = File(...)):
    """
    업로드된 신청서 이미지에서
    필드별 OCR 결과만 반환하는 엔드포인트.

    반환 구조 (예시):
    {
      "success": true,
      "data": {
        "고객명": { "text": "홍길동", "points": [[x1,y1],[x2,y2]] },
        "연락처": { "text": "010-1234-5678", "points": [...] },
        ...
      }
    }
    """
    try:
        image_bytes = await file.read()

        raw_results = run_ocr(image_bytes)

        return JSONResponse({
            "success": True,
            "data": raw_results
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


# --------------------------------------------------------
# 2. 최종 구조화된 결과 (트리/옵션 구조까지)
# --------------------------------------------------------
@app.post("/ocr/structured")
async def ocr_structured(file: UploadFile = File(...)):
    """
    업로드된 신청서 이미지에서
    - 필드별 OCR
    - parsing.py의 트리/옵션 구조 생성
    까지 수행한 최종 결과를 반환하는 엔드포인트.

    반환 구조 (예시):
    {
      "success": true,
      "data": {
        "최상단라벨1": {
          "중간라벨1_옵션그룹": {
            "options": [
              { "name": "옵션1", "text": "...", "points": [...], "selected": false },
              ...
            ],
            "selected_option": null
          },
          ...
        },
        "최상단라벨2": { ... }
      }
    }
    """
    try:
        image_bytes = await file.read()

        # 1) OCR (raw_results: label -> {text, points})
        raw_results = run_ocr(image_bytes)

        # 2) 구조화 (기존 parsing.py 로직 그대로 사용)
        structured = build_structure_from_raw(raw_results)

        return JSONResponse({
            "success": True,
            "data": structured
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


# --------------------------------------------------------
# 3. 헬스체크용 엔드포인트
# --------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}
