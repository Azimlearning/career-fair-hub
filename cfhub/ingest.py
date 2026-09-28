import json
import zipfile
from pathlib import Path

from PIL import Image, ImageOps

from .config import BATCH_SIZE

IMAGE_EXT = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}


def ingest(fair_dir, max_side=2000, booklet_dpi=100, hires_dpi=300):
    """raw/ (zip, photos, pdf) -> processed/photos_jpg, processed/booklet_pages, processed/booklet_hires."""
    import fitz
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        print("! pillow-heif not installed — HEIC photos will be skipped")

    fair_dir = Path(fair_dir)
    raw, proc = fair_dir / "raw", fair_dir / "processed"
    photos_raw = raw / "photos"
    photos_raw.mkdir(parents=True, exist_ok=True)

    for z in raw.glob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            for member in zf.namelist():
                if Path(member).suffix.lower() in IMAGE_EXT:
                    target = photos_raw / Path(member).name
                    if not target.exists():
                        target.write_bytes(zf.read(member))
        print(f"unzipped {z.name}")

    out = proc / "photos_jpg"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(photos_raw.rglob("*")):
        if f.suffix.lower() not in IMAGE_EXT:
            continue
        target = out / (f.stem + ".jpg")
        if target.exists():
            continue
        try:
            img = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        except Exception as e:  # unreadable file — report and move on
            print(f"! could not read {f.name}: {e}")
            continue
        img.thumbnail((max_side, max_side))
        img.save(target, quality=88)
        n += 1
    print(f"photos converted: {n} new, {len(list(out.glob('*.jpg')))} total")

    pdfs = sorted(raw.glob("*.pdf"))
    for pdf in pdfs:
        prefix = "" if len(pdfs) == 1 else pdf.stem + "_"
        doc = fitz.open(pdf)
        for sub, dpi in (("booklet_pages", booklet_dpi), ("booklet_hires", hires_dpi)):
            d = proc / sub
            d.mkdir(parents=True, exist_ok=True)
            for i, page in enumerate(doc, start=1):
                p = d / f"{prefix}page_{i:03d}.png"
                if not p.exists():
                    page.get_pixmap(dpi=dpi).save(p)
        print(f"rendered {pdf.name}: {len(doc)} pages")


def make_batches(fair_dir, size=BATCH_SIZE):
    """Split photos + booklet pages into batches for booth-extractor subagents."""
    fair_dir = Path(fair_dir)
    proc = fair_dir / "processed"
    photos = sorted(str(p) for p in (proc / "photos_jpg").glob("*.jpg"))
    pages = sorted(str(p) for p in (proc / "booklet_pages").glob("*.png"))
    batches = []
    for kind, files, tag in (("photos", photos, "P"), ("booklet", pages, "B")):
        for i in range(0, len(files), size):
            batches.append({"id": f"{tag}{i // size + 1}", "kind": kind, "files": files[i:i + size],
                            "output": str(fair_dir / "work" / "extraction" / f"batch_{tag}{i // size + 1}.json")})
    path = fair_dir / "work" / "extraction" / "batches.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(batches, indent=1), encoding="utf-8")
    return batches
