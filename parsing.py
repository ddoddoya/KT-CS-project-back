import json

def is_inside(child_pts, parent_pts):
    (cx1, cy1), (cx2, cy2) = child_pts
    (px1, py1), (px2, py2) = parent_pts
    return cx1 >= px1 and cy1 >= py1 and cx2 <= px2 and cy2 <= py2


def is_middle(label):
    return "_" in label    


def is_top(label):
    return "_" not in label


def build_structure_from_raw(raw: dict) -> dict:

    # 노드 만들기
    nodes = []
    for label, info in raw.items():
        nodes.append({
            "label": label,
            "text": info["text"],     # 옵션일 때만 쓸 것
            "points": info["points"],
            "children": []
        })

    # 부모-자식 관계 설정
    for p in nodes:
        for c in nodes:
            if p is c:
                continue
            if is_inside(c["points"], p["points"]):
                p["children"].append(c)

    # 루트 노드 찾기
    roots = []
    for n in nodes:
        is_child = any(n in p["children"] for p in nodes)
        if not is_child:
            roots.append(n)

    # 변환 함수
    def convert(node):
        label = node["label"]

        # 1) leaf 노드 (children 없음)
        if len(node["children"]) == 0:
            return {
                "name": node["label"],
                "text": node["text"],
                "points": node["points"],
                "selected": False
            }

        # 2) 중간 노드 (옵션 그룹: 라벨에 '_' 포함)
        if is_middle(label):
            option_list = []

            for c in node["children"]:
                converted = convert(c)
                if "selected" in converted:   # leaf만 옵션
                    option_list.append(converted)

            return {
                label: {
                    "options": option_list,
                    "selected_option": None
                }
            }

        # 3) 최상위/일반 그룹 노드
        result = {label: {}}

        for c in node["children"]:
            converted = convert(c)
            if isinstance(converted, dict):
                result[label].update(converted)

        return result

    # 최종 구조 만들기
    final_output = {}
    for r in roots:
        final_output.update(convert(r))

    return final_output


def build_structure(
        raw_json_path="/home/elicer/KT-CS-project-back/output/raw_text.json",
        output_json="/home/elicer/KT-CS-project-back/output/structured_output.json"
    ):

    # 1) 기존대로 raw_text.json 읽기
    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 2) 메모리 기반 구조 생성 로직 재사용
    final_output = build_structure_from_raw(raw)

    # 3) 기존대로 structured_output.json 파일로 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("구조 생성 완료:", output_json)
    return final_output


if __name__ == "__main__":
    build_structure()
