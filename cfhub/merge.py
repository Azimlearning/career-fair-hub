"""Merge booth-extractor batch outputs into a draft companies list (dedupe by company name)."""
import json
import re
from pathlib import Path

STOPWORDS = r"\b(sdn|bhd|berhad|malaysia|m|technologies|technology|inc|ltd|corp|group|solutions|systems|pte)\b"

# raw extractor field -> companies.json field
FIELD_MAP = {
    "industry": "industry", "roles": "roles", "requirements": "requirements", "description": "about",
    "contact": "contact", "email": "email", "phone": "phone", "website": "website", "social": "social",
    "application_instructions": "how_to_apply", "resume_drop": "resume_drop", "location": "location", "booth": "booth",
}


def merge_key(name, aliases):
    n = name.lower()
    n = re.sub(r"\(.*?\)", " ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(STOPWORDS, " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = aliases.get(n, n)
    return n.replace(" ", "")


def _join(values):
    seen = []
    for v in values:
        v = (v or "").strip()
        if v and v != "-" and v not in seen:
            seen.append(v)
    return " | ".join(seen)


def merge(fair_dir):
    fair_dir = Path(fair_dir)
    ext = fair_dir / "work" / "extraction"
    aliases_path = fair_dir / "data" / "aliases.json"
    aliases = json.loads(aliases_path.read_text(encoding="utf-8")) if aliases_path.exists() else {}
    records = []
    for f in sorted(ext.glob("batch_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")).get("records", []):
            r["batch"] = f.stem.replace("batch_", "")
            records.append(r)
    groups = {}
    for r in records:
        if not r.get("name") or r.get("booth_type") == "skip":
            continue
        groups.setdefault(merge_key(r["name"], aliases), []).append(r)
    draft = []
    for key, rs in groups.items():
        c = {"name": max((r["name"] for r in rs), key=len) if len(rs) > 1 else rs[0]["name"],
             "category": "further" if any("further" in (r.get("booth_type") or "").lower() for r in rs) else "job"}
        for src, dst in FIELD_MAP.items():
            c[dst] = _join(r.get(src) for r in rs)
        c["links"] = [{"label": l.get("label", "link"), "url": l["url"]} for r in rs for l in r.get("links", []) if l.get("url")]
        c["sources"] = sorted({s for r in rs for s in r.get("source_files", [])})
        c["notes"] = [r["notes"] for r in rs if r.get("notes") and r["notes"] != "-"]
        c["merged_from"] = [r["name"] for r in rs]
        draft.append(c)
    draft.sort(key=lambda c: c["name"].lower())
    out = fair_dir / "data" / "companies.draft.json"
    out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    multi = [c for c in draft if len(c["merged_from"]) > 1]
    print(f"{len(records)} raw records -> {len(draft)} companies ({len(multi)} merged) -> {out}")
    print("Near-duplicates to eyeball (add to data/aliases.json if they are the same company):")
    names = sorted(c["name"] for c in draft)
    for a, b in zip(names, names[1:]):
        if a.split()[0].lower() == b.split()[0].lower():
            print(f"  {a}  <->  {b}")
    return draft
