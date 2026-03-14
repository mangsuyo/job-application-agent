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
    r"기준",
    r"얼마나\s+중요한지\s+몸으로\s+익혔습니다",
    r"구조",
    r"보다",
]

PAREN_EXPLANATION_PATTERN = re.compile(r"[가-힣A-Za-z0-9][ \t]*\([^)]+\)")
QUOTE_PATTERN = re.compile(r"[\"']")
SUMMARY_PATTERN = re.compile(r"^\[[^\[\]\n]{1,80}\]$")
REVIEWER_STATUS_PATTERN = re.compile(r"최종 판정:\s*(통과|보류|탈락)")
REVIEWER_LOOP_PATTERN = re.compile(r"리뷰어 반복 횟수:\s*([12])회")
REMAINING_ISSUES_PATTERN = re.compile(r"잔여 미흡 항목:\s*(.+)")
REFERENCE_CHECK_PATTERN = re.compile(r"회사 레퍼런스 구조 비교:\s*(.+)")

REQUIRED_ASSET_PATHS = (
    "assets/resume.md",
    "assets/portfolio.md",
    "assets/credentials.md",
)


def extract_section(content: str, title: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(title)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None
    return match.group("body").strip()


def extract_reviewer_section(content: str) -> str | None:
    for title in ("리뷰어 평가", "자체 평가"):
        section = extract_section(content, title)
        if section is not None:
            return section
    return None


def extract_similarity_section(content: str) -> str | None:
    return extract_section(content, "유사 문항 참조")


def extract_question_tags_section(content: str) -> str | None:
    return extract_section(content, "질문 태그")


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


def validate_reference_section(text: str, path: Path) -> list[str]:
    issues: list[str] = []

    if not text:
        return ["`## 참조 자산` 섹션이 비어 있습니다."]

    listed_paths: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        body = line[2:].strip()
        candidate = body.split("|", 1)[0].strip()
        if candidate:
            listed_paths.append(candidate)

    if not listed_paths:
        issues.append("`## 참조 자산` 섹션에는 `- 경로 | 활용 메모` 형식의 항목이 필요합니다.")
        return issues

    root = path.parents[3]

    for required in REQUIRED_ASSET_PATHS:
        if required not in listed_paths:
            issues.append(f"`## 참조 자산`에 필수 공통 자산 `{required}`가 없습니다.")

    company_path = path.parents[1] / "company.md"
    company_rel = company_path.relative_to(root).as_posix()
    if company_rel not in listed_paths:
        issues.append(f"`## 참조 자산`에 회사 해석 문서 `{company_rel}`가 없습니다.")

    if not any(entry.startswith("companies/") and "/references/" in entry for entry in listed_paths):
        issues.append("`## 참조 자산`에는 최소 1개의 회사별 참고자료 경로가 필요합니다.")

    for entry in listed_paths:
        target = root / entry
        if not target.exists():
            issues.append(f"`## 참조 자산`에 적힌 경로가 실제로 존재하지 않습니다: `{entry}`")

    return issues


def validate_question_tags_section(text: str) -> list[str]:
    issues: list[str] = []
    allowed_types = {
        "motivation",
        "job-fit-and-career-vision",
        "problem-solving",
        "collaboration",
        "communication-and-conflict",
        "strengths-and-weaknesses",
        "achievement-and-challenge",
        "education-and-learning",
        "values-and-criteria",
        "adaptability-and-attitude",
    }

    if not text:
        return ["`## 질문 태그` 섹션이 비어 있습니다."]

    tags: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("대표 질문 유형:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                issues.append("`대표 질문 유형:` 값이 비어 있습니다.")
            else:
                tags.append(value)
                if value not in allowed_types:
                    issues.append(
                        "`대표 질문 유형:`은 question-library 분류 체계를 따라야 합니다. "
                        f"허용값: {', '.join(sorted(allowed_types))}"
                    )
        elif line.startswith("보조 태그:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                issues.append("`보조 태그:` 값이 비어 있습니다.")
        elif line.startswith("- "):
            issues.append(
                "`## 질문 태그`는 `대표 질문 유형:`과 `보조 태그:` 형식으로 적어야 합니다."
            )

    if not tags:
        issues.append("`## 질문 태그`에는 `대표 질문 유형:`이 반드시 있어야 합니다.")

    return issues


def validate_similarity_section(text: str, path: Path) -> list[str]:
    issues: list[str] = []

    if not text:
        return ["`## 유사 문항 참조` 섹션이 비어 있습니다."]

    root = path.parents[3]
    available_question_files = sorted(
        candidate.relative_to(root).as_posix()
        for candidate in root.glob("companies/*/questions/*.md")
        if candidate != path
    )
    if not available_question_files:
        return issues

    listed_paths: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        body = line[2:].strip()
        candidate = body.split("|", 1)[0].strip()
        if candidate:
            listed_paths.append(candidate)

    if not listed_paths:
        issues.append("`## 유사 문항 참조`에는 `- 경로 | 질문 태그 기준 유사한 이유` 형식의 항목이 필요합니다.")
        return issues

    question_refs = [
        entry for entry in listed_paths
        if entry.startswith("companies/") and "/questions/" in entry
    ]
    if not question_refs:
        issues.append("`## 유사 문항 참조`에는 `companies/*/questions/*.md` 경로가 최소 1개 필요합니다.")

    for entry in question_refs:
        if entry == path.relative_to(root).as_posix():
            issues.append("`## 유사 문항 참조`에는 현재 작성 중인 파일 자신을 넣을 수 없습니다.")
            continue
        target = root / entry
        if not target.exists():
            issues.append(f"`## 유사 문항 참조`에 적힌 경로가 실제로 존재하지 않습니다: `{entry}`")

    return issues


def validate_reviewer_section(text: str) -> list[str]:
    issues: list[str] = []
    required_labels = [
        "리뷰어 총평:",
        "리뷰어 반복 횟수:",
        "핵심 보완 포인트:",
        "수정 반영 요약:",
        "최종 판정:",
        "잔여 미흡 항목:",
        "회사 레퍼런스 구조 비교:",
    ]

    if not text:
        return ["`## 리뷰어 평가` 섹션이 비어 있습니다."]

    missing = [label for label in required_labels if label not in text]
    if missing:
        joined = ", ".join(missing)
        issues.append(
            "`## 리뷰어 평가` 섹션에 reviewer 형식이 부족합니다. "
            f"다음 항목이 필요합니다: {joined}"
        )
        return issues

    status_match = REVIEWER_STATUS_PATTERN.search(text)
    if not status_match:
        issues.append("`최종 판정:`은 `통과`, `보류`, `탈락` 중 하나로 적어야 합니다.")

    loop_match = REVIEWER_LOOP_PATTERN.search(text)
    if not loop_match:
        issues.append("`리뷰어 반복 횟수:`는 `1회` 또는 `2회` 형식으로 적어야 합니다.")

    remaining_match = REMAINING_ISSUES_PATTERN.search(text)
    if not remaining_match:
        issues.append("`잔여 미흡 항목:`을 적어야 합니다.")

    reference_match = REFERENCE_CHECK_PATTERN.search(text)
    if not reference_match:
        issues.append("`회사 레퍼런스 구조 비교:`에 비교 결과를 적어야 합니다.")

    if issues:
        return issues

    status = status_match.group(1)
    remaining = remaining_match.group(1).strip()
    reference_note = reference_match.group(1).strip()
    loop_count = int(loop_match.group(1))

    if status != "통과":
        issues.append("리뷰어의 `최종 판정`이 `통과`가 아니므로 아직 최종 검증 단계로 넘기면 안 됩니다.")

    if loop_count < 2:
        issues.append(
            "리뷰어 반복 횟수가 1회입니다. 최종 확정본으로 간주하려면 최소 2회 reviewer 루프를 거쳐야 합니다."
        )

    if remaining not in {"없음", "해당 없음"}:
        issues.append("`잔여 미흡 항목:`이 남아 있습니다. reviewer 지적을 모두 해소한 뒤 다시 검증해야 합니다.")

    if reference_note in {"미수행", "안 함", "없음", "미작성"}:
        issues.append(
            "`회사 레퍼런스 구조 비교:`가 비어 있거나 미수행 상태입니다. 비교 결과나 미적용의 구체적 사유를 적어야 합니다."
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

    reference_section = extract_section(content, "참조 자산")
    if reference_section is None:
        print("[ERROR] `## 참조 자산` 섹션을 찾지 못했습니다.")
        return 1

    similarity_section = extract_similarity_section(content)
    if similarity_section is None:
        print("[ERROR] `## 유사 문항 참조` 섹션을 찾지 못했습니다.")
        return 1

    question_tags_section = extract_question_tags_section(content)
    if question_tags_section is None:
        print("[ERROR] `## 질문 태그` 섹션을 찾지 못했습니다.")
        return 1

    reviewer_section = extract_reviewer_section(content)
    if reviewer_section is None:
        print("[ERROR] `## 리뷰어 평가` 또는 `## 자체 평가` 섹션을 찾지 못했습니다.")
        return 1

    issues = []
    issues.extend(validate_reference_section(reference_section, path))
    issues.extend(validate_question_tags_section(question_tags_section))
    issues.extend(validate_similarity_section(similarity_section, path))
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
