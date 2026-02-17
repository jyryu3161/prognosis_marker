# GUI Desktop App Design Document

> **Summary**: Tauri 2.0 + React 기반 크로스플랫폼 데스크톱 GUI 앱 상세 설계
>
> **Project**: prognosis_marker
> **Author**: User
> **Date**: 2026-02-17
> **Status**: Draft
> **Planning Doc**: [gui-desktop-app.plan.md](../../01-plan/features/gui-desktop-app.plan.md)

---

## 1. Overview

### 1.1 Design Goals

- 기존 R 분석 엔진(`Main_Binary.R`, `Main_Survival.R`)을 **무변경**으로 유지하면서 GUI 래퍼 제공
- 모든 YAML 설정 파라미터를 직관적인 UI 컨트롤로 1:1 매핑
- Tauri IPC를 통한 비동기 R 프로세스 실행 및 실시간 로그 스트리밍
- Mac/Linux/Windows 네이티브 바이너리 빌드

### 1.2 Design Principles

- **Separation of Concerns**: Frontend(UI) ↔ Rust Backend(IPC/Process) ↔ R Engine(분석) 3계층 분리
- **Zero R Modification**: R 스크립트는 기존 `--config` 인자 방식 그대로 사용
- **Config Compatibility**: 생성되는 YAML은 기존 설정 파일과 100% 호환
- **Progressive Disclosure**: 기본 파라미터 → Advanced → Evidence 순으로 점진적 노출

---

## 2. Architecture

### 2.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Tauri 2.0 Desktop App                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              React Frontend (WebView2)                  │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │ SetupPage│  │ ResultsPage  │  │  SettingsPage   │  │  │
│  │  │          │  │              │  │                 │  │  │
│  │  │AnalysisT.│  │ PlotViewer   │  │ R Path Config   │  │  │
│  │  │DataLoader│  │ TableViewer  │  │ Default Params  │  │  │
│  │  │ColMapping│  │ LogConsole   │  │ Theme/Language  │  │  │
│  │  │ParamForm │  │              │  │                 │  │  │
│  │  │AdvOpts   │  │              │  │                 │  │  │
│  │  │RunButton │  │              │  │                 │  │  │
│  │  └──────────┘  └──────────────┘  └─────────────────┘  │  │
│  │                                                        │  │
│  │  Zustand Store: analysisStore, configStore, uiStore    │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│                    Tauri IPC (invoke / listen)                │
│                           │                                  │
│  ┌────────────────────────┴───────────────────────────────┐  │
│  │              Rust Backend (src-tauri/)                  │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │ config.rs    │  │ analysis.rs  │  │ fs_ops.rs   │  │  │
│  │  │              │  │              │  │             │  │  │
│  │  │ load_yaml()  │  │ run()        │  │ pick_file() │  │  │
│  │  │ save_yaml()  │  │ cancel()     │  │ pick_dir()  │  │  │
│  │  │ list_presets()│  │ get_status() │  │ read_csv()  │  │  │
│  │  │ validate()   │  │ stream_log() │  │ list_plots()│  │  │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐                    │  │
│  │  │ r_runtime.rs │  │ presets.rs   │                    │  │
│  │  │              │  │              │                    │  │
│  │  │ detect_r()   │  │ TCGA presets │                    │  │
│  │  │ detect_pixi()│  │ load/save    │                    │  │
│  │  │ check_deps() │  │              │                    │  │
│  │  └──────────────┘  └──────────────┘                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                  │
│                    Child Process (spawn)                      │
│                           │                                  │
│  ┌────────────────────────┴───────────────────────────────┐  │
│  │              R Runtime (Rscript / pixi run)             │  │
│  │                                                        │  │
│  │  Main_Binary.R --config=/tmp/gui_config_xxxx.yaml      │  │
│  │  Main_Survival.R --config=/tmp/gui_config_xxxx.yaml    │  │
│  │                                                        │  │
│  │  stdout → progress events → Frontend Progress Bar      │  │
│  │  stderr → log events → Frontend Log Console            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
[User Input (GUI)]
      │
      ▼
[Zustand Store] ──build──▶ [AnalysisConfig object]
      │                            │
      │                    serialize to YAML
      │                            │
      ▼                            ▼
[Tauri invoke]              [/tmp/gui_config_xxxx.yaml]
      │                            │
      ▼                            │
