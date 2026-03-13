#!/usr/bin/env python3
"""
Import one or more Linkareer accepted cover-letter pages into companies/<company>/references/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
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
            "Referer": "https://linkareer.com/",
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def extract_next_data(html: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise ValueError("`__NEXT_DATA__` 블록을 찾지 못했습니다.")
    return json.loads(match.group(1))


def find_cover_letter(node: Any) -> dict[str, Any] | None:
    if isinstance(node, dict):
        has_company = "company" in node and isinstance(node.get("company"), dict)
        has_org_name = isinstance(node.get("organizationName"), str)
        if "content" in node and (has_company or has_org_name):
            return node
        for value in node.values():
            found = find_cover_letter(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_cover_letter(value)
            if found:
                return found
    return None


def to_date(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()
    return str(value)


def split_qa(content: str) -> list[tuple[str, str]]:
    cleaned = unescape(content).replace("\r\n", "\n").strip()
    pattern = re.compile(
        r"(?ms)^\s*(\d+)\.\s*(.+?)\n\s*(.+?)(?=^\s*\d+\.\s+|\Z)"
    )
    pairs: list[tuple[str, str]] = []
    for match in pattern.finditer(cleaned):
        question = re.sub(r"\s+", " ", match.group(2)).strip()
        answer = re.sub(r"\n{3,}", "\n\n", match.group(3)).strip()
        pairs.append((question, answer))
    if not pairs:
        raise ValueError("문항과 답변을 분리하지 못했습니다.")
    return pairs


def build_markdown(url: str, cover_letter: dict[str, Any]) -> str:
    company = cover_letter.get("company") or {}
    company_name = (
        company.get("name", "").strip()
        or (cover_letter.get("organizationName") or "").strip()
        or "알 수 없음"
    )
    role = (cover_letter.get("role") or "").strip() or "알 수 없음"
    passed_at = to_date(cover_letter.get("passedAt"))
    university = (cover_letter.get("university") or "").strip()
    major = (cover_letter.get("major") or "").strip()
    grades = (cover_letter.get("grades") or "").strip()
    language_score = (cover_letter.get("languageScore") or "").strip()
    activity = (cover_letter.get("activity") or "").strip()
    qa_pairs = split_qa(cover_letter.get("content", ""))

    spec_parts = [part for part in [university, major, grades, language_score, activity] if part]
    lines = [
        f"## 링크드 레퍼런스: {company_name} / {role}",
        "",
        f"- 출처: {url}",
        f"- 회사: {company_name}",
        f"- 직무: {role}",
    ]
    if passed_at:
        lines.append(f"- 합격 시점: {passed_at}")
    if spec_parts:
        lines.append(f"- 스펙 요약: {' / '.join(spec_parts)}")

    lines.append("")
    lines.append("### 활용 원칙")
    lines.append("")
    lines.append("- 이 레퍼런스는 경험 내용을 복사하기 위한 자료가 아니다.")
    lines.append("- 우선 참고할 것은 문항에 답하는 논리, 문단 구성, 문장 밀도, 가독성, 설득 흐름이다.")
    lines.append("- 현재 지원자의 경험과 성과는 반드시 `assets/`와 현재 회사 문맥 기준으로 다시 구성한다.")
    lines.append("")
    lines.append("### 문항 및 답변")
    lines.append("")

    for index, (question, answer) in enumerate(qa_pairs, start=1):
        lines.extend(
            [
                f"#### Q{index}",
                question,
                "",
                "##### A",
                answer,
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def slug_from_url(url: str) -> str:
    match = re.search(r"/cover-letter/(\d+)", url)
    if match:
        return f"linkareer-{match.group(1)}.md"
    fallback = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")
    return f"{fallback[:60]}.md"


def write_reference(markdown: str, company_dir: Path, filename: str) -> Path:
    references_dir = company_dir / "references"
    references_dir.mkdir(parents=True, exist_ok=True)
    reference_path = references_dir / filename
    reference_path.write_text(markdown)
    return reference_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import one or more Linkareer accepted cover-letter pages into references/."
    )
    parser.add_argument(
        "sources",
        nargs="+",
        help="Linkareer URLs followed by the target companies/<company-name> path",
    )
    args = parser.parse_args()

    if len(args.sources) < 2:
        print("[ERROR] 최소 1개의 URL과 마지막 회사 폴더 경로가 필요합니다.")
        return 1

    urls = args.sources[:-1]
    trailing = args.sources[-1]
    if trailing.startswith("http://") or trailing.startswith("https://"):
        urls.append(trailing)
        print("[ERROR] 마지막 인자는 companies/<company-name> 경로여야 합니다.")
        return 1

    company_dir = Path(trailing)

    outputs: list[Path] = []
    references_dir = company_dir / "references"

    for url in urls:
        filename = slug_from_url(url)
        target_path = references_dir / filename
        if target_path.exists():
            print(f"[SKIP] already imported: {url}")
            continue

        html = fetch_html(url)
        data = extract_next_data(html)
        cover_letter = find_cover_letter(data)
        if not cover_letter:
            print(f"[ERROR] cover letter payload를 찾지 못했습니다: {url}")
            return 1

        markdown = build_markdown(url, cover_letter)
        outputs.append(write_reference(markdown, company_dir, filename))

    if not outputs:
        print("[OK] no new references to import")
        return 0

    print(f"[OK] imported {len(outputs)} reference(s)")
    for output in outputs:
        print(f"- {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
