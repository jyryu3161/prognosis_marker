# GUI Desktop App Planning Document

> **Summary**: 스크립트 기반 Prognosis Marker 플랫폼을 Mac/Linux/Windows 크로스플랫폼 데스크톱 GUI 애플리케이션으로 전환
>
> **Project**: prognosis_marker
> **Author**: User
> **Date**: 2026-02-17
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

현재 Prognosis Marker 플랫폼은 R 스크립트(`Main_Binary.R`, `Main_Survival.R`)와 YAML 설정 파일 기반으로 동작한다. 사용자는 YAML을 직접 편집하고, 커맨드라인에서 스크립트를 실행해야 한다. 이를 **크로스플랫폼 데스크톱 GUI 애플리케이션**으로 전환하여:

- 비개발자(연구자, 임상의)도 쉽게 사용할 수 있도록 한다
- 파라미터 입력을 직관적인 UI 컨트롤(Radio Button, Checkbox, Slider 등)로 제공한다
- Mac, Linux, Windows 에서 네이티브 앱처럼 동작한다

### 1.2 Background

- 현재 Streamlit 웹 앱(`streamlit_app.py`)이 있지만, 서버 실행이 필요하고 배포가 복잡하다
- 34개 TCGA 데이터셋에 대한 사전 설정 파일이 있어, 프리셋 선택 기능이 유용하다
- R 분석 엔진은 그대로 유지하면서 프론트엔드만 GUI로 교체하는 전략이 필요하다
- pixi 기반 환경 관리를 활용하여 R 런타임 의존성을 해결한다

### 1.3 Related Documents

- README.md (현재 플랫폼 사용법)
- config/example_analysis.yaml (설정 파일 구조)
- streamlit_app.py (기존 웹 UI 참조)

---

## 2. Scope

### 2.1 In Scope

- [ ] 크로스플랫폼 데스크톱 앱 프레임워크 선정 및 구축
- [ ] YAML 파라미터를 GUI 컨트롤로 매핑 (Radio, Checkbox, Slider, Dropdown 등)
- [ ] Binary/Survival 분석 실행 및 실시간 진행 상황 표시
- [ ] 결과 시각화 (ROC 곡선, KM 곡선 등) 앱 내 표시
- [ ] TCGA 프리셋 설정 로드/저장 기능
- [ ] Evidence 기반 필터링 (Open Targets) 옵션 통합
- [ ] 결과 파일 내보내기 (CSV, TIFF, SVG)

### 2.2 Out of Scope

- R 분석 엔진 자체의 로직 변경
- 클라우드 배포 / 웹 서비스 형태
- 실시간 협업 기능
- 새로운 통계 분석 방법 추가

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | **분석 타입 선택**: Binary / Survival을 Radio Button으로 선택 | High | Pending |
| FR-02 | **데이터 파일 로드**: 파일 탐색기로 CSV 파일 선택 | High | Pending |
| FR-03 | **컬럼 매핑**: 데이터 로드 후 컬럼 목록을 Dropdown으로 표시하여 sample_id, outcome, time_variable 등 매핑 | High | Pending |
| FR-04 | **통계 파라미터 설정**: split_prop(Slider 0.5~0.9), num_seed(Number Input), freq(Number Input) | High | Pending |
| FR-05 | **P-value 필터링 옵션**: Checkbox로 활성화, p_adjust_method(Radio: FDR/Bonferroni), p_threshold(Number), top_k(Number) | Medium | Pending |
| FR-06 | **Feature Include/Exclude**: 컬럼 목록에서 Checkbox 다중 선택 | Medium | Pending |
| FR-07 | **Evidence 필터링**: Checkbox로 활성화, score_threshold(Slider), gene_file(File Picker) | Medium | Pending |
| FR-08 | **Survival 전용 파라미터**: horizon(Number Input) - Survival 선택 시만 표시 | High | Pending |
| FR-09 | **출력 디렉토리 선택**: 폴더 탐색기로 결과 저장 경로 지정 | High | Pending |
| FR-10 | **TCGA 프리셋 로드**: 34개 사전 설정 Dropdown 선택 시 파라미터 자동 입력 | Medium | Pending |
| FR-11 | **분석 실행 및 진행 표시**: Run 버튼 → Progress Bar + 실시간 로그 출력 | High | Pending |
| FR-12 | **결과 뷰어**: 생성된 ROC 곡선, KM 곡선, Variable Importance 플롯을 앱 내 탭으로 표시 | High | Pending |
| FR-13 | **설정 저장/불러오기**: 현재 파라미터를 YAML로 내보내기/가져오기 | Medium | Pending |
| FR-14 | **성능 최적화 옵션**: max_candidates_per_step, prescreen_seeds를 Advanced 섹션에 Number Input으로 제공 | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | 분석 실행 중 UI 블로킹 없음 (백그라운드 프로세스) | 분석 중 UI 조작 테스트 |
| Compatibility | Mac (Intel/ARM), Linux (x86_64), Windows (x86_64) 지원 | 3개 OS에서 빌드/실행 테스트 |
| Usability | 비개발자가 5분 내 첫 분석 실행 가능 | 사용성 테스트 |
| Install Size | 앱 번들 500MB 이하 (R 런타임 제외) | 빌드 결과 측정 |
| Startup Time | 앱 시작 5초 이내 | 실측 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] Mac, Linux, Windows 3개 플랫폼에서 앱 빌드 및 실행 확인
- [ ] 모든 YAML 파라미터가 GUI 컨트롤로 매핑됨
- [ ] Binary/Survival 분석 실행 후 결과 파일 정상 생성
- [ ] 결과 시각화가 앱 내에서 표시됨
- [ ] 기존 YAML 설정 파일 호환성 유지

