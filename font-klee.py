# Salin potongan font Klee One SemiBold (npm @fontsource/klee-one, SIL OFL 1.1) yang memuat huruf yang dipakai situs
# ke public/fonts/klee-one/ + klee-one.css. Jalankan ulang setelah data kanji/kosakata/pola bertambah:
#   npm i @fontsource/klee-one && python3 scripts/font-klee.py
import re, glob, os, shutil
SRC = "node_modules/@fontsource/klee-one"
DST = "public/fonts/klee-one"
used = set()
for f in glob.glob("content/**/*.json", recursive=True) + glob.glob("public/data/*.json") + glob.glob("lib/*.ts") + glob.glob("content/*.ts") + glob.glob("components/*.tsx") + glob.glob("app/**/*.tsx", recursive=True):
    used |= {ch for ch in open(f, encoding="utf-8").read() if ord(ch) >= 0x3000}
css = open(f"{SRC}/600.css").read()
os.makedirs(DST, exist_ok=True)
out = []
for b in re.findall(r"@font-face \{(.*?)\}", css, re.S):
    fn = re.search(r"url\(\./files/([^)]+\.woff2)\)", b).group(1)
    rng = re.search(r"unicode-range: ([^;]+);", b).group(1)
    cps = set()
    for r in rng.split(","):
        r = r.strip()[2:]
        if "-" in r:
            a, c = r.split("-"); cps |= set(range(int(a, 16), int(c, 16) + 1))
        else:
            cps.add(int(r, 16))
    if any(ord(ch) in cps for ch in used):
        shutil.copy(f"{SRC}/files/{fn}", f"{DST}/{fn}")
        out.append(f"@font-face{{font-family:'Klee One';font-style:normal;font-display:swap;font-weight:600;src:url(./{fn}) format('woff2');unicode-range:{rng}}}")
open(f"{DST}/klee-one.css", "w").write("/* Klee One SemiBold (Fontworks, SIL OFL 1.1) — hanya potongan yang dipakai situs. Dibuat ulang: scripts/font-klee.py */\n" + "\n".join(out) + "\n")
shutil.copy(f"{SRC}/LICENSE", f"{DST}/OFL.txt")
print(len(used), "karakter,", len(out), "potongan")
