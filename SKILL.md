---
name: job-application-agent
description: 한국어 자기소개서 작성과 회사별 지원 작업을 위한 스킬. 국내 채용 지원에서 회사와 직무별 자기소개서 문항을 작성, 개선, 리라이트할 때 사용한다. 사용자의 이력서, 포트폴리오, 과거 지원서와 회사별 공고, 참고자료, 합격 자소서를 함께 참조해 문항별 완성본을 만든다.
---

# Job Application Agent

## 개요

회사별 작업공간을 기준으로 자기소개서를 작성하고 다듬는다. 공통 자산은 `assets/`에서 읽고, 회사별 자료와 문항별 작업 결과는 `companies/` 아래에서 관리한다.

## 작업 방식

- 먼저 지원 회사와 직무를 확인한다.
- 회사별 공고를 먼저 정리하고 회사 이해와 직무 이해를 끝낸 뒤 참고자료와 자소서 문항 전체를 받는다.
- 문항 전체를 먼저 받는 이유는 한 번에 전부 쓰기 위해서가 아니라, 어떤 경험을 어떤 문항에 배치할지 먼저 정하기 위해서다.
- `company.md`의 회사 이해와 직무 이해가 정리되기 전에는 초안을 쓰지 않는다.
- 합격 자소서와 회사 참고자료를 받기 전에는 문항 초안 작성으로 바로 넘어가지 않는다.
- 공통 자산은 `assets/resume.md`, `assets/portfolio.md`, `assets/past-applications/` 순서로 우선 참조한다.
- 사용자가 확정해 준 회사별 해석 최종본은 해당 `companies/<company-name>/company.md`를 이후 유사 질문 전반에서 가장 먼저 참조하는 기준 자산으로 취급한다.
- 정량 항목과 증빙성 성과는 `assets/credentials.md`에서 함께 참조한다.
- 세부 흐름은 `references/workflow.md`를 따른다.
- 공고 분석과 반영 원칙은 `references/job-posting.md`를 따른다.
- 작성 원칙은 `references/writing.md`를 따른다.
- 출력 형식과 문체 규칙은 `references/output-rules.md`를 따른다.
- 평가 기준은 `references/evaluation.md`를 따른다.
- 수정과 첨삭 기준은 `references/revision.md`를 따른다.
- 문단 구조와 리라이트 예시는 `references/few-shot.md`를 참고한다.
- 스타일 검증은 `scripts/validation.py`를 사용한다.
- 링크로 받은 원본 공고는 `scripts/import_job_posting.py`로 파싱해 `company.md`에 저장한다.
- `company.md`는 공고 원문 저장만 하는 파일이 아니라, 회사 이해, 직무 이해, 핵심 키워드, 자소서 반영 포인트까지 정리한 해석 문서로 사용한다.
- 링크로 받은 합격 자소서는 `scripts/import_linkareer_reference.py`로 파싱해 `references/` 폴더 아래에 개별 파일로 저장한다.
- 회사별 참고자료 입력은 합격 자소서에 한정하지 않는다.
- 인재상 글, 기업문화 글, 블로그 글, 자소서 작성 팁, 면접 후기, 현직자 글도 모두 `companies/<company-name>/references/` 아래의 정상 입력으로 취급한다.
- 현재 회사 자료가 아니더라도 문항이 같거나 매우 유사한 타회사 합격 자소서는 보조 레퍼런스로 받을 수 있다.
- 이런 자료도 현재 작업 중인 회사 폴더의 `references/` 아래에 보관하되, 현재 회사 자료보다 낮은 우선순위로 참고한다.
- 기업과 무관하게 수집하는 합격 자소서 링크는 `question-library/` 아래의 질문 유형 라이브러리에 저장한다.
- `question-library/`는 질문 유형 기준 공통 few-shot 저장소이며, 각 항목에는 원문과 구조 분석을 함께 남긴다.
- 새 레퍼런스에서 반복적으로 확인되는 좋은 구조 패턴은 먼저 `question-library/`에 축적하고, 여러 사례에서 다시 확인되면 `references/few-shot.md`로 승격하며, 더 보편적인 규칙으로 검증되면 `references/writing.md`, `references/workflow.md`, `references/evaluation.md` 같은 공통 규칙 문서에 반영한다.
- 사용자가 각 문항에 대해 직접 고친 완성본을 주는 경우에는 그 문안을 우선 반영하고, 가능하면 기존 초안과 함께 `before`, `after`로 저장해 차이를 분석한다.
- 이런 `before`, `after` 비교에서 반복적으로 확인되는 개선 패턴은 먼저 메모나 `question-library/`에 누적하고, 다시 확인되면 `references/few-shot.md`와 공통 규칙 문서로 승격한다.
- 노션 MCP 같은 외부 기록 시스템을 사용할 경우에는 최종 답변만 저장하지 말고, 각 문항의 질문 원문과 글자 수 제한도 함께 저장할 수 있도록 구조를 잡는다.

