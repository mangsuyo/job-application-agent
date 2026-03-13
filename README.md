# job-application-agent

License: MIT

한국어 자기소개서 초안을 회사별 컨텍스트에 맞춰 작성하는 Codex skill 저장소입니다.

공고 링크, 합격 자소서 레퍼런스, 개인 자산을 워크스페이스에 정리한 뒤 문항별 초안 작성과 reviewer 루프, validation까지 같은 구조로 반복할 수 있게 설계되어 있습니다.

## Architecture

```text
 Input Sources                         Workspace                           Drafting Loop
┌────────────────────────┐    ┌──────────────────────────────┐    ┌──────────────────────────────┐
│ job posting URL        │    │ assets/                      │    │ question planning            │
│ Linkareer URLs         │──▶ │ companies/<company>/         │──▶ │ writer                       │
│ personal assets        │    │ question-library/            │    │ reviewer                     │
│ user-provided prompts  │    │ references/                  │    │ revision                     │
└────────────────────────┘    └──────────────────────────────┘    │ validation                   │
                                                                  └──────────────────────────────┘
```

## Core Interfaces

### 1. Job posting import

공고 링크를 `companies/<company-name>/company.md`로 정규화합니다.

```bash
python3 scripts/import_job_posting.py <job-posting-url> companies/<company-name>
```

출력:

- `companies/<company-name>/company.md`

현재 구현은 ApplyIn 페이지 구조를 기준으로 동작합니다.

### 2. Linkareer reference import

링커리어 합격 자소서 링크를 회사별 레퍼런스 파일로 정규화합니다.

```bash
python3 scripts/import_linkareer_reference.py <url1> <url2> companies/<company-name>
```

출력:

- `companies/<company-name>/references/linkareer-xxxx.md`

현재 구현은 Linkareer 합격 자소서 페이지 구조를 기준으로 동작합니다.

### 3. Question file validation

문항 파일의 최종 형식을 검사합니다.

```bash
python3 scripts/validation.py companies/<company-name>/questions/q1.md
```

검사 섹션:

- `## 글자 수 제한`
- `## 자체 평가`
- `## 최종 답변`

## Execution Model

이 저장소는 먼저 회사 컨텍스트를 고정한 뒤 문항별로 내려가는 방식을 전제로 합니다.

실행 순서:

1. `assets/`에 기본 자산을 정리한다.
2. 지원 회사용 워크스페이스를 만든다.
3. 공고를 `company.md`로 가져온다.
4. 합격 자소서와 회사별 참고자료를 `references/`에 모은다.
5. 문항 전체를 한 번에 수집한다.
6. 문항별 경험 배치안을 먼저 정한다.
7. 그다음부터 `q1.md`, `q2.md`처럼 한 문항씩 작성한다.
8. 각 문항은 `writer -> reviewer -> revision -> final validation` 순서로 닫는다.

## Quick Start

### 1. Prepare shared assets

`assets/`에 아래 파일을 준비합니다.

- `assets/resume.md`
- `assets/portfolio.md`
- `assets/credentials.md`
- `assets/past-applications/`

형식은 `assets/*.example.md`를 참고하면 됩니다.

### 2. Create a company workspace

```bash
mkdir -p companies/<company-name>/{references,questions}
```

### 3. Import the job posting

```bash
python3 scripts/import_job_posting.py <job-posting-url> companies/<company-name>
```

### 4. Import accepted cover-letter references

```bash
python3 scripts/import_linkareer_reference.py <url1> <url2> companies/<company-name>
```

### 5. Draft question files

문항은 `companies/<company-name>/questions/q1.md`처럼 개별 파일에서 작업합니다.

### 6. Validate final output

```bash
python3 scripts/validation.py companies/<company-name>/questions/q1.md
```

## Workspace Contract

```text
assets/                              # shared applicant context
  resume.md                          # base resume
  portfolio.md                       # project details and evidence
  credentials.md                     # certifications, awards, activities
  past-applications/                 # previous applications
companies/
  <company-name>/
    company.md                       # posting source + company/job interpretation
    references/                      # company-specific references
    questions/                       # q1.md, q2.md, ...
question-library/                    # question-type indexed reference set
references/                          # global writing/review/validation rules
scripts/                             # import and validation utilities
SKILL.md                             # agent-level workflow contract
```

경로가 곧 컨텍스트 경계이고, 파일 이름이 곧 작업 단위입니다.

## Repository Layout

```text
job-application-agent/
├── agents/
│   └── openai.yaml
├── assets/
├── companies/
│   └── demo-company/
├── question-library/
├── references/
├── scripts/
│   ├── import_job_posting.py
│   ├── import_linkareer_reference.py
│   └── validation.py
├── SKILL.md
├── README.md
└── LICENSE
```

## Related Docs

- `SKILL.md`
- `references/workflow.md`
- `references/job-posting.md`
- `references/writing.md`
- `references/output-rules.md`
- `references/evaluation.md`
- `references/revision.md`
- `references/few-shot.md`
