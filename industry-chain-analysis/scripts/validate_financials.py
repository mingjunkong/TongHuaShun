import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def validate_price_logic(report_data: dict) -> bool:
    """
    对产业链报告中的上下游价格区间、利润率进行逻辑自洽校验。
    """
    is_valid = True
    try:
        upstream_cost_max = sum([item.get('max_price', 0) for item in report_data.get('upstream_materials', [])])
        midstream_price_min = report_data.get('midstream_product', {}).get('min_price', 0)
        
        # 简单逻辑防呆检查：中游卖出的最低价不能离谱地低于上游原材料的总成本价（如果不具备大量政府补贴等因素）
        if midstream_price_min > 0 and upstream_cost_max > midstream_price_min:
            logging.error(
                "逻辑阻断: 中游产品售价估计区间下限 (%s) 低于主要上游物料推演成本上限 (%s)，请提示Agent重新推演或补充倒挂原因（如补贴、价格战等）。",
                midstream_price_min,
                upstream_cost_max,
            )
            is_valid = False
            
        # 检查代表企业数量
        for stage in ['upstream', 'midstream', 'downstream']:
            companies = report_data.get(stage, {}).get('companies', [])
            if 0 < len(companies) < 3 and not report_data.get(stage).get('is_monopoly'):
                logging.warning("提醒: 环节 %s 列出的公司少于3家且未声明垄断行业。", stage)
               
    except (TypeError, ValueError, AttributeError) as e:
        logging.error("校验异常: %s", e)
        
    return is_valid

def main() -> int:
    parser = argparse.ArgumentParser(description="校验产业链报告财务逻辑是否自洽。")
    parser.add_argument(
        "--json",
        type=str,
        required=True,
        help="待校验的报告结构化 JSON 文件路径",
    )
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        logging.error("输入文件不存在: %s", json_path)
        return 2

    try:
        report_data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logging.error("JSON 解析失败: %s", exc)
        return 2

    valid = validate_price_logic(report_data)
    if valid:
        print(json.dumps({"passed": True, "message": "财务逻辑校验通过"}, ensure_ascii=False))
        return 0

    print(json.dumps({"passed": False, "message": "财务逻辑校验未通过"}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
