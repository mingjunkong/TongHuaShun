import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


REQUIRED_SECTION_TITLES = [
    "## 0. 任务卡与研究边界",
    "## 1. 数据检索清单与证据台账",
    "## 2. 执行摘要",
    "## 3. 产业链全景图谱与价值池",
    "## 4. 上游深度拆解",
    "## 5. 中游深度拆解",
    "## 6. 下游深度拆解",
    "## 7. 情景分析与估值锚",
    "## 8. 风险、催化剂与跟踪指标",
    "## 9. 数据来源与质量闸门",
]

# YYYY, YYYYQX, YYYY-MM, YYYY/MM, YYYY年X月
DATE_PATTERN = re.compile(
    r"(?:20\d{2}(?:Q[1-4]|H[12])?|20\d{2}[-/](?:0?[1-9]|1[0-2])|20\d{2}年(?:0?[1-9]|1[0-2])月|20\d{2}年)",
    re.IGNORECASE,
)


def find_section_block(md: str, section_prefix: str) -> str:
    lines = md.splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(section_prefix):
            start = i
            break
    if start == -1:
        return ""

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end])


def count_table_rows(section_text: str) -> int:
    lines = [ln for ln in section_text.splitlines() if "|" in ln]
    if len(lines) < 3:
        return 0
    # Exclude header and separator; count remaining non-empty table rows.
    data_rows = 0
    for ln in lines[2:]:
        stripped = ln.strip()
        if stripped and stripped != "|":
            data_rows += 1
    return data_rows


def score_structure(md: str) -> Dict:
    missing = [title for title in REQUIRED_SECTION_TITLES if title not in md]
    score = 25
    deductions = min(len(missing) * 3, 25)
    score = max(0, score - deductions)
    notes = "章节完整" if not missing else f"缺失章节: {', '.join(missing)}"
    return {
        "score": score,
        "max": 25,
        "notes": notes,
    }


def score_quantitative(md: str) -> Dict:
    score = 25
    notes: List[str] = []

    has_cr = bool(re.search(r"CR3|CR5", md, re.IGNORECASE))
    has_margin = bool(re.search(r"毛利|利润率", md))
    has_bom = "BOM" in md
    has_date = bool(DATE_PATTERN.search(md))

    upstream_rows = count_table_rows(find_section_block(md, "## 4."))
    midstream_rows = count_table_rows(find_section_block(md, "## 5."))
    downstream_rows = count_table_rows(find_section_block(md, "## 6."))

    if not has_cr:
        score -= 5
        notes.append("缺少CR3/CR5")
    if not has_margin:
        score -= 5
        notes.append("缺少毛利/利润率")
    if not has_bom:
        score -= 5
        notes.append("缺少BOM")
    if not has_date:
        score -= 5
        notes.append("缺少日期口径")

    if upstream_rows < 3 or midstream_rows < 3 or downstream_rows < 3:
        score -= 5
        notes.append("上中下游企业表行数不足3")

    return {
        "score": max(0, score),
        "max": 25,
        "notes": "通过" if not notes else "; ".join(notes),
    }


def score_evidence(md: str) -> Dict:
    score = 25
    notes: List[str] = []

    # Evidence section and keywords
    has_sources_section = "## 9. 数据来源与质量闸门" in md
    source_keywords = ["财报", "公告", "协会", "监管", "数据库", "媒体"]
    present_categories = sum(1 for kw in source_keywords if kw in md)

    evidence_table_rows = count_table_rows(find_section_block(md, "## 1."))

    if not has_sources_section:
        score -= 10
        notes.append("缺少来源章节")
    if present_categories < 3:
        score -= 8
        notes.append("来源类别不足3")
    if evidence_table_rows < 8:
        score -= 7
        notes.append("证据台账少于8行")

    return {
        "score": max(0, score),
        "max": 25,
        "notes": "通过" if not notes else "; ".join(notes),
    }


def score_logic(md: str) -> Dict:
    score = 25
    notes: List[str] = []

    has_scenarios = all(token in md for token in ["Bear", "Base", "Bull"])
    has_quality_gate = "质量闸门" in md
    has_validation = "validate_financials.py" in md

    if not has_scenarios:
        score -= 10
        notes.append("缺少Bear/Base/Bull三情景")
    if not has_quality_gate:
        score -= 8
        notes.append("缺少质量闸门")
    if not has_validation:
        score -= 7
        notes.append("缺少财务逻辑校验引用")

    return {
        "score": max(0, score),
        "max": 25,
        "notes": "通过" if not notes else "; ".join(notes),
    }


def evaluate_markdown(md_text: str, threshold: int = 85) -> Dict:
    structure = score_structure(md_text)
    quantitative = score_quantitative(md_text)
    evidence = score_evidence(md_text)
    logic = score_logic(md_text)

    total = structure["score"] + quantitative["score"] + evidence["score"] + logic["score"]
    passed = total >= threshold

    return {
        "summary": {
            "total_score": total,
            "max_score": 100,
            "threshold": threshold,
            "passed": passed,
        },
        "dimensions": {
            "structure_completeness": structure,
            "quantitative_rigor": quantitative,
            "evidence_quality": evidence,
            "logic_consistency": logic,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score an industry chain markdown report.")
    parser.add_argument("--md", type=str, required=True, help="Path to markdown report")
    parser.add_argument("--out", type=str, default="", help="Optional output json path")
    parser.add_argument("--threshold", type=int, default=85, help="Minimum score to pass")
    args = parser.parse_args()

    md_path = Path(args.md)
    if not md_path.exists():
        print(f"ERROR: markdown file not found: {md_path}")
        return 2

    md_text = md_path.read_text(encoding="utf-8")
    result = evaluate_markdown(md_text, threshold=args.threshold)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if result["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
