"""Bangun data Pola Kalimat N5/N4 + audio contoh kalimat per modul.

Sumber: scripts/pola/n5.txt, n4.txt (ditulis Kelas Nakama, format lihat kepala n5.txt).
Furigana & romaji dari pyopenjtalk + koreksi GLOBAL/KHUSUS (sama dengan buat-kosakata.py, ditambah KHUSUS di bawah).
Pakai: python scripts/buat-pola.py <folder berisi mei_normal.htsvoice> [--tanpa-audio] [--cek]
Hasil: public/data/pola-n5.json, -n4.json; public/audio/pola-n5-3.mp3/.json, ...
"""
import importlib.util, json, os, re, sys

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("kosa", os.path.join(AKAR, "scripts/buat-kosakata.py"))
kosa = importlib.util.module_from_spec(spec); spec.loader.exec_module(kosa)
kunci = kosa.kunci
# koreksi bacaan khusus kalimat pola: {kalimat: {potongan: bacaan}}
kosa.GLOBAL.update({"日本人": "にほんじん"})
kosa.KHUSUS.update({
    "急いで帰りました。": {"帰り": "かえり"},
    "一か月に一回国に電話します。": {"一か月": "いっかげつ", "一回": "いっかい"},
    "一週間に二回ジムへ行きます。": {"一週間": "いっしゅうかん"},
    "先生方、こちらへどうぞ。": {"方": "がた"},
    "彼は眠そうな顔をしています。": {"眠そ": "ねむそ"},
    "駅まで十分ぐらいかかります。": {"十分": "じゅっぷん"},
    "会社まで三十分かかります。": {"三十分": "さんじゅっぷん"},
    "一個ずつ入れてください。": {"一個": "いっこ"},
    "来年、二十歳になります。": {"二十歳": "はたち"},
    "リナさんは二十歳で、学生です。": {"二十歳": "はたち"},
    "会議は三時じゃなくて、四時です。": {"四時": "よじ"},
    "それは何ですか。": {"何": "なん"},
    "これは何ですか。": {"何": "なん"},
    "趣味は何ですか。…歌を歌うことです。": {"何": "なん"},
    "「ほうれんそう」って何ですか。": {"何": "なん"},
    "兄は絵を描くのが上手です。": {"描く": "かく"},
    "この絵はピカソによって描かれました。": {"描か": "かか"},
})

def kalimat(s):
    if "→" in s:  # tabel perubahan bentuk: "書く → 書いて、飲む → 飲んで"
        seg, rom, tts = [], [], []
        for i, pas in enumerate(s.split("、")):
            if i: seg.append(["、"]); rom.append(" · ")
            for j, w in enumerate(pas.split("→")):
                w = w.strip()
                if j: seg.append([" → "]); rom.append(" → ")
                a, b, c = kosa.kalimat(w)
                seg += a; rom.append(b); tts.append(c)
        return seg, "".join(rom), "、".join(tts)
    return kosa.kalimat(s)

# koreksi furigana judul/rumus/pilihan (tanpa konteks kalimat): {id: {"pf"/"rf"/"of": {kanji: bacaan}}}
FURI_KOREKSI = {
    "n5-16": {"of": {"人": "にん"}},
    "n5-104": {"pf": {"中": ""}, "rf": {"中": ""}, "of": {"中": "じゅう", "間": "かん", "後": "ご"}},
    "n5-105": {"of": {"人": "にん"}},
    "n5-106": {"rf": {"方": "がた"}},
    "n4-57": {"rf": {"来": ["く", "こ"]}},
    "n4-85": {"pf": {"方": "かた"}, "rf": {"方": "かた"}, "of": {"方": "かた"}},
    "n4-86": {"of": {"方": "かた"}},
    "n4-129": {"of": {"方": "かた"}},
}

def koreksi_furi(id_, kunci_, seg):
    k = FURI_KOREKSI.get(id_, {}).get(kunci_, {})
    if not seg or not k: return seg
    urut = {c: iter(r) for c, r in k.items() if isinstance(r, list)}  # daftar = bacaan per kemunculan, berurutan
    out = []
    for g in seg:
        if len(g) == 2 and g[0] in k:
            r = k[g[0]]
            if isinstance(r, list): r = next(urut[g[0]])
            g = [g[0]] if r == "" else [g[0], r]
        if len(g) == 1 and out and len(out[-1]) == 1: out[-1] = [out[-1][0] + g[0]]
        else: out.append(g)
    return out if any(len(g) == 2 for g in out) else None

