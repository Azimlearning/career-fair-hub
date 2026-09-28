"""Career Fair Hub CLI.

  python -m cfhub new 2027-03-uxfair --name "UX Career Fair 2027" --short UXF27
  python -m cfhub ingest <fair>        raw zip/photos/pdf -> processed JPGs + booklet PNGs
  python -m cfhub batches <fair>       split images into batches for booth-extractor subagents
  python -m cfhub merge <fair>         batch_*.json -> data/companies.draft.json (deduped)
  python -m cfhub scan-qr <fair>       decode every QR -> work/qr/qr_raw.json
  python -m cfhub qr-index <fair>      classify QR codes against companies.json -> work/qr/qr_index.json
  python -m cfhub check-links <fair>   follow every link, flag expired/dead ones
  python -m cfhub validate <fair>      sanity-check data/companies.json
  python -m cfhub build [--fair X]     share copy for each fair + hub master tracker
  python -m cfhub list                 list fairs
"""
import argparse
import sys

from . import fairs as F


def main(argv=None):
    p = argparse.ArgumentParser(prog="cfhub", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("fair_id")
    n.add_argument("--name", required=True)
    n.add_argument("--short")
    n.add_argument("--organiser", default="")
    n.add_argument("--venue", default="")
    n.add_argument("--dates", nargs="*", default=[])
    for cmd in ("ingest", "batches", "merge", "scan-qr", "qr-index", "check-links", "validate"):
        sp = sub.add_parser(cmd)
        sp.add_argument("fair")
        if cmd == "batches":
            sp.add_argument("--size", type=int, default=15)
    b = sub.add_parser("build")
    b.add_argument("--fair", help="only rebuild this fair's share copy (master always covers all fairs)")
    b.add_argument("--seed", help="legacy master .xlsx to import tracker values from (first build only)")
    b.add_argument("--seed-fair", help="fair short name to assign to rows in the seed file")
    b.add_argument("--no-master", action="store_true")
    sub.add_parser("list")
    a = p.parse_args(argv)

    if a.cmd == "new":
        d = F.new_fair(a.fair_id, a.name, a.short, a.organiser, a.venue, a.dates)
        print(f"created {d}\nNext: drop photos zip / booklet PDF into {d / 'raw'} and run `python -m cfhub ingest {a.fair_id}`")
    elif a.cmd == "list":
        for d in F.list_fairs():
            m = F.load_meta(d)
            print(f"{d.name:28} {m.get('short_name', ''):10} {len(F.load_companies(d)):4} companies  {m.get('name', '')}")
    elif a.cmd == "ingest":
        from .ingest import ingest
        ingest(F.resolve(a.fair))
    elif a.cmd == "batches":
        from .ingest import make_batches
        for b_ in make_batches(F.resolve(a.fair), a.size):
            print(f"{b_['id']:4} {b_['kind']:8} {len(b_['files']):3} files -> {b_['output']}")
    elif a.cmd == "merge":
        from .merge import merge
        merge(F.resolve(a.fair))
    elif a.cmd == "scan-qr":
        from .qr import scan
        scan(F.resolve(a.fair))
    elif a.cmd == "qr-index":
        from .qr import build_index
        d = F.resolve(a.fair)
        build_index(d, F.load_companies(d))
    elif a.cmd == "check-links":
        from .links import check_links
        d = F.resolve(a.fair)
        check_links(d, F.load_companies(d))
    elif a.cmd == "validate":
        d = F.resolve(a.fair)
        probs = F.validate(F.load_companies(d))
        print("\n".join(probs) if probs else "companies.json looks good")
        sys.exit(1 if probs else 0)
    elif a.cmd == "build":
        from .excel import build_share, build_master
        targets = [F.resolve(a.fair)] if a.fair else F.list_fairs()
        for d in targets:
            probs = F.validate(F.load_companies(d))
            for pr in probs:
                print(f"! {d.name}: {pr}")
            build_share(d)
        if not a.no_master:
            build_master(seed=a.seed, seed_fair=a.seed_fair)


if __name__ == "__main__":
    main()
