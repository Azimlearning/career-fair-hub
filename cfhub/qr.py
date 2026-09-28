import json
from pathlib import Path

from PIL import Image, ImageOps, ImageEnhance

GENERIC_RULES = [
    ("me-qr.com", "DEAD — expired me-qr code (check with `check-links`)"),
    ("000201", "Payment QR (DuitNow/EMVCo) — unrelated"),
    ("uevent.", "Organiser event / voting form"),
    ("linkedin.com", "LinkedIn"),
    ("instagram.com", "Instagram"),
    ("facebook.com", "Facebook"),
]


def _read(im):
    import zxingcpp
    out = []
    for b in (zxingcpp.Binarizer.LocalAverage, zxingcpp.Binarizer.GlobalHistogram):
        try:
            out += zxingcpp.read_barcodes(im, formats=zxingcpp.BarcodeFormat.QRCode,
                                          try_rotate=True, try_downscale=True, binarizer=b)
        except Exception:
            pass
    return out


def _scan_image(img):
    """Full-image passes at several scales + overlapping tiles (catches small QRs in big photos)."""
    W, H = img.size
    found = {}

    def add(codes, ox, oy, s):
        for c in codes:
            if not c.valid or not c.text or c.text in found:
                continue
            p = c.position
            xs = [p.top_left.x, p.top_right.x, p.bottom_left.x, p.bottom_right.x]
            ys = [p.top_left.y, p.top_right.y, p.bottom_left.y, p.bottom_right.y]
            found[c.text] = (ox + min(xs) / s, oy + min(ys) / s, ox + max(xs) / s, oy + max(ys) / s)

    gray = ImageEnhance.Contrast(img.convert("L")).enhance(1.6)
    for s in (1.0, 0.5, 0.3):
        im = gray if s == 1.0 else gray.resize((int(W * s), int(H * s)))
        add(_read(im), 0, 0, s)
    tw, th = W // 2, H // 2
    for x in (0, W // 4, W // 2):
        for y in (0, H // 4, H // 2):
            tile = gray.crop((x, y, min(W, x + tw), min(H, y + th)))
            s = 1.0 if max(tile.size) <= 1600 else 1600 / max(tile.size)
            t = tile if s == 1.0 else tile.resize((int(tile.size[0] * s), int(tile.size[1] * s)))
            add(_read(t), x, y, s)
    return found


def scan(fair_dir):
    """Decode every QR in processed photos + hi-res booklet pages -> work/qr/qr_raw.json (+ crops)."""
    fair_dir = Path(fair_dir)
    proc = fair_dir / "processed"
    crops = fair_dir / "work" / "qr" / "crops"
    crops.mkdir(parents=True, exist_ok=True)
    files = sorted((proc / "photos_jpg").glob("*.jpg")) + sorted((proc / "booklet_hires").glob("*.png"))
    results = []
    for path in files:
        img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        W, H = img.size
        for i, (text, (x0, y0, x1, y1)) in enumerate(_scan_image(img).items()):
            pad = 0.12 * max(x1 - x0, y1 - y0)
            box = (max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(W, int(x1 + pad)), min(H, int(y1 + pad)))
            crop = img.crop(box)
            crop.thumbnail((400, 400))
            name = f"{path.stem}_qr{i}.png"
            crop.save(crops / name)
            results.append({"source": path.stem, "text": text, "cx": round((x0 + x1) / 2 / W, 3),
                            "cy": round((y0 + y1) / 2 / H, 3), "crop": f"work/qr/crops/{name}"})
        print(f"{path.name}: {sum(1 for r in results if r['source'] == path.stem)}", flush=True)
    out = fair_dir / "work" / "qr" / "qr_raw.json"
    out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"TOTAL {len(results)} QR codes -> {out}")
    return results


def build_index(fair_dir, companies):
    """Merge qr_raw.json into qr_index.json: keep manual company/status, auto-classify the rest."""
    fair_dir = Path(fair_dir)
    idx_path = fair_dir / "work" / "qr" / "qr_index.json"
    raw_path = fair_dir / "work" / "qr" / "qr_raw.json"
    existing = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else []
    known = {(e["source"], e["text"]): e for e in existing}
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else []
    url_owner = {l["url"]: (c["name"], l["label"]) for c in companies for l in c["links"]}
    for r in raw:
        key = (r["source"], r["text"])
        e = known.get(key) or {"source": r["source"], "text": r["text"], "company": "", "status": "", "crop": r["crop"]}
        if r["text"] in url_owner:
            e["company"], lbl = url_owner[r["text"]]
            e["status"] = f"Used in directory — {lbl}"
        elif not e["status"]:
            e["status"] = next((desc for pat, desc in GENERIC_RULES if pat in r["text"]), "Not used — review")
        known[key] = e
    index = sorted(known.values(), key=lambda x: (not x["source"].startswith("IMG"), x["source"]))
    idx_path.write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding="utf-8")
    todo = [e for e in index if e["status"].startswith("Not used")]
    print(f"qr_index: {len(index)} entries, {len(todo)} need review")
    return index
