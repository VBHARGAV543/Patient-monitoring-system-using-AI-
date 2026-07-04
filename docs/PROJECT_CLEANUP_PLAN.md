# Project Cleanup Plan

This repository has useful source code, but it also contains backup trees, phase notes, generated assets, and repeated documentation. The goal is to make the tree professional without breaking runtime behavior.

## Canonical Trees To Keep

- `backend/` is the canonical backend source tree.
- `backend/main.py` is the active FastAPI entrypoint.
- `frontend_new/` is the canonical web frontend candidate.
- `mobile_app/NurseAlarmApp/` is the canonical Android app.
- `ML/` contains the training and simulation source files.
- `assets/` is the canonical home for images, diagrams, and flowcharts.

## Legacy Trees Kept For Review

- `Frontend_legacy/` is the renamed legacy static frontend.
- `backend/main_new.py` is an older backend implementation snapshot.
- `backend/main_old_backup.py` is the original backend backup.
- `frontend_new/backups/` contains archived frontend snapshots.
- `mobile_app/backups/` contains archived Android snapshots.

## Candidate Backups And Duplicates

These should be reviewed before any deletion. They are likely redundant or archival copies:

- `docs/patent/Patent_Figures_Package.docx`
- `docs/patent/Patent_Figures_Package_v2.docx`
- `docs/patent/Patent_Figures_Package_v3.docx`
- `docs/patent/Patent_Rough_Draft_Utility.docx`
- `docs/patent/Patent_Rough_Draft_Utility_Image_Placeholder.docx`
- `docs/patent/Patent_Rough_Draft_Utility_With_Flowchart.docx`

## Files That Should Move Into docs/

These are documentation and progress artifacts that belong under `docs/` once you approve the move:

- `docs/phases/PHASE0_baseline_freeze.md`
- `docs/phases/PHASE1_hardware_mode_admission.md`
- `docs/phases/PHASE2_hardware_vitals_pipeline.md`
- `docs/phases/PHASE3_web_frontend_vitals.md`
- `docs/phases/PHASE4_tampering_button.md`
- `docs/phases/PHASE5_manual_override.md`
- `docs/phases/PHASE6_mobile_app_alignment.md`
- `docs/phases/PHASE7_validation_testing.md`
- `docs/fixes/ANDROID_FIX_SUMMARY.md`
- `docs/fixes/CRITICAL_FIX.md`
- `docs/implementation/HARDWARE_MODE_IMPLEMENTATION_SUMMARY.md`
- `docs/implementation/IMPLEMENTATION_PROGRESS.md`
- `docs/implementation/MOCK_DATA_IMPLEMENTATION.md`
- `docs/setup/NETWORK_CONFIG.md`
- `docs/updates/NETWORK_UPDATE_SUMMARY.md`
- `docs/reference/PROJECT_OVERVIEW.md`
- `docs/setup/QUICK_START.md`
- `docs/setup/QUICK_START_MOCK_DATA.md`
- `docs/setup/RESTART_INSTRUCTIONS.md`
- `docs/updates/SPLASH_LOGO_UPDATE.md`
- `docs/updates/TODO.md`
- `docs/fixes/VITALS_CAMERA_FIX.md`
- `docs/reference/METHODOLOGY_AND_INTRODUCTION.txt`

## Recommended Retention Rules

- Keep the newest version when filenames differ only by suffix like `_v2`, `_v3`, `_new`, or `_backup`.
- Prefer source files that are referenced by the active launch commands over unused variants.
- Do not delete any generated patent artifacts until you confirm which version was submitted or published.

## Manual Review Targets

- `backend/main_new.py` should be compared against `backend/main.py` before any cleanup.
- `backend/main_old_backup.py` should remain untouched until a diff review confirms it is disposable.
- `frontend_new/backups/` should be retained until the canonical React build is validated.
- `mobile_app/backups/` should be retained until the Android app is validated.
- `Frontend_legacy/` should remain as the archived static frontend until the React app fully replaces it.

## No-Deletion Rule

No file has been deleted in this pass. The next safe step is to move the confirmed documentation set into `docs/` and then remove only clearly redundant duplicates.