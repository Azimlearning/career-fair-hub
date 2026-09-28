import json
from pathlib import Path

from .config import FAIRS_DIR, CATEGORY

COMPANY_FIELDS = {
    "name": "", "category": "job", "booth": "", "tier": "", "industry": "", "programme_type": "", "it_roles": "",
    "roles": "", "requirements": "", "min_cgpa": "", "intake": "", "about": "", "contact": "", "email": "",
    "phone": "", "website": "", "social": "", "how_to_apply": "", "resume_drop": "", "location": "",
    "links": [], "share": True, "share_reason": "", "sources": [], "notes": [],
}


def resolve(ref):
    """Accept a fair id (e.g. 2026-09-tec26-utp) or a path."""
    p = Path(ref)
    if p.is_dir():
        return p.resolve()
    p = FAIRS_DIR / ref
    if p.is_dir():
        return p
    matches = [d for d in FAIRS_DIR.iterdir() if d.is_dir() and ref.lower() in d.name.lower()]
    if len(matches) == 1:
        return matches[0]
    raise SystemExit(f"Fair not found: {ref!r}. Known: {[d.name for d in list_fairs()]}")


def list_fairs():
    if not FAIRS_DIR.exists():
        return []
    return sorted(d for d in FAIRS_DIR.iterdir() if (d / "fair.json").exists())


def load_meta(fair_dir):
    return json.loads((Path(fair_dir) / "fair.json").read_text(encoding="utf-8"))


def load_companies(fair_dir):
    path = Path(fair_dir) / "data" / "companies.json"
    if not path.exists():
        return []
    out = []
    for c in json.loads(path.read_text(encoding="utf-8")):
        rec = {k: (list(v) if isinstance(v, list) else v) for k, v in COMPANY_FIELDS.items()}
        rec.update(c)
        out.append(rec)
    return out


def load_json(fair_dir, rel, default=None):
    p = Path(fair_dir) / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def new_fair(fair_id, name, short_name=None, organiser="", venue="", dates=()):
    d = FAIRS_DIR / fair_id
    if d.exists():
        raise SystemExit(f"{d} already exists")
    for sub in ("raw/photos", "processed", "work/extraction", "work/qr", "data", "output"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    meta = {"id": fair_id, "name": name, "short_name": short_name or fair_id, "organiser": organiser,
            "venue": venue, "dates": list(dates), "links_checked": ""}
    (d / "fair.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (d / "data" / "companies.json").write_text("[]\n", encoding="utf-8")
    return d


def validate(companies):
    problems = []
    seen = set()
    for c in companies:
        n = c.get("name", "").strip()
        if not n:
            problems.append("record with empty name")
            continue
        if n.lower() in seen:
            problems.append(f"duplicate company: {n}")
        seen.add(n.lower())
        if c["category"] not in CATEGORY:
            problems.append(f"{n}: unknown category {c['category']!r}")
        if c["category"] == "job":
            has_route = c["links"] or c["email"] or c["website"] or c.get("qr_photo")
            if not has_route:
                problems.append(f"{n}: job booth with no link, email or website — move to 'other'?")
        for l in c["links"]:
            if not l.get("url"):
                problems.append(f"{n}: link {l.get('label')!r} has no url")
    return problems
