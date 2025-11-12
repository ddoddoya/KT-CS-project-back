import os, json, random, shutil
from tqdm import tqdm

# ======== 기본 경로 ========
BASE_DIR = "/home/elicer/dataset/data/"
TRAIN_DIR = os.path.join(BASE_DIR, "1.Training")
VAL_DIR = os.path.join(BASE_DIR, "2.Validation")

OUT_DIR = "/home/elicer/KT-CS-project-back/dataset"
IMG_OUT_DIR = os.path.join(OUT_DIR, "images")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMG_OUT_DIR, exist_ok=True)

# ======== 샘플 비율 ========
SAMPLES = {
    "print": 20000,     # 인쇄체
    "hand_char": 7000,  # 필기체 - 글자
    "hand_word": 3000   # 필기체 - 단어
}
VAL_RATIO = 0.1  # 검증 데이터 비율

# ======== 라벨 경로 설정 함수 ========
def label_dirs(base):
    return {
        "print": os.path.join(base, "Label", "1.Printed"),
        "hand_char": os.path.join(base, "Label", "2.Handwritten", "1.Character"),
        "hand_word": os.path.join(base, "Label", "2.Handwritten", "2.Word"),
    }

TRAIN_LABELS = label_dirs(TRAIN_DIR)
VAL_LABELS = label_dirs(VAL_DIR)

# ======== 공통 함수 ========

def load_json_files(label_dir, max_samples):
    json_paths = []
    for root, _, files in os.walk(label_dir):
        for f in files:
            if f.endswith(".json"):
                json_paths.append(os.path.join(root, f))
    random.shuffle(json_paths)
    return json_paths[:max_samples] if max_samples else json_paths

def extract_texts(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [w["value"].strip() for w in data.get("text", {}).get("word", []) if w.get("value")]
    except Exception:
        return []

def convert_det_item(json_path):
    img_path = json_path.replace("Label", "Character").replace(".json", ".jpg")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    anns = []
    for w in data.get("text", {}).get("word", []):
        if "wordbox" in w:
            anns.append({"transcription": w.get("value", ""), "points": w["wordbox"]})
    return {"image_path": img_path, "annotations": anns}

# ======== 균형 샘플링 ========

def sample_balanced():
    print(" 균형 샘플링 진행 중...")
    selected = []
    for k, v in SAMPLES.items():
        label_dirs_combined = [TRAIN_LABELS[k], VAL_LABELS[k]]
        all_jsons = []
        for d in label_dirs_combined:
            all_jsons += load_json_files(d, None)
        random.shuffle(all_jsons)
        selected.extend(all_jsons[:v])
        print(f" - {k}: {len(all_jsons[:v])}개 선택 완료")
    random.shuffle(selected)
    split = int(len(selected) * (1 - VAL_RATIO))
    return selected[:split], selected[split:]

# ======== DET / REC 생성 ========

def create_det_json(file_list, out_path):
    det_data = []
    for js in tqdm(file_list, desc=f"DET 생성 ({os.path.basename(out_path)})"):
        det_data.append(convert_det_item(js))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(det_data, f, ensure_ascii=False, indent=2)
    print(f" {out_path} 저장 완료 ({len(det_data)}개)")

def create_rec_txt(file_list, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        for js in tqdm(file_list, desc=f"REC 생성 ({os.path.basename(out_path)})"):
            img_path = js.replace("Label", "Character").replace(".json", ".jpg")
            texts = extract_texts(js)
            if texts:
                f.write(f"{img_path}\t{' '.join(texts)}\n")
    print(f" {out_path} 저장 완료 ({len(file_list)}개 기준)")

# ======== 이미지 복사 ========

def copy_images(file_list, output_dir):
    copied = 0
    for js in tqdm(file_list, desc="📸 이미지 복사 중"):
        img_path = js.replace("Label", "Character").replace(".json", ".jpg")
        if os.path.exists(img_path):
            fname = os.path.basename(img_path)
            dst = os.path.join(output_dir, fname)
            shutil.copy2(img_path, dst)
            copied += 1
    print(f" 이미지 {copied:,}장 복사 완료 → {output_dir}")

# ======== 메인 실행 ========

if __name__ == "__main__":
    train_files, val_files = sample_balanced()
    print(f" 학습: {len(train_files)}개 / 검증: {len(val_files)}개")

    create_det_json(train_files, os.path.join(OUT_DIR, "train_det.json"))
    create_det_json(val_files, os.path.join(OUT_DIR, "val_det.json"))
    create_rec_txt(train_files, os.path.join(OUT_DIR, "train_rec.txt"))
    create_rec_txt(val_files, os.path.join(OUT_DIR, "val_rec.txt"))

    copy_images(train_files + val_files, IMG_OUT_DIR)

    print(" DET + REC + 이미지 복사까지 완료!")
