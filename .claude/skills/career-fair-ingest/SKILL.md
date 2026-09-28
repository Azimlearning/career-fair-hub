---
name: career-fair-ingest
description: Turn a career-fair dump (booth photos zip/HEIC, brochure or programme-booklet PDF) into a curated company directory, a shareable Excel for friends, and rows in the job-hunt master tracker. Use when the user drops a new career fair's photos/booklet, says "new career fair", "process this career fair", "add this fair to the hub", or asks to update/rebuild the career fair spreadsheets.
---

# Career fair ingest

Repo layout (see README.md): `fairs/<YYYY-MM-shortname>/{raw,processed,work,data,output}`, pipeline code in
`cfhub/`, hub-wide tracker at `output/Career_Fair_Master.xlsx`. Run all commands from the repo root.

## 1. Set up the fair
- Pick an id `YYYY-MM-<short>-<host>` (e.g. `2027-03-cf27-um`) and short name (e.g. `CF27`).
- `python -m cfhub new <id> --name "<full name>" --short <SHORT> --venue "<venue>" --dates 2027-03-10 2027-03-11`
- Move the user's files into `fairs/<id>/raw/` (photos zip or loose photos → `raw/photos/`, booklet → `raw/*.pdf`).
- `python -m cfhub ingest <id>` → JPGs in `processed/photos_jpg`, pages in `processed/booklet_pages` (+ 300 dpi
  `booklet_hires` for QR decoding).

## 2. Extract (parallel subagents)
- `python -m cfhub batches <id>` → `work/extraction/batches.json` (15 images per batch).
- Launch one **booth-extractor** subagent per batch **in a single message** (parallel, background). Give each its
  batch id, file list and output path. It writes `work/extraction/batch_<id>.json`.
- Start QR decoding meanwhile: `python -m cfhub scan-qr <id>` (run in background; takes a few minutes).
- When a batch reports back, check its JSON parses. If an agent is silent for >10 min, relaunch that batch
  (TEC26 lost one to an orphaned agent after a session resume).

## 3. Merge and curate → `data/companies.json`
- `python -m cfhub merge <id>` → `data/companies.draft.json` + a near-duplicate list. Add true duplicates to
  `data/aliases.json` (`{"normalized variant": "normalized canonical"}`) and re-run.
- Curate into `data/companies.json` (schema = `cfhub/fairs.py: COMPANY_FIELDS`; see the TEC26 file as the model):
  - **category**: `job` (any way to apply), `further` (study), `startup` (incubators/accelerators), `other`
    (real employer but no apply details — logo only / brand ad), `career` (career-support partners, activities),
    `sponsor` (merchandise, F&B). Only job/further/startup go in the share copy.
  - **programme_type**: say whether it is Direct hire, Graduate / rotation / trainee programme, Internship,
    Apprenticeship, Scholarship — combine with "+".
  - **roles**: full lists, grouped by location/entity/qualification with line breaks. Never "and more".
  - **contact**: named hiring contacts with their own email/phone/LinkedIn.
  - **links**: first link = the main "apply" QR (it becomes the QR image). Use decoded URLs from
    `work/qr/qr_raw.json` — copy them exactly, never retype. Others after it with clear labels.
  - **it_roles / min_cgpa / intake / tier / resume_drop**: fill only from what's printed.
  - Booth directory and sponsor-tier pages list every exhibitor: make sure each one exists in some category.
  - Unreadable-but-important QR (e.g. dense CV-drop code): use `qr_photo` with the photo box instead of a link.
- Resolve short links you can't identify with WebFetch (e.g. `qr.generatorqr.com/<id>/go`, `canvaqr.com/<id>`) so
  labels say what they are. Links that land on job postings: add the listed roles (mark "per QR link").

## 4. Verify
- `python -m cfhub qr-index <id>`: every QR gets a company + status; fix any "Not used — review" by hand in
  `work/qr/qr_index.json` (organiser voting forms, unrelated personal QRs, duplicates are normal).
- `python -m cfhub check-links <id>`: DEAD links must not be primary links. Known traps: **me-qr.com codes expire and
  redirect to ME-QR's blog**; LinkedIn returns 999 and SmartRecruiters 400 to bots (not dead).
- Launch the **fair-qa-reviewer** subagent; fix every "Blocking" item.
- `python -m cfhub validate <id>`.

## 5. Build and hand over
- `python -m cfhub build` → `fairs/<id>/output/<SHORT>_Job_Directory_Share.xlsx` and the hub master
  `output/Career_Fair_Master.xlsx`. The master keeps the user's tracker columns (status, dates, notes) and any
  hand-added rows across rebuilds — never delete it to "start fresh".
- If a file is open in Excel the build saves `*_new.xlsx`; tell the user to close Excel and rebuild.
- Visual check: export a copy to PDF via Excel COM (PowerShell) and look at a few rows (QR images, row heights).
- Tell the user: counts per category, what was excluded from the share copy and why, dead/unclear links, anything
  you could not read.

## Share copy rules (user preferences)
- No tracker columns, no "Accepts Resume Drop?" column, no source/internal notes, no booth numbers.
- Companies with nothing to apply to are left out; further study bunched after job booths; startup/incubators last.
- QR image in the cell (regenerated from the decoded URL so it scans cleanly) + clickable URL beside it.
