import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

STAGES = ("upstream", "midstream", "downstream")
REQUIRED_STAGE_FIELDS = ("definition", "companies", "metrics", "date")
REQUIRED_METRICS = ("market_size", "margin_or_profit", "concentration")
MISSING_TAG = "[暂缺/待验证]"


def _is_missing_tag(value: Any) -> bool:
    return isinstance(value, str) and value.strip() == MISSING_TAG


def _is_non_empty(value: Any) -> bool:
    if _is_missing_tag(value):
        return True
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _validate_stage(stage_name: str, stage_data: Dict[str, Any], issues: List[str]) -> None:
    for field in REQUIRED_STAGE_FIELDS:
        if field not in stage_data:
            issues.append(f"{stage_name}.{field} 缺失")
            continue

        if not _is_non_empty(stage_data[field]):
            issues.append(f"{stage_name}.{field} 为空")

    companies = stage_data.get("companies")
    if companies is not None and not _is_missing_tag(companies):
        if not isinstance(companies, list):
            issues.append(f"{stage_name}.companies 应为数组或 {MISSING_TAG}")
        elif len(companies) == 0:
            issues.append(f"{stage_name}.companies 不能为空")

    metrics = stage_data.get("metrics")
    if isinstance(metrics, dict):
        for metric in REQUIRED_METRICS:
            if metric not in metrics:
                issues.append(f"{stage_name}.metrics.{metric} 缺失")
                continue
            if not _is_non_empty(metrics[metric]):
                issues.append(f"{stage_name}.metrics.{metric} 为空")
    elif metrics is not None and not _is_missing_tag(metrics):
        issues.append(f"{stage_name}.metrics 应为对象或 {MISSING_TAG}")


def validate_data_completeness(data: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []

    for stage in STAGES:
        stage_data = data.get(stage)
        if stage_data is None:
            issues.append(f"{stage} 模块缺失")
            continue
        if not isinstance(stage_data, dict):
            issues.append(f"{stage} 模块应为对象")
            continue
        _validate_stage(stage, stage_data, issues)

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "message": "数据完整性检查通过" if not issues else "数据完整性检查未通过",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查上中下游模块在写作前的数据完整性。")
    parser.add_argument("--json", type=str, required=True, help="待检查的结构化 JSON 文件路径")
    args = parser.parse_args()

    input_path = Path(args.json)
    if not input_path.exists():
        print(json.dumps({"passed": False, "message": f"输入文件不存在: {input_path}"}, ensure_ascii=False))
        return 2

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(json.dumps({"passed": False, "message": f"JSON 解析失败: {exc}"}, ensure_ascii=False))
        return 2

    result = validate_data_completeness(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
