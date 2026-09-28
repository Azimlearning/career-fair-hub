import json
import urllib.request
import urllib.error
from pathlib import Path

from .config import DEAD_LINK_MARKERS

UA = {"User-Agent": "Mozilla/5.0 (career-fair-hub link checker)"}
# Some QR generators only redirect when you hit /go on the short link
GO_SUFFIX_HOSTS = ("qr.generatorqr.com",)


def resolve_url(url, timeout=15):
    """Follow redirects; return (final_url, http_status, verdict)."""
    if not url.startswith("http"):
        return url, None, "skipped (not http)"
    tried = [url] + ([url.rstrip("/") + "/go"] if any(h in url for h in GO_SUFFIX_HOSTS) else [])
    final, status, err = url, None, None
    for u in tried:
        try:
            req = urllib.request.Request(u, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                final, status = resp.geturl(), resp.status
            if final.rstrip("/") != u.rstrip("/"):
                break
        except urllib.error.HTTPError as e:
            final, status, err = e.geturl() or u, e.code, None
        except Exception as e:  # network error, timeout, TLS…
            err = type(e).__name__
    if err and status is None:
        return final, None, f"error ({err})"
    if any(m in final for m in DEAD_LINK_MARKERS):
        return final, status, "DEAD (expired QR — redirects to generator's site)"
    if status in (401, 403):
        return final, status, "ok (needs sign-in)"
    if status == 999:
        return final, status, "ok (LinkedIn blocks automated checks)"
    if status in (400, 429):
        return final, status, "unclear (site rejects automated checks) — open in a browser"
    if status and status >= 400:
        return final, status, f"DEAD ({status})"
    return final, status, "ok"


def check_links(fair_dir, companies):
    fair_dir = Path(fair_dir)
    urls = {}
    for c in companies:
        for l in c["links"]:
            urls.setdefault(l["url"], []).append(f"{c['name']} — {l['label']}")
    raw = fair_dir / "work" / "qr" / "qr_raw.json"
    if raw.exists():
        for r in json.loads(raw.read_text(encoding="utf-8")):
            urls.setdefault(r["text"], []).append(f"QR in {r['source']}")
    report = []
    for url, used_by in urls.items():
        final, status, verdict = resolve_url(url)
        report.append({"url": url, "final_url": final, "status": status, "verdict": verdict, "used_by": used_by})
        flag = "" if verdict.startswith(("ok", "skipped")) else "  <-- CHECK"
        print(f"[{verdict}] {url[:80]} -> {final[:80]}{flag}")
    out = fair_dir / "work" / "qr" / "link_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    bad = [r for r in report if not r["verdict"].startswith(("ok", "skipped"))]
    print(f"\n{len(report)} links checked, {len(bad)} need attention -> {out}")
    return report
