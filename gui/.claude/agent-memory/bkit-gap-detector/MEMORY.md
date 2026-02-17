# Gap Detector Memory - prognosis_marker/gui

## Project Structure
- Design doc: `/home/ubuntu/projects/prognosis_marker/docs/02-design/features/gui-desktop-app.design.md`
- Analysis doc: `/home/ubuntu/projects/prognosis_marker/docs/03-analysis/gui-desktop-app.analysis.md`
- Rust backend: `/home/ubuntu/projects/prognosis_marker/gui/src-tauri/src/`
- React frontend: `/home/ubuntu/projects/prognosis_marker/gui/src/`
- NOTE: docs/ is at parent level (`/home/ubuntu/projects/prognosis_marker/docs/`), NOT inside gui/

## Last Analysis (2026-02-17, Iteration 4)
- Overall match rate: 89% (up from 87%) -- 1% below 90% threshold
- Phases 1-3: 88-100% complete (Phase 3 at 100%)
- Phase 4: 90% (streaming working)
- Phase 5: 85% (AucTable, dynamic plots, no zoom/pan or ExportButtons)
- Phase 6: 90% (Settings has path overrides + dep checker)
- Phase 7: 52% (up from 45% -- 14 Rust tests + 12 Vitest tests including 4 component tests)
- R process streaming: IMPLEMENTED (BufReader + event emission)
- AppError adoption: 10 structured / 18 total error paths = 56%
  - fs_ops.rs: 5 AppError, 1 ad-hoc (83%)
  - config.rs: 3 AppError, 6 ad-hoc (33%) -- biggest remaining gap
  - analysis.rs: 2 AppError, 1 ad-hoc (67%)
  - All 4 constructors (E001,E003,E004,E006) now ACTIVE in commands
- 14/15 IPC commands implemented (only analysis:get_status missing)
- All 4 event types emitted (error payload simplified)
- shadcn/ui still not installed (plain HTML + Tailwind)
- Shared components still inlined into parents (11 of 24)
- 26 total tests: 14 Rust + 12 frontend (8 store + 4 component)
- To reach 90%: wire AppError into remaining config.rs format!() (~+1%), add 2+ component tests (~+1%), OR update design doc for intentional diffs (~+1-2%)
