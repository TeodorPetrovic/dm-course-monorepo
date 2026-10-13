#!/usr/bin/env python3
"""Nastavni alat: prebacuje kod u STARTER stanje dana (TEACH blokovi -> TODO) ili vraća REŠENJE (git HEAD).

  scripts/teach.sh start NN      # dan NN: njegovi TEACH blokovi postaju TODO; ostali dani ostaju rešeni
  scripts/teach.sh solution [NN] # vrati rešenje (svi dani ili samo NN) iz git HEAD-a
  scripts/teach.sh status        # koji dani su trenutno u starter stanju
  scripts/teach.sh lines [NN]    # broj linija koje se kucaju uživo (po fajlu)
  scripts/teach.sh diff NN       # prikaži šta starter uklanja
  scripts/teach.sh verify        # za svaki dan: start -> kompajlira/importuje/API se diže -> solution -> nema razlike
Blokovi u kodu:  # TEACH dNN: naslov ... # /TEACH   (Python)   //  TEACH dNN: ... // /TEACH  (TS/Vue)
"""
import argparse, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = [ROOT / "apps/api/app", ROOT / "apps/frontend/app", ROOT / "apps/frontend/server"]
EXT = {".py", ".ts", ".vue"}
START = re.compile(r"^(\s*)(#|//)\s*TEACH (d\d\d): ?(.*)$")
END = re.compile(r"^\s*(#|//)\s*/TEACH\s*$")
TODO = re.compile(r"TODO (d\d\d): ")


def files():
    for base in SCAN:
        for p in sorted(base.rglob("*")):
            if p.suffix in EXT and "node_modules" not in p.parts and ".nuxt" not in p.parts:
                yield p


def blocks(text):
    """[(day, title, start_idx, end_idx, indent, comment)] — indeksi linija markera."""
    out, cur = [], None
    for i, line in enumerate(text.split("\n")):
        m = START.match(line)
        if m:
            if cur: raise ValueError(f"ugnježden TEACH na liniji {i+1}")
            cur = (m.group(3), m.group(4).strip(), i, m.group(1), m.group(2))
        elif END.match(line):
            if not cur: raise ValueError(f"/TEACH bez početka na liniji {i+1}")
            out.append((cur[0], cur[1], cur[2], i, cur[3], cur[4])); cur = None
    if cur: raise ValueError("TEACH bez /TEACH")
    return out


def day_files(day=None):
    res = {}
    for p in files():
        b = [x for x in blocks(p.read_text()) if day is None or x[0] == day]
        if b: res[p] = b
    return res


def git(*a, check=True):
    return subprocess.run(["git", "-C", str(ROOT), *a], check=check, capture_output=True, text=True)


def rel(p): return str(p.relative_to(ROOT))


def starter_text(text, day):
    lines = text.split("\n"); n = int(day[1:])
    for d, title, s, e, ind, com in sorted(blocks(text), key=lambda b: -b[2]):
        if d != day: continue
        msg = f"TODO {d}: {title}  (teaching/day-{n:02d}/PLAN.md)"
        stub = [f"{ind}# {msg}", f'{ind}raise NotImplementedError("TODO {d}: {title}")'] if com == "#" else [f"{ind}// {msg}"]
        lines[s:e + 1] = stub
    return "\n".join(lines)


def norm(day):
    return f"d{int(day):02d}"


def cmd_solution(day=None):
    targets = set(day_files(norm(day)) if day else day_files())
    # fajlovi u starter stanju više nemaju markere -> nađi ih po TODO dNN
    for p in files():
        t = p.read_text()
        if any(day is None or m == norm(day) for m in TODO.findall(t)): targets.add(p)
    if targets:
        git("checkout", "HEAD", "--", *[rel(p) for p in sorted(targets)])
    print(f"rešenje vraćeno ({'svi dani' if day is None else norm(day)}): {len(targets)} fajlova")