def rubyteks(s):
    """furigana untuk judul/rumus/pilihan: hanya bagian Jepang yang berkanji diberi bacaan; None kalau tidak ada kanji."""
    if not kosa.KANJI.search(s): return None
    seg = []
    for run in re.findall(r"[\u3040-\u30ff\u3400-\u9fffー々]+|[^\u3040-\u30ff\u3400-\u9fffー々]+", s):
        part = kosa.kalimat(run)[0] if kosa.KANJI.search(run) else [[run]]
        for g in part:
            if len(g) == 1 and seg and len(seg[-1]) == 1: seg[-1][0] += g[0]
            else: seg.append(g)
    return seg

# --- sorotan bagian pola di contoh kalimat: "h": [[mulai, akhir], ...] (indeks huruf di kalimat) ---
JPR = r"[\u3040-\u30ff\u3400-\u9fffー々]+"

def batas_token(s):
    b, p = {0}, 0
    for t in kosa.pyopenjtalk.run_frontend(s): p += len(t["string"]); b.add(p)
    return b

def potongan_pola(p):
    """bagian Jepang dari judul & rumus (keterangan dalam kurung di rumus dibuang), terpanjang dulu."""
    src = p["p"] + " " + re.sub(r"[（(][^）)]*[)）]", "", p["rumus"])
    ps = {q for m in re.findall(JPR, src) for q in re.split(r"[・〜～]", m) if q}
    return sorted(ps, key=len, reverse=True)

def sorot_otomatis(s, ps):
    if "→" in s: return []
    tanda, B = [0] * len(s), batas_token(s)
    for q in ps:
        # bentuk berubah (来ました → 来ます): coba awalan yang lebih pendek
        for cand in [q] + ([q[:k] for k in range(len(q) - 1, 1, -1)] if len(q) >= 3 else []):
            kena = False
            for m in re.finditer(re.escape(cand), s):
                if len(cand) == 1 and not kosa.KANJI.search(cand) and (m.start() not in B or m.end() not in B): continue  # partikel harus kata sendiri
                if not any(tanda[m.start():m.end()]):
                    tanda[m.start():m.end()] = [1] * len(cand); kena = True
            if kena: break
    return rentang(tanda)

def rentang(tanda):
    rg, i = [], 0
    while i < len(tanda):
        if tanda[i]:
            j = i
            while j < len(tanda) and tanda[j]: j += 1
            rg.append([i, j]); i = j
        else: i += 1
    return rg

def baca_sorot():
    out = {}
    for l in open(os.path.join(AKAR, "scripts/pola/sorot.txt"), encoding="utf8"):
        l = l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        polos, tanda, buka = "", [], False
        for c in l:
            if c == "[": buka = True
            elif c == "]": buka = False
            else: polos += c; tanda.append(1 if buka else 0)
        out[polos] = rentang(tanda)
    return out
SOROT = None

def sorot(p, jp):
    global SOROT
    if SOROT is None: SOROT = baca_sorot(); SOROT["_dipakai"] = set()
    if jp in SOROT: SOROT["_dipakai"].add(jp); return SOROT[jp]
    return sorot_otomatis(jp, potongan_pola(p))

def potong(s):
    """potongan untuk latihan susun kalimat: partikel & akhiran menempel ke kata sebelumnya."""
    fe = kosa.pyopenjtalk.run_frontend(s.rstrip("。？！"))
    ch = []
    for x in fe:
        nempel = x["pos"] in ("助詞", "助動詞", "記号") or x["pos_group1"] in ("非自立", "接尾")
        if ch and nempel: ch[-1] += x["string"]
        else: ch.append(x["string"])
    # gabung potongan yang terlalu pendek (mis. awalan お)
    out = []
    for c in ch:
        if out and (len(out[-1]) == 1 and not kosa.KANJI.search(out[-1])): out[-1] += c
        else: out.append(c)
    return out

def potong_ruby(seg, a, b):
    """furigana diambil dari kalimat lengkap, lalu dipotong: [sebelum titik-titik, sesudahnya]."""
    out, pos = [[], []], 0
    for g in seg:
        t = g[0]; ujung = pos + len(t)
        if len(g) == 2 or ujung <= a or pos >= b:
            if ujung <= a or (len(g) == 2 and pos < a): out[0].append(g)
            elif pos >= b: out[1].append(g)
        else:
            if pos < a: out[0].append([t[:a - pos]])
            if ujung > b: out[1].append([t[b - pos:]])
        pos = ujung
    return out

def baca(n):
    pola, cur = [], None
    for l in open(os.path.join(AKAR, f"scripts/pola/{n}.txt"), encoding="utf8"):
        l = l.rstrip("\n")
        if l.startswith("#") or not l.strip(): continue
        if l.startswith("@ "):
            bab, kel, p = [x.strip() for x in l[2:].split("|")]
            cur = {"id": f"{n}-{len(pola) + 1}", "bab": bab, "k": kel, "p": p, "ex": []}
            pola.append(cur); continue
        kunci_, _, isi = l.partition(": ")
        if kunci_ == "ex":
            jp, _, ar = isi.partition(" = ")
            cur["ex"].append((jp.strip(), ar.strip()))
        elif kunci_ in ("rumus", "arti", "jelas", "catat", "isi"):
            cur[kunci_] = isi.strip()
        else:
            raise SystemExit(f"{n}: baris tak dikenal: {l}")
    return pola