### 4.2 Quality Criteria

- [ ] 3개 OS에서 E2E 테스트 통과
- [ ] 분석 실행 중 UI Freeze 없음
- [ ] 에러 발생 시 사용자 친화적 메시지 표시

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| R 런타임 번들링 복잡성 | High | High | pixi를 활용한 환경 관리, 또는 시스템 R 경로 자동 탐지 |
| 크로스플랫폼 빌드 파이프라인 복잡성 | Medium | Medium | CI/CD로 3개 OS 자동 빌드, GitHub Actions 활용 |
| 대용량 데이터(수만 유전자) 로드 시 UI 지연 | Medium | Medium | 비동기 로딩 + 가상 스크롤링 적용 |
| R 프로세스 크래시 시 앱 복구 | Medium | Low | 별도 프로세스로 R 실행, 타임아웃 및 재시도 로직 |
| 사용자별 R 패키지 의존성 미설치 | High | Medium | 첫 실행 시 의존성 자동 검증/설치 마법사 제공 |

---

## 6. Architecture Considerations

### 6.1 GUI 프레임워크 선택

| Option | 장점 | 단점 | 적합성 |
|--------|------|------|:------:|
| **Tauri + React** | 경량(~10MB), Rust 기반 보안, 웹 기술 활용 | Rust 빌드 환경 필요 | ★★★★☆ |
| **Electron + React** | 성숙한 에코시스템, 풍부한 라이브러리 | 무거움(~150MB+), 메모리 사용량 큼 | ★★★☆☆ |
| **R Shiny + Electron** | R 네이티브, 기존 코드 재사용 극대화 | Electron 의존, R 서버 번들링 복잡 | ★★☆☆☆ |
| **Python (PyQt6/PySide6)** | 데이터 과학 에코시스템, Python-R 연동 | 네이티브 룩앤필 부족, 배포 복잡 | ★★★☆☆ |
| **Wails (Go + Web)** | 경량, Go 백엔드, 빌드 단순 | Go 생태계 R 연동 지원 부족 | ★★☆☆☆ |

**추천: Tauri + React (TypeScript)**

- 경량 바이너리로 배포 용이
- React 생태계의 풍부한 UI 컴포넌트
- Rust backend에서 R 프로세스를 child process로 관리
- IPC를 통한 프론트엔드-백엔드 통신