def cmd_start(day, force=False):
    d = norm(day)
    head = {}
    for p in files():  # izvor je uvek rešenje iz HEAD-a (ne trenutni radni fajl)
        r = git("show", f"HEAD:{rel(p)}", check=False)
        if r.returncode == 0 and any(b[0] == d for b in blocks(r.stdout)): head[p] = r.stdout
    if not head: sys.exit(f"nema TEACH blokova za {d}")
    dirty = [rel(p) for p in head if git("diff", "--quiet", "HEAD", "--", rel(p), check=False).returncode]
    if dirty and not force:
        sys.exit("ovi fajlovi imaju nesačuvane izmene (dodaj --force da ih pregaziš):\n  " + "\n  ".join(dirty))
    cmd_solution()  # jedan dan u starter stanju u isto vreme
    for p, t in head.items(): p.write_text(starter_text(t, d))
    n = sum(sum(e - s - 1 for _, _, s, e, _, _ in blocks(t) if _ == d) for t in head.values())
    print(f"{d} starter: {len(head)} fajlova, {n} linija za kucanje uživo")
    for p in head: print("  ", rel(p))


def cmd_status():
    days = sorted({m for p in files() for m in TODO.findall(p.read_text())})
    print("starter stanje:", ", ".join(days) if days else "nijedan dan (sve je rešenje)")


def count(day=None):
    res = {}
    for p, bl in day_files(day).items():
        for d, title, s, e, *_ in bl:
            res.setdefault(d, {}).setdefault(rel(p), 0); res[d][rel(p)] += e - s - 1
    return res


def cmd_lines(day=None):
    for d, per in sorted(count(norm(day) if day else None).items()):
        be = sum(v for k, v in per.items() if k.startswith("apps/api")); fe = sum(per.values()) - be
        print(f"{d}: backend {be}, frontend {fe}, ukupno {be + fe}")
        if day:
            for k, v in per.items(): print(f"    {v:4d}  {k}")


def cmd_diff(day):
    d = norm(day)
    for p in day_files(d):
        t = p.read_text(); s = starter_text(t, d)
        import difflib
        sys.stdout.writelines(difflib.unified_diff(t.splitlines(True), s.splitlines(True), f"solution/{rel(p)}", f"starter/{rel(p)}"))


def cmd_verify():
    py = ROOT / "apps/api/.venv/bin/python"; ok = True
    probe = ("import os,tempfile;os.environ['DM_MODELS_DIR']=tempfile.mkdtemp();os.environ['DM_LIVE_EVENTS']=tempfile.mktemp();"
             "from fastapi.testclient import TestClient;from app.main import app;c=TestClient(app);"
             "r=c.get('/platform/modules');print(r.status_code)")
    days = sorted(count())
    for d in days:
        cmd_start(int(d[1:]), force=True)
        comp = subprocess.run([str(py), "-m", "compileall", "-q", "app"], cwd=ROOT / "apps/api", capture_output=True)
        imp = subprocess.run([str(py), "-c", probe], cwd=ROOT / "apps/api", capture_output=True, text=True)
        todo = sum(p.read_text().count(f"TODO {d}: ") for p in files())
        cmd_solution()
        clean = git("diff", "--quiet", "HEAD", "--", "apps", check=False).returncode == 0
        good = comp.returncode == 0 and imp.returncode == 0 and todo > 0 and clean
        ok &= good
        print(f"{'PASS' if good else 'FAIL'} {d}: compile={comp.returncode == 0} api_import+start={imp.stdout.strip() or imp.stderr[-200:]} todo_blokova={todo} solution_čist={clean}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["start", "solution", "status", "lines", "diff", "verify"])
    ap.add_argument("day", nargs="?", type=int); ap.add_argument("--force", action="store_true"); a = ap.parse_args()
    if a.cmd in ("start", "diff") and a.day is None: sys.exit("navedi dan, npr. 5")
    {"start": lambda: cmd_start(a.day, a.force), "solution": lambda: cmd_solution(a.day), "status": cmd_status,
     "lines": lambda: cmd_lines(a.day), "diff": lambda: cmd_diff(a.day), "verify": cmd_verify}[a.cmd]()
