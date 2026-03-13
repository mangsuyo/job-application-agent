#!/usr/bin/env python3
"""
Import a job-posting page into companies/<company>/company.md.
Currently optimized for ApplyIn pages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": url,
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def extract_applyin_resource(html: str) -> dict:
    match = re.search(
        r'<script type="application/json" id="recruit-resource">\s*(\{.*?\})\s*</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise ValueError("ApplyIn recruit-resource JSON을 찾지 못했습니다.")
    return json.loads(match.group(1))


def html_to_text(html: str) -> str:
    text = html
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|li|tr|h1|h2|h3|h4|h5|h6|ul|ol|table)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def build_markdown(url: str, payload: dict) -> str:
    data = payload["data"]
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    status = data.get("status", {}).get("text", "").strip()
    d_day = data.get("d_day")
    content_html = data.get("content", "")
    content_text = html_to_text(content_html)

    lines = [
        f"# {title}",
        "",
        f"- 출처: {url}",
    ]
    if description:
        lines.append(f"- 공고 설명: {description}")
    if status:
        lines.append(f"- 접수 상태: {status}")
    if d_day is not None:
        lines.append(f"- 마감 D-day: {d_day}")

    lines.extend(
        [
            "",
            "## 원문 정리",
            "",
            content_text,
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_company(markdown: str, company_dir: Path) -> Path:
    company_dir.mkdir(parents=True, exist_ok=True)
    company_path = company_dir / "company.md"
    company_path.write_text(markdown)
    return company_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a job-posting page into companies/<company>/company.md."
    )
    parser.add_argument("url", help="Job posting URL")
    parser.add_argument("company_dir", help="Path to companies/<company-name>")
    args = parser.parse_args()

    html = fetch_html(args.url)
    payload = extract_applyin_resource(html)
    markdown = build_markdown(args.url, payload)
    output_path = write_company(markdown, Path(args.company_dir))
    print(f"[OK] imported job posting to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