### 6.2 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri Desktop App                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │              React Frontend (WebView)              │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │  │
│  │  │ Analysis │ │ Parameter│ │   Result Viewer    │ │  │
│  │  │ Type     │ │ Form     │ │ (Plots, Tables)    │ │  │
│  │  │ Selector │ │          │ │                    │ │  │
│  │  └──────────┘ └──────────┘ └───────────────────┘ │  │
│  └───────────────────┬───────────────────────────────┘  │
│                      │ Tauri IPC (invoke)                │
│  ┌───────────────────┴───────────────────────────────┐  │
│  │              Rust Backend (Tauri Core)              │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │  │
│  │  │ Config   │ │ R Process│ │   File System      │ │  │
│  │  │ Manager  │ │ Manager  │ │   Manager          │ │  │
│  │  │ (YAML)   │ │ (spawn)  │ │   (read/write)     │ │  │
│  │  └──────────┘ └──────────┘ └───────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                      │ Child Process                     │
│  ┌───────────────────┴───────────────────────────────┐  │
│  │           R Runtime (Rscript)                      │  │
│  │  Main_Binary.R / Main_Survival.R                   │  │
│  │  (기존 분석 엔진 그대로 사용)                          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 6.3 파라미터-UI 컨트롤 매핑

| Parameter | Type | UI Control | Section |
|-----------|------|------------|---------|
| Analysis Type | binary/survival | **Radio Button** (2개) | Main |
| data_file | file path | **File Picker** (CSV 필터) | Data |
| sample_id | column name | **Dropdown** (데이터 로드 후 동적) | Column Mapping |
| outcome (binary) | column name | **Dropdown** | Column Mapping |
| event (survival) | column name | **Dropdown** | Column Mapping |
| time_variable | column name | **Dropdown** | Column Mapping |
| split_prop | 0.5~0.9 | **Slider** + Number (기본값 0.7) | Parameters |
| num_seed | 10~1000 | **Number Input** (기본값 100) | Parameters |
| freq | 1~100 | **Number Input** (기본값 50) | Parameters |
| horizon | 1~20 | **Number Input** (기본값 5) | Parameters (Survival Only) |
| p-value 필터링 활성화 | boolean | **Checkbox** | Advanced |
| p_adjust_method | fdr/bonferroni | **Radio Button** (2개) | Advanced |
| p_threshold | 0.001~1.0 | **Number Input** (기본값 0.05) | Advanced |
| top_k | number | **Number Input** (optional) | Advanced |
| include features | column list | **Checkbox List** (다중 선택) | Feature Selection |
| exclude features | column list | **Checkbox List** (다중 선택) | Feature Selection |
| evidence 필터링 활성화 | boolean | **Checkbox** | Evidence |
| evidence gene_file | file path | **File Picker** | Evidence |
| score_threshold | 0.0~1.0 | **Slider** + Number (기본값 0.1) | Evidence |
| output_dir | directory path | **Folder Picker** | Output |
| TCGA Preset | preset name | **Dropdown** (34개 옵션) | Preset |
| max_candidates_per_step | number | **Number Input** | Advanced (Performance) |
| prescreen_seeds | number | **Number Input** | Advanced (Performance) |

### 6.4 UI 레이아웃 구조

