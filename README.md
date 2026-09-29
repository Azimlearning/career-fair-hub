# Career Fair Hub

A side project born out of processing UTP's TEC26 career fair by hand — sharing it in case it's useful to other job
seekers doing the same thing, or to career-fair organisers/managers who want a clean, shareable directory of their
own event's exhibitors instead of a pile of booth photos.

Turn a career-fair photo dump (booth photos, phone screenshots, programme-booklet PDF) into:

- **a shareable directory** per fair — every employer with roles, requirements, contacts, and a scannable QR code +
  clickable link to apply (`fairs/<fair>/output/<SHORT>_Job_Directory_Share.xlsx`)
- **one master job-hunt tracker** across all fairs — status, dates, follow-ups, dashboard
  (`output/Career_Fair_Master.xlsx`, personal, not committed)

## Fairs

| Fair | Dates | Companies | Share copy |
|---|---|---|---|
| TEC26 — Technology, Education & Career 2026 (UTP) | 23–24 Sep 2026 | 96 (57 in share copy) | `fairs/2026-09-tec26-utp/output/TEC26_Job_Directory_Share.xlsx` |

## Layout

```
cfhub/                     pipeline code (python -m cfhub ...)
.claude/
  skills/career-fair-ingest/   end-to-end workflow for Claude Code (/career-fair-ingest)
  agents/booth-extractor.md    subagent: one batch of images -> strict JSON
  agents/fair-qa-reviewer.md   subagent: independent QA before sharing
fairs/<YYYY-MM-short-host>/
  fair.json                name, venue, dates
  raw/                     original zip / HEIC photos / booklet PDF            (git-ignored)
  processed/               photos_jpg, booklet_pages, booklet_hires            (git-ignored)
  work/extraction/         batch_*.json from subagents, raw_records.json
  work/qr/                 qr_raw.json, qr_index.json, link_report.json (crops git-ignored)
  data/companies.json      curated source of truth  <- edit this
  data/aliases.json        optional: merge rules for name variants
  output/                  share copy .xlsx
output/Career_Fair_Master.xlsx   hub-wide tracker (git-ignored, personal)
archive/                   superseded spreadsheets (git-ignored)
```

## Setup

```bash
pip install -r requirements.txt
```

## Adding a new fair

**With Claude Code (recommended):** drop the photos/booklet somewhere and run `/career-fair-ingest` — it follows
`.claude/skills/career-fair-ingest/SKILL.md`: create the fair → ingest → parallel `booth-extractor` subagents +
QR scan → merge/curate → link check + `fair-qa-reviewer` → build.

**By hand:**

```bash
python -m cfhub new 2027-03-cf27-um --name "Career Fair 2027" --short CF27 --venue "UM" --dates 2027-03-10 2027-03-11
# copy zip / photos / booklet.pdf into fairs/2027-03-cf27-um/raw/
python -m cfhub ingest cf27          # HEIC->JPG, booklet -> PNG pages
python -m cfhub batches cf27         # image batches for extraction
python -m cfhub scan-qr cf27         # decode every QR code
python -m cfhub merge cf27           # batch_*.json -> data/companies.draft.json
#   ...curate data/companies.json...
python -m cfhub qr-index cf27        # classify QR codes
python -m cfhub check-links cf27     # flag dead / expired links
python -m cfhub validate cf27
python -m cfhub build                # share copies + master tracker
```

## The master tracker

- Red columns (Interested, Priority, Application Status, Applied Date, Follow-up Date, Interview Date, Next
  Action, Notes…) are yours. **`build` keeps them** — it reads the existing master before regenerating, matching rows
  by (Fair, Company). Rows you add at the bottom by hand are kept too.
- Follow-up dates turn amber within 7 days and red when overdue; the Dashboard sheet counts everything.
- Close the file in Excel before `build`, otherwise it writes `Career_Fair_Master_new.xlsx`.

## `companies.json` fields

`name, category (job|further|startup|other|career|sponsor), booth, tier, industry, programme_type, it_roles, roles,
requirements, min_cgpa, intake, about, contact, email, phone, website, social, how_to_apply, resume_drop, location,
links [{label, url}] (first = QR image), qr_photo {file, box, label} (optional), share, share_reason, sources, notes`

## Data & privacy

`data/companies.json` only records what was printed or displayed on a company's own booth material (booth signage,
brochure ads, application-form screenshots) — company names, roles, and the contact details each exhibitor chose to
hand out for recruitment. No attendee's personal information is captured. If you fork this for your own fair, keep
that same rule.

## Lessons learned (TEC26)

- Extract to **JSON, not markdown tables** — one missing `|` silently shifted a whole row.
- Booth directory + sponsor-tier pages are the checklist: a company was missed (VAT) and a logo misread (ATM→TTM).
- me-qr.com QR codes **expire** and redirect to the generator's blog — always run `check-links`.
- Decode QRs with zxing-cpp on 300 dpi renders + tiled scanning; regenerate clean QR images from the URLs.
- An "unidentified" booth was identified from its QR (LinkedIn → Synthomer). Scan before giving up on a name.