def olah(n):
    hasil = []
    for p in baca(n):
        assert len(p["ex"]) == 3 and "isi" in p and "rumus" in p, p["p"]
        x = {"id": p["id"], "bab": p["bab"], "k": p["k"], "p": p["p"], "r": p["rumus"], "a": p["arti"], "j": p["jelas"]}
        if p.get("catat"): x["c"] = p["catat"]
        for k, v in (("pf", p["p"]), ("rf", p["rumus"])):
            f = koreksi_furi(p["id"], k, rubyteks(v))
            if f: x[k] = f
        x["ex"], tts = [], {}
        for jp, ar in p["ex"]:
            seg, rom, t = kalimat(jp)
            x["ex"].append({"s": seg, "sb": rom, "a": ar})
            h = sorot(p, jp)
            if h: x["ex"][-1]["h"] = h
            tts[kunci(jp)] = t
        # isi titik-titik
        q, _, pil = p["isi"].partition(" = ")
        pil = [o.strip() for o in pil.split(" / ")]
        assert len(pil) == 4 and len(set(pil)) == 4 and all(pil), (p["p"], pil)
        h = re.search(r"（([^）]*[A-Za-z][^）]*)）", q)
        if h: q = q.replace(h.group(0), "")
        assert q.count("＿＿") == 1, q
        depan, belakang = q.split("＿＿")
        lengkap = depan + pil[0] + belakang
        isi = {"q": potong_ruby(kalimat(lengkap)[0], len(depan), len(depan) + len(pil[0])), "o": pil}
        if h: isi["h"] = h.group(1)
        of = [koreksi_furi(p["id"], "of", rubyteks(o)) or [[o]] for o in pil]
        if any(len(g) > 1 for o in of for g in o): isi["of"] = of
        isi["full"] = lengkap
        tts[kunci(lengkap)] = kosa.kalimat(lengkap)[2]
        x["isi"] = isi
        # susun kalimat: contoh pertama (bukan tabel bentuk) yang punya 3..7 potongan
        for jp, ar in p["ex"]:
            if "→" in jp or "…" in jp: continue
            c = potong(jp)
            if 3 <= len(c) <= 7: x["su"] = {"c": c, "a": ar, "s": jp}; break
        x["_tts"] = tts
        hasil.append(x)
    return hasil

def main():
    data = {n: olah(n) for n in ["n5", "n4"]}
    sisa = set(k for k in SOROT if k != "_dipakai") - SOROT["_dipakai"]
    assert not sisa, f"sorot.txt: kalimat tidak ditemukan: {sisa}"
    if "--cek" in sys.argv:
        for n, L in data.items():
            for x in L:
                for e in x["ex"]:
                    print(x["id"], "".join(g[0] if len(g) == 1 else f"{g[0]}({g[1]})" for g in e["s"]), "|", e["sb"])
        return
    for n, L in data.items():
        for x in L: x["au"] = f"pola-{n}-{'x' if x['bab'] == '+' else x['bab'].split('.')[0]}"
        json.dump([{k: v for k, v in x.items() if not k.startswith("_")} for x in L],
                  open(os.path.join(AKAR, f"public/data/pola-{n}.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        print(n, len(L), "pola,", sum(1 for x in L if "su" in x), "susun")
    if "--tanpa-audio" in sys.argv: return
    from pyopenjtalk.htsengine import HTSEngine
    import numpy as np
    mei = HTSEngine(os.path.join(sys.argv[1], "mei_normal.htsvoice").encode())
    def suara(teks, sp=0.9):
        teks = re.sub(r"[ 　＿〜→]+", "", teks)
        lab = kosa.pyopenjtalk.extract_fullcontext(teks)
        if len(lab) < 3: return None, None
        mei.set_speed(sp); y = mei.synthesize(lab); sr = mei.get_sampling_frequency()
        i = np.where(np.abs(y) > 300)[0]
        if len(i): y = y[max(0, i[0] - int(.03 * sr)): i[-1] + int(.08 * sr)]
        return y, sr
    for n, L in data.items():
        grup = {}
        for x in L:
            for k, t in x["_tts"].items(): grup.setdefault(x["au"], {}).setdefault(k, (t, 0.9))
        for nama, tugas in grup.items(): kosa.tulis(tugas, nama, suara)

if __name__ == "__main__":
    main()