```
┌──────────────────────────────────────────────────────┐
│  Prognosis Marker                          [─][□][×] │
├──────────────────────────────────────────────────────┤
│  [Setup]  [Results]  [Settings]                      │
├──────────────────────────────────────────────────────┤
│ ┌─ Analysis Type ─────────────────────────────────┐  │
│ │  (●) Binary Classification  ( ) Survival        │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌─ Data ──────────────────────────────────────────┐  │
│ │  Preset: [TCGA_BRCA ▼] or [Load Custom CSV...] │  │
│ │  File: /path/to/data.csv              [Browse]  │  │
│ │  Rows: 1,097  Columns: 20,531                   │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌─ Column Mapping ────────────────────────────────┐  │
│ │  Sample ID:    [sample      ▼]                  │  │
│ │  Outcome:      [OS          ▼]                  │  │
│ │  Time Variable:[OS.year     ▼]  (Survival only) │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌─ Parameters ────────────────────────────────────┐  │
│ │  Train/Test Split: [===●=====] 0.70             │  │
│ │  Iterations:       [100    ]                    │  │
│ │  Frequency:        [50     ] %                  │  │
│ │  Horizon (years):  [5      ]  (Survival only)   │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ▶ Advanced Options                                   │
│ ▶ Feature Selection                                  │
│ ▶ Evidence Filtering                                 │
│                                                      │
│ ┌─ Output ────────────────────────────────────────┐  │
│ │  Directory: /path/to/results         [Browse]   │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│        [Save Config]    [ ▶ Run Analysis ]           │
│                                                      │
│ ┌─ Progress ──────────────────────────────────────┐  │
│ │  [████████░░░░░░░░░] 45% - Iteration 45/100     │  │
│ │  > Running stepwise selection...                 │  │
│ └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 6.5 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| GUI Framework | Tauri / Electron / PyQt6 | **Tauri 2.0** | 경량 바이너리, 크로스플랫폼, 보안 |
| Frontend | React / Vue / Svelte | **React + TypeScript** | 풍부한 에코시스템, 컴포넌트 라이브러리 |
| UI Library | shadcn/ui / MUI / Ant Design | **shadcn/ui** | 경량, 커스터마이징 용이, Tailwind 기반 |
| Styling | Tailwind / CSS Modules | **Tailwind CSS** | 빠른 개발, 일관된 디자인 |
| State Management | Zustand / Jotai / Context | **Zustand** | 경량, 간결한 API |
| R Integration | Child Process / rpy2 / API | **Child Process (spawn)** | 격리, 기존 스크립트 무변경 |
| Config Format | JSON / YAML / TOML | **YAML** (기존 호환) | 기존 설정 파일 그대로 사용 |
| Build/Package | Tauri CLI / electron-builder | **Tauri CLI** | 내장 빌드, 자동 업데이트 지원 |

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] R 스크립트 네이밍: `Main_Binary.R`, `Main_Survival.R` (PascalCase prefix)
- [x] YAML 설정 파일: `config/TCGA_{TYPE}_analysis.yaml`
- [x] 결과 디렉토리 구조: `results/{type}/{analysis}/`
- [ ] TypeScript/React 코드 컨벤션 (신규 정의 필요)
- [ ] 테스트 컨벤션 (신규 정의 필요)

### 7.2 Conventions to Define

| Category | To Define | Priority |
|----------|-----------|:--------:|
| **Folder structure** | `src-tauri/` (Rust), `src/` (React), `r-engine/` (R scripts) | High |
| **Naming** | React: PascalCase 컴포넌트, camelCase 함수/변수 | High |
| **Component structure** | Feature-based: `src/features/{feature}/` | Medium |
| **IPC naming** | `{domain}:{action}` (e.g., `analysis:run`, `config:load`) | Medium |
| **Error handling** | Rust → Frontend 에러 전파 패턴 | Medium |

### 7.3 Environment & Dependencies

| Item | Purpose | Scope |
|------|---------|-------|
| Rust toolchain | Tauri backend 빌드 | Build |
| Node.js 20+ | React frontend 빌드 | Build |
| R 4.3+ | 분석 엔진 실행 | Runtime |
| pixi | R 패키지 환경 관리 | Runtime |

---

## 8. Implementation Phases (High-Level)

| Phase | Description | Estimated Effort |
|-------|-------------|:---:|
| **Phase 1** | Tauri + React 프로젝트 초기 설정, 기본 레이아웃 | Small |
| **Phase 2** | 파라미터 입력 폼 구현 (모든 UI 컨트롤) | Medium |
| **Phase 3** | Rust ↔ R 프로세스 연동 (IPC, 실행, 로그 스트리밍) | Medium |
| **Phase 4** | 결과 뷰어 (플롯 표시, CSV 테이블) | Medium |
| **Phase 5** | 프리셋 관리, 설정 저장/불러오기 | Small |
| **Phase 6** | 크로스플랫폼 빌드 및 패키징 | Medium |
| **Phase 7** | 테스트 및 폴리싱 | Small |

---

## 9. Next Steps

1. [ ] Design 문서 작성 (`gui-desktop-app.design.md`)
2. [ ] Tauri 2.0 + React 프로젝트 스캐폴딩
3. [ ] 프로토타입: 파라미터 폼 → R 실행 → 결과 표시 E2E
4. [ ] 크로스플랫폼 빌드 파이프라인 검증

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | Initial draft | User |