## 작업공간 구조

- `assets/resume.md`: 이력서 및 기본 경력 정보
- `assets/portfolio.md`: 프로젝트와 작업물 상세 정보
- `assets/credentials.md`: 자격증, 수상, 교육, 대외활동 같은 정량 항목
- `assets/past-applications/`: 과거 지원서 모음
- `companies/<company-name>/company.md`: 회사 공고와 JD
- `companies/<company-name>/references/`: 합격 자소서, 인재상, 블로그 글, 면접 후기, 현직자 글 같은 회사별 참고자료
- `companies/<company-name>/questions/q1.md`: 문항별 작업 문서
- `question-library/`: 기업 무관 질문 유형별 합격 자소서 라이브러리

## 기본 원칙

- 각 문항은 `questions/q1.md`, `q2.md` 같은 개별 파일에서 작업한다.
- 전체 문항을 먼저 보고 경험 배치 전략을 정한 뒤 실제 작성은 한 문항씩 진행한다.
- 전체 문항을 받은 뒤에는 바로 쓰기 시작하지 말고, 어떤 경험을 어떤 문항에 배치할지 문항별 경험 배치안을 먼저 정리해 사용자와 합의한다.
- 문항은 한 번에 하나씩 작성한다.
- 각 문항은 `writer -> reviewer -> revision -> final validation` 순서의 내부 루프를 먼저 거친 뒤 사용자에게 보여준다.
- reviewer는 초안을 떨어뜨릴 이유를 찾는 역할이며, validation은 마지막 형식 게이트로만 사용한다.
- 사용자가 `company.md` 확정본이나 그에 준하는 최종 해석을 주면, 해당 `companies/<company-name>/company.md`를 다음 세션과 다음 회사 지원의 유사 질문에서도 우선 반영하는 기준 자산으로 사용한다.
- 각 문항은 내부 내용 루프를 끝낸 뒤 `scripts/validation.py`로 마지막 검증을 하고, 그 다음 CLI에 답변을 보여준 뒤 사용자 피드백을 받는다.
- 사용자가 피드백 대신 완성본에 가까운 문안을 주면, 그 문안을 반영하고 기존 초안과 비교 분석까지 수행한다.
- 사용자가 현재 문항을 완료했다고 판단한 뒤에만 다음 문항으로 넘어간다.
- 합격 자소서는 정답에 가까운 참고 케이스로 보되, 경험 자체를 가져오는 용도가 아니라 가독성, 논리 전개, 문장 밀도, 설득 방식을 참고하는 용도로 사용한다.
- 타회사 합격 자소서는 현재 회사 자료가 부족할 때 문항 대응 방식과 전개 구조를 참고하는 보조 레퍼런스로만 사용한다.
- 반복 패턴의 승격 순서는 항상 `question-library`에서 관찰, `few-shot`에서 일반화, `rules`에서 고정의 순서를 따른다.
- 모든 문항에서 경험 설명만으로 끝내지 않고, 그 경험을 통해 무엇을 배우고 어떤 기준을 갖게 되었는지까지 써야 한다.
- 한 문항에 많은 경험을 나열하기보다 가장 강한 경험 하나를 깊게 쓰는 방식을 기본으로 한다.
- 사용자가 특정 경험이나 톤을 지정하지 않으면 자산과 회사 자료를 바탕으로 스스로 판단한다.
- 최종 답변은 내용 평가와 `scripts/validation.py` 검증을 모두 통과한 뒤 확정한다.
