import argparse
import re
from pathlib import Path

PLACEHOLDER = "<!-- 在这里注入 Agent 输出的 Markdown 文本内容 -->"
HEADING_REQUIREMENT_PATTERN = re.compile(r"^(#{1,6}\s+.*?)(?:\s*（([^）]*)）)\s*$")
REQUIREMENT_HINT_PATTERN = re.compile(
    r"(必填|必须|至少|建议|不少于|\d+字|\d+条|\d+行|\d+家|\d+项|\d+分)"
)


def clean_heading_requirements(md_text: str) -> str:
    """
    仅清理标题行尾部的模板要求括注，避免在网页中展示“必须填写/至少X行”等说明。
    保留 Markdown 原文件不变，只处理本次 HTML 注入内容。
    """
    lines = md_text.splitlines()
    cleaned_lines = []
    inside_fence = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            inside_fence = not inside_fence
            cleaned_lines.append(line)
            continue

        if not inside_fence:
            match = HEADING_REQUIREMENT_PATTERN.match(line)
            if match:
                hint_text = match.group(2)
                if REQUIREMENT_HINT_PATTERN.search(hint_text):
                    line = match.group(1)

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    if md_text.endswith("\n"):
        result += "\n"
    return result


def generate_report_html(md_file_path: str, template_path: str, output_path: str) -> int:
    """
    读取 Markdown 结果并合并进入 HTML 骨架中。
    """
    md_path = Path(md_file_path).expanduser().resolve()
    template_path_obj = Path(template_path).expanduser().resolve()
    output_path_obj = Path(output_path).expanduser().resolve()

    if not md_path.exists() or not template_path_obj.exists():
        print("文本或模板不存在，请检查路径。")
        return 2

    md_content = md_path.read_text(encoding="utf-8")
    md_content = clean_heading_requirements(md_content)
    html_template = template_path_obj.read_text(encoding="utf-8")

    if PLACEHOLDER not in html_template:
        print("模板中未找到 Markdown 注入占位符，请检查 references/report_ui.html。")
        return 2

    # 替换占位注入
    final_html = html_template.replace(PLACEHOLDER, md_content)

    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_path_obj.write_text(final_html, encoding="utf-8")

    print(f"✅ HTML 图谱研报已生成: {output_path_obj}")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成可视化的图谱研报 HTML 页面。")
    parser.add_argument("--md", type=str, required=True, help="生成的 Markdown 分析报告路径")
    default_template = Path(__file__).resolve().parent.parent / "references" / "report_ui.html"
    parser.add_argument("--template", type=str, default=str(default_template), help="HTML UI 模板路径")
    parser.add_argument("--out", type=str, default="final_analysis_report.html", help="输出文件名")
    args = parser.parse_args()

    raise SystemExit(generate_report_html(args.md, args.template, args.out))