[Rust: analysis::run()] ──spawn──▶ [Rscript --config=...]
      │                            │
      │◀──── stdout/stderr ────────┘
      │
      ▼
[Tauri Event: "analysis://progress"]
[Tauri Event: "analysis://log"]
[Tauri Event: "analysis://complete"]
      │
      ▼
[Frontend: ResultsPage]
      │
      ▼
[PlotViewer: read output_dir/figures/*.tiff|svg]
[TableViewer: read output_dir/*.csv]
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| React Frontend | Tauri IPC API | 백엔드 통신 |
| React Frontend | Zustand | 상태 관리 |
| React Frontend | shadcn/ui + Tailwind | UI 컴포넌트 |
| Rust Backend | serde_yaml | YAML 직렬화 |
| Rust Backend | tauri::process::Command | R 프로세스 실행 |
| Rust Backend | csv crate | CSV 헤더 파싱 |
| R Engine | pixi / system R | 런타임 환경 |
| R Engine | YAML config file | 입력 파라미터 |

---

## 3. Data Model

### 3.1 Core Types (TypeScript)

```typescript
// src/types/analysis.ts

/** 분석 타입 */
type AnalysisType = "binary" | "survival";

/** P-value 보정 방법 */
type PAdjustMethod = "fdr" | "bonferroni";

/** 분석 실행 상태 */
type AnalysisStatus = "idle" | "running" | "completed" | "failed" | "cancelled";

/** 공통 분석 설정 */
interface BaseConfig {
  dataFile: string;
  sampleId: string;
  timeVariable: string | null;
  splitProp: number;        // 0.5 ~ 0.9
  numSeed: number;          // 10 ~ 1000
  outputDir: string;
  freq: number;             // 1 ~ 100
  exclude: string[];
  include: string[];
  // Advanced (optional)
  maxCandidatesPerStep: number | null;
  prescreenSeeds: number | null;
  topK: number | null;
  pAdjustMethod: PAdjustMethod;
  pThreshold: number;       // 0.001 ~ 1.0
  // Evidence (optional)
  evidence: EvidenceConfig | null;
}

/** Binary 전용 설정 */
interface BinaryConfig extends BaseConfig {
  type: "binary";
  outcome: string;           // binary 결과 컬럼
}

/** Survival 전용 설정 */
interface SurvivalConfig extends BaseConfig {
  type: "survival";
  event: string;             // 이벤트 컬럼 (0/1)
  horizon: number;           // 평가 시점 (years)
}

/** 통합 분석 설정 */
type AnalysisConfig = BinaryConfig | SurvivalConfig;

/** Evidence 기반 필터링 */
interface EvidenceConfig {
  geneFile: string;
  scoreThreshold: number;    // 0.0 ~ 1.0
  source: string;
  diseaseName: string;
  efoId: string;
}

/** 데이터 파일 메타정보 */
interface DataFileInfo {
  path: string;
  rowCount: number;
  columns: string[];         // 전체 컬럼 목록
  preview: Record<string, string[]>;  // 컬럼별 처음 5개 값
}

/** TCGA 프리셋 */
interface TcgaPreset {
  id: string;                // e.g., "TCGA_BRCA"
  label: string;             // e.g., "Breast Cancer (BRCA)"
  configPath: string;        // config/ 내 YAML 경로
  hasEvidence: boolean;      // opentargets 설정 존재 여부
}
```

### 3.2 분석 결과 Types

```typescript
// src/types/results.ts

/** 분석 실행 결과 */
interface AnalysisResult {
  status: AnalysisStatus;
  outputDir: string;
  plots: PlotFile[];
  aucData: AucIteration[];
  duration: number;          // seconds
  error: string | null;
}

/** 플롯 파일 */
interface PlotFile {
  name: string;              // e.g., "ROCcurve"
  tiffPath: string;          // .tiff 경로
  svgPath: string;           // .svg 경로
  category: "roc" | "importance" | "kaplan_meier" | "time_auc" | "dca" | "other";
}

/** AUC 반복 결과 */
interface AucIteration {
  iteration: number;
  selectedGenes: string[];
  trainAuc: number;
  testAuc: number;
}

/** 실시간 진행 이벤트 */
interface ProgressEvent {
  type: "start" | "iteration" | "stepwise_start" | "stepwise_log" | "stepwise_done" | "complete" | "error";
  current: number;
  total: number;
  message: string;
}
```

### 3.3 Store Types

```typescript
// src/types/store.ts

/** 분석 스토어 상태 */
interface AnalysisStore {
  // State
  analysisType: AnalysisType;
  config: Partial<AnalysisConfig>;
  dataInfo: DataFileInfo | null;
  status: AnalysisStatus;
  progress: { current: number; total: number; message: string };
  result: AnalysisResult | null;
  logs: string[];

  // Actions
  setAnalysisType: (type: AnalysisType) => void;
  updateConfig: (partial: Partial<AnalysisConfig>) => void;
  setDataInfo: (info: DataFileInfo) => void;
  runAnalysis: () => Promise<void>;
  cancelAnalysis: () => void;
  resetAll: () => void;
}

/** 설정 스토어 */
interface ConfigStore {
  rPath: string | null;
  pixiPath: string | null;
  usePixi: boolean;
  presets: TcgaPreset[];

  detectRuntime: () => Promise<void>;
  loadPresets: () => Promise<void>;
  loadPresetConfig: (presetId: string) => Promise<Partial<AnalysisConfig>>;
  saveConfigToFile: (config: AnalysisConfig, path: string) => Promise<void>;
  loadConfigFromFile: (path: string) => Promise<Partial<AnalysisConfig>>;
}
```

---

## 4. IPC Specification (Tauri Commands)

### 4.1 Command List

| Command | Direction | Description | Returns |
|---------|-----------|-------------|---------|
| `config:load_yaml` | FE → BE | YAML 설정 파일 로드 | `AnalysisConfig` |
| `config:save_yaml` | FE → BE | 현재 설정을 YAML로 저장 | `string` (path) |
| `config:validate` | FE → BE | 설정 유효성 검증 | `ValidationResult` |
| `config:list_presets` | FE → BE | TCGA 프리셋 목록 | `TcgaPreset[]` |
| `config:load_preset` | FE → BE | 특정 프리셋 로드 | `AnalysisConfig` |
| `fs:pick_file` | FE → BE | 파일 탐색기 열기 (CSV 필터) | `string \| null` |
| `fs:pick_directory` | FE → BE | 폴더 탐색기 열기 | `string \| null` |
| `fs:read_csv_header` | FE → BE | CSV 파일 헤더 + 미리보기 읽기 | `DataFileInfo` |
| `fs:list_output_plots` | FE → BE | 결과 디렉토리의 플롯 파일 목록 | `PlotFile[]` |
| `fs:read_image` | FE → BE | 이미지를 base64로 읽기 | `string` (base64) |
| `analysis:run` | FE → BE | 분석 실행 (비동기) | `void` |
| `analysis:cancel` | FE → BE | 실행 중인 분석 취소 | `void` |
| `analysis:get_status` | FE → BE | 현재 분석 상태 조회 | `AnalysisStatus` |
| `runtime:detect` | FE → BE | R/pixi 경로 자동 탐지 | `RuntimeInfo` |
| `runtime:check_deps` | FE → BE | R 패키지 의존성 확인 | `DepCheckResult` |

### 4.2 Event List (Backend → Frontend)

| Event | Payload | Description |
|-------|---------|-------------|
| `analysis://progress` | `ProgressEvent` | 진행 상황 업데이트 |
| `analysis://log` | `{ line: string }` | 실시간 로그 라인 |
| `analysis://complete` | `AnalysisResult` | 분석 완료 |
| `analysis://error` | `{ message: string, code: string }` | 에러 발생 |

### 4.3 Key Command Detail

#### `analysis:run`

```rust
// src-tauri/src/commands/analysis.rs

#[tauri::command]
async fn analysis_run(
    app: tauri::AppHandle,
    config: AnalysisConfig,
) -> Result<(), String> {
    // 1. config → YAML 직렬화 → 임시 파일 작성
    let tmp_config = write_temp_yaml(&config)?;

    // 2. R 실행 경로 결정 (pixi or system Rscript)
    let r_cmd = resolve_r_command(&app)?;

    // 3. 분석 스크립트 선택
    let script = match config.analysis_type {
        "binary" => "Main_Binary.R",
        "survival" => "Main_Survival.R",
    };

    // 4. Child process spawn
    let child = Command::new(r_cmd)
        .args(&[script, &format!("--config={}", tmp_config)])
        .current_dir(&config.workdir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;

    // 5. stdout/stderr 비동기 읽기 → Tauri 이벤트 emit
    tokio::spawn(async move {
        stream_output(app, child).await;
    });

    Ok(())
}
```

#### `fs:read_csv_header`

```rust
#[tauri::command]
async fn fs_read_csv_header(path: String) -> Result<DataFileInfo, String> {
    // 1. CSV 파일 열기
    // 2. 헤더 행 읽기 → columns
    // 3. 처음 5행 읽기 → preview
    // 4. 전체 행 수 카운트 → row_count
    // 5. DataFileInfo 반환
}
```

---

## 5. UI/UX Design

### 5.1 Page Structure

```
App
├── Layout (Sidebar + Content)
│   ├── Sidebar Navigation
│   │   ├── Setup (기본 선택)
│   │   ├── Results
│   │   └── Settings
│   │
│   └── Content Area
│       ├── SetupPage
│       │   ├── AnalysisTypeSelector
│       │   ├── DataSection
│       │   │   ├── PresetSelector
│       │   │   ├── FilePickerField
│       │   │   └── DataPreview
│       │   ├── ColumnMappingSection
│       │   │   ├── DropdownField × 3~4
│       │   │   └── (conditional by analysis type)
│       │   ├── ParametersSection
│       │   │   ├── SliderField (split_prop)
│       │   │   ├── NumberField (num_seed)
│       │   │   ├── NumberField (freq)
│       │   │   └── NumberField (horizon) [survival only]
│       │   ├── AdvancedOptionsAccordion
│       │   │   ├── PValueFilterGroup
│       │   │   │   ├── Checkbox (enable)
│       │   │   │   ├── RadioGroup (method)
│       │   │   │   ├── NumberField (threshold)
│       │   │   │   └── NumberField (top_k)
│       │   │   └── PerformanceGroup
│       │   │       ├── NumberField (max_candidates)
│       │   │       └── NumberField (prescreen_seeds)
│       │   ├── FeatureSelectionAccordion
│       │   │   ├── CheckboxList (include)
│       │   │   └── CheckboxList (exclude)
│       │   ├── EvidenceFilterAccordion
│       │   │   ├── Checkbox (enable)
│       │   │   ├── FilePickerField (gene_file)
│       │   │   └── SliderField (score_threshold)
│       │   ├── OutputSection
│       │   │   └── DirectoryPickerField
│       │   ├── ActionBar
│       │   │   ├── SaveConfigButton
│       │   │   ├── LoadConfigButton
│       │   │   └── RunAnalysisButton
│       │   └── ProgressPanel
│       │       ├── ProgressBar
│       │       └── LogConsole
│       │
│       ├── ResultsPage
│       │   ├── PlotTabs
│       │   │   ├── ROC Curve Tab
│       │   │   ├── Variable Importance Tab
│       │   │   ├── KM Curve Tab [survival]
│       │   │   ├── Time AUC Tab [survival]
│       │   │   └── DCA Tab [binary]
│       │   ├── AucTable
│       │   └── ExportButtons
│       │
│       └── SettingsPage
│           ├── RuntimeConfig
│           │   ├── R path detection/override
│           │   └── pixi path detection/override
│           └── AppPreferences
│               └── Default output directory
```

### 5.2 User Flow

```
앱 시작
  │
  ▼
[Runtime Check] ──실패──▶ [Settings: R 경로 설정]
  │ 성공                        │
  ▼                            ▼
[Setup Page]◀──────────────────┘
  │
  ├─▶ Preset 선택 ──▶ 파라미터 자동 입력
  │        또는
  ├─▶ CSV 파일 선택 ──▶ 컬럼 목록 로드 ──▶ 컬럼 매핑
  │
  ▼
[파라미터 조정]
  │
  ├─▶ [Save Config] ──▶ YAML 파일 저장
  │
  ▼
[Run Analysis] ──▶ [Progress Bar + Log]
  │                       │
  │                  [Cancel] 가능
  │                       │
  ▼                       ▼
[완료] ──자동──▶ [Results Page]
  │
  ├─▶ 플롯 뷰어 (탭 전환)
  ├─▶ AUC 테이블
  └─▶ 파일 내보내기
```

### 5.3 Component List

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `App` | `src/App.tsx` | 루트 레이아웃, 라우팅 |
| `Sidebar` | `src/components/layout/Sidebar.tsx` | 페이지 네비게이션 |
| `SetupPage` | `src/pages/SetupPage.tsx` | 메인 설정 페이지 |
| `ResultsPage` | `src/pages/ResultsPage.tsx` | 결과 표시 페이지 |
| `SettingsPage` | `src/pages/SettingsPage.tsx` | 앱 설정 페이지 |
| `AnalysisTypeSelector` | `src/components/setup/AnalysisTypeSelector.tsx` | Radio: Binary/Survival |
| `PresetSelector` | `src/components/setup/PresetSelector.tsx` | TCGA 프리셋 Dropdown |
| `FilePickerField` | `src/components/shared/FilePickerField.tsx` | 파일 선택 + 경로 표시 |
| `DirectoryPickerField` | `src/components/shared/DirectoryPickerField.tsx` | 폴더 선택 |
| `DataPreview` | `src/components/setup/DataPreview.tsx` | CSV 미리보기 테이블 |
| `ColumnMappingSection` | `src/components/setup/ColumnMappingSection.tsx` | 컬럼 Dropdown 매핑 |
| `ParametersSection` | `src/components/setup/ParametersSection.tsx` | 기본 파라미터 폼 |
| `SliderField` | `src/components/shared/SliderField.tsx` | Slider + Number 표시 |
| `NumberField` | `src/components/shared/NumberField.tsx` | 숫자 입력 + 범위 검증 |
| `AdvancedOptionsAccordion` | `src/components/setup/AdvancedOptionsAccordion.tsx` | 접힌 고급 옵션 |
| `PValueFilterGroup` | `src/components/setup/PValueFilterGroup.tsx` | P-value 필터링 그룹 |
| `FeatureSelectionAccordion` | `src/components/setup/FeatureSelectionAccordion.tsx` | 피처 선택 체크리스트 |
| `EvidenceFilterAccordion` | `src/components/setup/EvidenceFilterAccordion.tsx` | Evidence 필터 옵션 |
| `ActionBar` | `src/components/setup/ActionBar.tsx` | 실행/저장/불러오기 버튼 |
| `ProgressPanel` | `src/components/setup/ProgressPanel.tsx` | Progress Bar + Log |
| `LogConsole` | `src/components/shared/LogConsole.tsx` | 스크롤 가능 로그 출력 |
| `PlotViewer` | `src/components/results/PlotViewer.tsx` | 이미지 뷰어 (확대/축소) |
| `PlotTabs` | `src/components/results/PlotTabs.tsx` | 플롯 탭 전환 |
| `AucTable` | `src/components/results/AucTable.tsx` | AUC 결과 테이블 |
| `RuntimeConfig` | `src/components/settings/RuntimeConfig.tsx` | R/pixi 경로 설정 |

---

## 6. Error Handling

### 6.1 Error Categories

| Category | Code | Cause | UI Handling |
|----------|------|-------|-------------|
| `RUNTIME_NOT_FOUND` | E001 | R / pixi 경로를 찾을 수 없음 | Settings 페이지로 안내, 설치 가이드 링크 |
| `DEPS_MISSING` | E002 | R 패키지 미설치 | 누락 패키지 목록 표시, 설치 명령 제공 |
| `FILE_NOT_FOUND` | E003 | CSV/YAML 파일 없음 | 파일 다시 선택 안내 |
| `CSV_PARSE_ERROR` | E004 | CSV 파싱 실패 (인코딩, 형식) | 에러 위치 표시, 파일 형식 안내 |
| `CONFIG_INVALID` | E005 | 설정 검증 실패 (필수값 누락) | 해당 필드 하이라이트 + 에러 메시지 |
| `ANALYSIS_FAILED` | E006 | R 스크립트 실행 오류 | 로그 콘솔에 에러 출력, 재실행 안내 |
| `ANALYSIS_TIMEOUT` | E007 | 분석 시간 초과 (10분) | 타임아웃 알림, num_seed 줄이기 제안 |
| `PERMISSION_DENIED` | E008 | 파일/디렉토리 권한 없음 | 다른 경로 선택 안내 |

### 6.2 Error Flow (Rust → Frontend)

```rust
// src-tauri/src/error.rs

#[derive(Debug, Serialize)]
struct AppError {
    code: String,       // "E001" ~ "E008"
    message: String,    // 사용자 친화적 메시지
    details: Option<String>,  // 기술적 세부사항 (로그용)
}

// Tauri command에서 Result<T, AppError> 반환
// Frontend에서 try-catch로 처리 → toast 알림 표시
```

### 6.3 Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| `dataFile` | 파일 존재 + .csv 확장자 | "유효한 CSV 파일을 선택해주세요" |
| `sampleId` | 컬럼 목록에 존재 | "선택한 컬럼이 데이터에 없습니다" |
| `outcome` / `event` | 값이 0/1만 포함 | "결과 컬럼은 0과 1만 포함해야 합니다" |
| `splitProp` | 0.5 ≤ x ≤ 0.9 | "분할 비율은 0.5~0.9 범위여야 합니다" |
| `numSeed` | 10 ≤ x ≤ 1000, 정수 | "반복 횟수는 10~1000 범위의 정수여야 합니다" |
| `freq` | 1 ≤ x ≤ 100, 정수 | "빈도 임계값은 1~100 범위의 정수여야 합니다" |
| `horizon` | 1 ≤ x ≤ 20 | "평가 시점은 1~20년 범위여야 합니다" |
| `outputDir` | 디렉토리 존재 + 쓰기 권한 | "출력 경로에 쓰기 권한이 없습니다" |

---

## 7. Security Considerations

- [x] 파일 경로 검증: path traversal 방지 (Tauri scope로 제한)
- [x] R 프로세스 격리: Child process로 실행, 타임아웃 적용
- [x] 사용자 입력 살균: YAML 직렬화 시 injection 방지 (serde_yaml)
- [ ] 앱 자동 업데이트: Tauri updater로 서명된 업데이트만 허용
- [x] 로컬 전용: 네트워크 통신 없음 (Open Targets 제외)

---

## 8. Test Plan

### 8.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit Test (FE) | Store logic, config 변환, 유효성 검증 | Vitest |
| Unit Test (BE) | YAML 직렬화, 경로 탐지, CSV 파싱 | Rust #[test] |
| Component Test | 개별 UI 컴포넌트 렌더링/인터랙션 | Vitest + Testing Library |
| Integration Test | IPC 명령 호출 → 응답 검증 | Tauri test utils |
| E2E Test | 전체 분석 워크플로우 | Playwright (WebDriver) |

### 8.2 Key Test Cases

- [ ] **Happy Path - Binary**: 파일 선택 → 컬럼 매핑 → 파라미터 설정 → 실행 → 결과 표시
- [ ] **Happy Path - Survival**: 동일 플로우, Survival 전용 필드 포함
- [ ] **Preset Load**: TCGA_BRCA 프리셋 로드 → 모든 필드 자동 입력 확인
- [ ] **Config Save/Load**: 설정 저장 → 새 세션에서 로드 → 동일 값 확인
- [ ] **R 미설치 시**: 앱 시작 → 에러 안내 → Settings로 이동
- [ ] **분석 취소**: 실행 중 Cancel → R 프로세스 종료 확인
- [ ] **대용량 CSV**: 20,000+ 컬럼 CSV → UI 렉 없이 컬럼 목록 표시
- [ ] **잘못된 입력**: 필수 필드 비움 → 유효성 에러 표시, 실행 버튼 비활성화
- [ ] **크로스플랫폼**: Mac/Linux/Windows에서 파일 경로 구분자 정상 처리

---

## 9. Clean Architecture

### 9.1 Layer Structure

| Layer | Responsibility | Location |
|-------|---------------|----------|
| **Presentation** | UI 컴포넌트, 이벤트 핸들링, 레이아웃 | `src/pages/`, `src/components/` |
| **Application** | 비즈니스 로직 조합, Store, IPC 호출 | `src/stores/`, `src/hooks/` |
| **Domain** | 타입 정의, 설정 변환, 유효성 검증 | `src/types/`, `src/lib/validation.ts` |
| **Infrastructure** | Tauri IPC 래퍼, 파일 시스템 접근 | `src/lib/tauri/`, `src/lib/config.ts` |

### 9.2 Dependency Rules

```
  Presentation ──▶ Application ──▶ Domain ◀── Infrastructure
                        │                         ▲
                        └─────────────────────────┘

  - Domain: 순수 타입/로직, 외부 의존 없음
  - Infrastructure: Tauri API 래퍼 (Domain 타입만 import)
  - Application: Store + Hook (Domain + Infrastructure 사용)
  - Presentation: 컴포넌트 (Application + Domain 사용)
```

---

## 10. Coding Convention

### 10.1 Naming Conventions

| Target | Rule | Example |
|--------|------|---------|
| React Component | PascalCase | `AnalysisTypeSelector` |
| Hook | camelCase with `use` prefix | `useAnalysisStore` |
| Utility function | camelCase | `buildYamlConfig()` |
| Constant | UPPER_SNAKE_CASE | `MAX_SEED_COUNT` |
| Type/Interface | PascalCase | `AnalysisConfig` |
| Component file | PascalCase.tsx | `SetupPage.tsx` |
| Utility file | camelCase.ts | `validation.ts` |
| Folder | kebab-case | `setup/`, `shared/` |
| Tauri command | snake_case (Rust) | `analysis_run` |
| IPC invoke name | `domain:action` | `"analysis:run"` |
| Tauri event | `domain://event` | `"analysis://progress"` |

### 10.2 Import Order

```typescript
// 1. React / external libraries
import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

// 2. UI components (shadcn/ui)
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

// 3. App components
import { FilePickerField } from "@/components/shared/FilePickerField";

// 4. Stores & Hooks
import { useAnalysisStore } from "@/stores/analysisStore";

// 5. Types
import type { AnalysisConfig, DataFileInfo } from "@/types/analysis";

// 6. Lib / Utils
import { validateConfig } from "@/lib/validation";
```

---

## 11. Implementation Guide

### 11.1 File Structure

```
prognosis_marker/
├── src-tauri/                      # Rust Backend
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── icons/
│   ├── src/
│   │   ├── main.rs                 # Tauri entry point
│   │   ├── lib.rs                  # Module declarations
│   │   ├── commands/
│   │   │   ├── mod.rs
│   │   │   ├── analysis.rs         # analysis:run, cancel, status
│   │   │   ├── config.rs           # config:load, save, validate, presets
│   │   │   ├── fs_ops.rs           # fs:pick_file, pick_dir, read_csv
│   │   │   └── runtime.rs          # runtime:detect, check_deps
│   │   ├── models/
│   │   │   ├── mod.rs
│   │   │   ├── config.rs           # AnalysisConfig serde structs
│   │   │   └── error.rs            # AppError definitions
│   │   └── utils/
│   │       ├── mod.rs
│   │       ├── yaml.rs             # YAML serialization helpers
│   │       ├── process.rs          # R process spawn + stream
│   │       └── csv_reader.rs       # CSV header reader
│   └── capabilities/
│       └── default.json            # Tauri permissions
│
├── src/                            # React Frontend
│   ├── App.tsx                     # Root component
│   ├── main.tsx                    # Entry point
│   ├── index.css                   # Tailwind base styles
│   │
│   ├── pages/
│   │   ├── SetupPage.tsx
│   │   ├── ResultsPage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   └── Sidebar.tsx
│   │   ├── ui/                     # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── slider.tsx
│   │   │   ├── radio-group.tsx
│   │   │   ├── checkbox.tsx
│   │   │   ├── select.tsx
│   │   │   ├── input.tsx
│   │   │   ├── accordion.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   ├── shared/
│   │   │   ├── FilePickerField.tsx
│   │   │   ├── DirectoryPickerField.tsx
│   │   │   ├── SliderField.tsx
│   │   │   ├── NumberField.tsx
│   │   │   └── LogConsole.tsx
│   │   ├── setup/
│   │   │   ├── AnalysisTypeSelector.tsx
│   │   │   ├── PresetSelector.tsx
│   │   │   ├── DataPreview.tsx
│   │   │   ├── ColumnMappingSection.tsx
│   │   │   ├── ParametersSection.tsx
│   │   │   ├── AdvancedOptionsAccordion.tsx
│   │   │   ├── PValueFilterGroup.tsx
│   │   │   ├── FeatureSelectionAccordion.tsx
│   │   │   ├── EvidenceFilterAccordion.tsx
│   │   │   ├── ActionBar.tsx
│   │   │   └── ProgressPanel.tsx
│   │   ├── results/
│   │   │   ├── PlotViewer.tsx
│   │   │   ├── PlotTabs.tsx
│   │   │   └── AucTable.tsx
│   │   └── settings/
│   │       └── RuntimeConfig.tsx
│   │
│   ├── stores/
│   │   ├── analysisStore.ts
│   │   └── configStore.ts
│   │
│   ├── hooks/
│   │   ├── useAnalysisRunner.ts    # 분석 실행 + 이벤트 리스닝
│   │   └── useTauriEvents.ts       # Tauri 이벤트 구독 유틸
│   │
│   ├── lib/
│   │   ├── tauri/
│   │   │   ├── commands.ts         # invoke 래퍼 (타입 안전)
│   │   │   └── events.ts           # listen 래퍼
│   │   ├── validation.ts           # config 유효성 검증
│   │   └── configTransform.ts      # Store ↔ YAML 변환
│   │
│   └── types/
│       ├── analysis.ts             # AnalysisConfig, DataFileInfo
│       ├── results.ts              # AnalysisResult, PlotFile
│       └── store.ts                # Store 타입
│
├── r-engine/                       # R 분석 엔진 (기존 파일 심볼릭 링크 또는 복사)
│   ├── Main_Binary.R
│   ├── Main_Survival.R
│   ├── Binary_TrainAUC_StepwiseSelection.R
│   └── Survival_TrainAUC_StepwiseSelection.R
│
├── config/                         # 기존 YAML 프리셋들
│   ├── example_analysis.yaml
│   ├── TCGA_BRCA_analysis.yaml
│   └── ... (34개)
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
└── postcss.config.js
```

### 11.2 Implementation Order

```
Phase 1: 프로젝트 초기화                          [Week 1]
─────────────────────────────────────────────────
1. [ ] Tauri 2.0 + React + TypeScript 프로젝트 생성
2. [ ] shadcn/ui + Tailwind 설정
3. [ ] 기본 레이아웃 (Sidebar + 3 Pages)
4. [ ] Zustand 스토어 스캐폴딩

Phase 2: Rust Backend 핵심                        [Week 1-2]
─────────────────────────────────────────────────
5. [ ] models/config.rs - Serde 구조체 정의
6. [ ] commands/runtime.rs - R/pixi 경로 탐지
7. [ ] commands/fs_ops.rs - 파일/폴더 선택, CSV 헤더 읽기
8. [ ] commands/config.rs - YAML 로드/저장/검증

Phase 3: Setup 페이지 UI                          [Week 2-3]
─────────────────────────────────────────────────
9.  [ ] AnalysisTypeSelector (Radio Button)
10. [ ] FilePickerField + DataPreview
11. [ ] ColumnMappingSection (동적 Dropdown)
12. [ ] ParametersSection (Slider, NumberInput)
13. [ ] AdvancedOptionsAccordion + PValueFilterGroup
14. [ ] FeatureSelectionAccordion (Checkbox List)
15. [ ] EvidenceFilterAccordion
16. [ ] OutputSection (DirectoryPicker)

Phase 4: 분석 실행 연동                            [Week 3-4]
─────────────────────────────────────────────────
17. [ ] commands/analysis.rs - R 프로세스 spawn + 로그 스트리밍
18. [ ] useAnalysisRunner hook - Tauri 이벤트 구독
19. [ ] ProgressPanel + LogConsole
20. [ ] ActionBar - Run/Cancel/Save/Load 버튼

Phase 5: 결과 뷰어                                [Week 4]
─────────────────────────────────────────────────
21. [ ] fs:list_output_plots + fs:read_image 구현
22. [ ] PlotTabs + PlotViewer (이미지 표시)
23. [ ] AucTable (CSV 파싱 + 테이블 렌더링)

Phase 6: 프리셋 & 설정                            [Week 5]
─────────────────────────────────────────────────
24. [ ] PresetSelector + config:list_presets
25. [ ] Settings 페이지 (RuntimeConfig)
26. [ ] Config 저장/불러오기 기능

Phase 7: 빌드 & 테스트                            [Week 5-6]
─────────────────────────────────────────────────
27. [ ] Vitest 단위 테스트 (유효성 검증, Store)
28. [ ] Rust #[test] (YAML 직렬화, CSV 파싱)
29. [ ] Mac/Linux/Windows 빌드 파이프라인
30. [ ] E2E 스모크 테스트
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | Initial draft | User |
