#!/usr/bin/env python3
"""
Validate the final answer section in a question markdown file.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


AI_PATTERNS = [
    r"저는\s+귀사",
    r"기여할\s+수\s+있다고\s+생각합니다",
    r"역량을\s+발휘",
    r"성장할\s+수\s+있는\s+기회",
    r"최선을\s+다하겠습니다",
    r"문제\s+해결\s+역량",
]

PAREN_EXPLANATION_PATTERN = re.compile(r"[가-힣A-Za-z0-9][ \t]*\([^)]+\)")
QUOTE_PATTERN = re.compile(r"[\"']")
SUMMARY_PATTERN = re.compile(r"^\[[^\[\]\n]{1,80}\]$")


def extract_section(content: str, title: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(title)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None
    return match.group("body").strip()


def parse_length_rule(raw: str | None) -> tuple[str, int] | None:
    if not raw:
        return None

    normalized = re.sub(r"\s+", "", raw)
    match = re.search(r"(\d+)자", normalized)
    if not match:
        return None

    mode = "with_spaces"
    if "공백제외" in normalized:
        mode = "without_spaces"
    return mode, int(match.group(1))


def count_chars(text: str, mode: str) -> int:
    normalized = text.replace("\n", "")
    if mode == "without_spaces":
        normalized = re.sub(r"\s+", "", normalized)
    return len(normalized)


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"([.!?])\s+", r"\1\n", text.strip())
    normalized = re.sub(r"(다\.|요\.)\s+", r"\1\n", normalized)
    return [chunk.strip() for chunk in normalized.splitlines() if chunk.strip()]


def validate_paragraph_summaries(text: str) -> list[str]:
    issues: list[str] = []
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text.strip()) if paragraph.strip()]
    if not paragraphs:
        issues.append("최종 답변에 문단이 없습니다.")
        return issues

    for index, paragraph in enumerate(paragraphs, start=1):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        if not SUMMARY_PATTERN.match(lines[0]):
            issues.append(f"{index}번째 문단 첫 줄에 `[문단 요약]` 형식이 없습니다.")
            continue
        if "." in lines[0]:
            issues.append(f"{index}번째 문단 요약에 마침표가 있습니다.")

    return issues


def validate_reviewer_section(text: str) -> list[str]:
    issues: list[str] = []
    required_labels = [
        "탈락 사유:",
        "미흡한 평가 항목:",
        "수정 우선순위:",
        "유지할 강한 문장:",
        "삭제 또는 축소할 문장:",
    ]

    if not text:
        return ["`## 자체 평가` 섹션이 비어 있습니다."]

    missing = [label for label in required_labels if label not in text]
    if missing:
        joined = ", ".join(missing)
        issues.append(
            "`## 자체 평가` 섹션에 reviewer 형식이 부족합니다. "
            f"다음 항목이 필요합니다: {joined}"
        )

    return issues


def validate_text(text: str, length_rule: tuple[str, int]) -> list[str]:
    issues: list[str] = []

    if not text:
        issues.append("최종 답변 섹션이 비어 있습니다.")
        return issues

    issues.extend(validate_paragraph_summaries(text))

    mode, limit = length_rule
    actual = count_chars(text, mode)
    if actual > limit:
        basis = "공백 제외" if mode == "without_spaces" else "공백 포함"
        issues.append(f"글자 수 제한을 초과했습니다. 기준 {basis} {limit}자, 현재 {actual}자입니다.")

    comma_count = text.count(",")
    if comma_count >= 4:
        issues.append("쉼표 사용이 많습니다. 문장을 나누거나 연결 구조를 단순화하는 편이 좋습니다.")

    if "(" in text or ")" in text:
        issues.append("괄호 표현이 포함되어 있습니다. 본문 문장으로 풀어 쓰는 편이 좋습니다.")

    if PAREN_EXPLANATION_PATTERN.search(text):
        issues.append("용어 뒤에 괄호로 부가설명을 붙인 표현이 있습니다. 예: `낙관적 UI(Optimistic UI)`")

    if QUOTE_PATTERN.search(text):
        issues.append("작은따옴표 또는 큰따옴표가 포함되어 있습니다. 따옴표는 금지이므로 문장으로 다시 풀어 써야 합니다.")

    if "·" in text:
        issues.append("가운데점이 포함되어 있습니다. 문장을 분리해서 자연스럽게 연결하는 편이 좋습니다.")

    for pattern in AI_PATTERNS:
        if re.search(pattern, text):
            issues.append(f"AI 같은 상투 표현이 감지되었습니다: `{pattern}`")

    sentences = split_sentences(text)
    if sentences:
        long_sentences = [sentence for sentence in sentences if len(sentence) >= 120]
        if long_sentences:
            issues.append("너무 긴 문장이 있습니다. 문장을 더 짧게 나누는 편이 좋습니다.")

    repeated_phrases = re.findall(r"(\b[가-힣A-Za-z]{2,}\b)(?:\s+\1){1,}", text)
    if repeated_phrases:
        unique = ", ".join(sorted(set(repeated_phrases)))
        issues.append(f"반복 표현이 감지되었습니다: {unique}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the final answer section in a question markdown file."
    )
    parser.add_argument("path", help="Path to qN.md")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return 1

    content = path.read_text()

    length_rule_section = extract_section(content, "글자 수 제한")
    if length_rule_section is None:
        print("[ERROR] `## 글자 수 제한` 섹션을 찾지 못했습니다.")
        return 1

    length_rule = parse_length_rule(length_rule_section)
    if length_rule is None:
        print("[ERROR] `## 글자 수 제한` 섹션에서 `700자`, `공백 포함 700자`, `공백 제외 700자` 같은 형식을 찾지 못했습니다.")
        return 1

    final_answer = extract_section(content, "최종 답변")
    if final_answer is None:
        print("[ERROR] `## 최종 답변` 섹션을 찾지 못했습니다.")
        return 1

    reviewer_section = extract_section(content, "자체 평가")
    if reviewer_section is None:
        print("[ERROR] `## 자체 평가` 섹션을 찾지 못했습니다.")
        return 1

    issues = []
    issues.extend(validate_reviewer_section(reviewer_section))
    issues.extend(validate_text(final_answer, length_rule))
    if issues:
        print("[FAIL] validation failed")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("[OK] validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
