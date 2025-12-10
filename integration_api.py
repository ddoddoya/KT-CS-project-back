# integration_api.py
import io
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI(
    title="KT CS 통합 OCR API",
    description="체크박스(YOLO) + OCR(유선신청서) 통합 엔드포인트",
    version="1.0.0",
)
CHECKBOX_URL = "https://jnadyknfzsmfhnyt.tunnel.elice.io/detect-checkbox"
OCR_URL       = "https://sryjsymzaxpkzfhf.tunnel.elice.io/ocr/structured"


@app.post("/analyze-form")
async def analyze_form(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()


        files_checkbox = {
            "file": (file.filename, io.BytesIO(image_bytes), file.content_type or "image/jpeg")
        }
        files_ocr = {
            "file": (file.filename, io.BytesIO(image_bytes), file.content_type or "image/jpeg")
        }

        resp_cb = requests.post(CHECKBOX_URL, files=files_checkbox)
        cb_data = resp_cb.json() if resp_cb.ok else {"success": False, "error": resp_cb.text}

        resp_ocr = requests.post(OCR_URL, files=files_ocr)
        ocr_data = resp_ocr.json() if resp_ocr.ok else {"success": False, "error": resp_ocr.text}

        return JSONResponse({
            "success": True,
            "checkbox": cb_data,   
            "ocr": ocr_data       
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
