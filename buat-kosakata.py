"""Bangun data Kosakata N5/N4 + audio per bagian 100 kata.

Sumber: scripts/kosakata/n5.tsv, n4.tsv (tulis|baca|arti|jenis|tema|kalimat|arti kalimat), ditulis Kelas Nakama.
Daftar kata: Jonathan Waller (tanos.co.uk) lewat open-anki-jlpt-decks (Jamie Sinclair, MIT).
Bacaan kalimat (furigana) dari pyopenjtalk, dibetulkan dengan KOREKSI di bawah.
Juga: public/data/kotoba-bab-n5.json (Kotoba per bab, dari content/kotoba-bab.ts).
Pakai: python scripts/buat-kosakata.py <folder berisi mei_normal.htsvoice> [--tanpa-audio]
Hasil: public/data/kosakata-n5.json, -n4.json; public/audio/kosakata-n5-1.mp3/.json, ...
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, pyopenjtalk
from scipy.io import wavfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAGIAN = 100
kunci = lambda t: re.sub(r"[\s、。・＿　!?！？〜]", "", t)
hira = lambda s: "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
KANJI = re.compile(r"[一-鿿々]")

# bacaan pyopenjtalk yang salah, berlaku untuk semua kalimat (per token)
GLOBAL = {"この間": "このあいだ", "十日": "とおか", "国": "くに", "太り": "ふとり", "日本": "にほん", "角": "かど",
          "米": "こめ", "表": "おもて", "辺": "へん", "辛い": "からい", "黄色": "きいろ", "会社": "かいしゃ",
          "薬": "くすり", "七": "しち", "山": "やま"}
# koreksi khusus satu kalimat: {kalimat: {potongan: bacaan}}
KHUSUS = {
    "りんごが十あります。": {"十": "とお"},
    "あの方は先生です。": {"方": "かた"},
    "一月に一回国に電話します。": {"一月": "ひとつき"},
    "妹は二十歳です。": {"二十歳": "はたち"},
    "駅まで十分かかります。": {"十分": "じゅっぷん"},
    "明日の会議は十時からです。": {"明日": "あす"},
    "家族は四人です。": {"四人": "よにん"},
    "七月七日は七夕です。": {"七夕": "たなばた"},
    "貿易会社で働いています。": {"会社": "がいしゃ"},
    "ぶどうを一房買いました。": {"一房": "ひとふさ"},
    "祖母は山田町に住んでいます。": {"町": "ちょう"},
    "洗濯機は一階にあります。": {"一階": "いっかい"},
}

def ruby(w, r):
    """[teks, furigana] dengan okurigana di depan/belakang dipisah supaya furigana hanya di atas kanji."""
    if not KANJI.search(w): return [[w]]
    a = 0
    while a < len(w) and not KANJI.search(w[a]) and a < len(r) and hira(w[a]) == r[a]: a += 1
    b = 0
    while b < len(w) - a and not KANJI.search(w[-1 - b]) and b < len(r) - a and hira(w[-1 - b]) == r[-1 - b]: b += 1
    out = []
    if a: out.append([w[:a]])
    out.append([w[a:len(w) - b], r[a:len(r) - b]])
    if b: out.append([w[len(w) - b:]])
    return out

def kalimat(s):
    fe = pyopenjtalk.run_frontend(s)
    # [teks, bacaan, kelas kata, lafal, nempel?]; romaji diberi spasi per kata, akhiran (ます, て, 接尾辞) menempel
    tk = [[x["string"], hira(x["read"]) if x["read"] != "、" else x["string"], x["pos"], hira(x["pron"]).replace("’", ""),
           x["pos"] in ("助動詞", "記号") or (x["pos"] == "助詞" and x["pos_group1"] == "接続助詞") or x["pos_group1"] in ("非自立", "接尾")]
          for x in fe]
    ubah = False
    for t in tk:
        if t[0] in GLOBAL: t[1] = GLOBAL[t[0]]; t[3] = t[1]; ubah = True
    for pot, rd in KHUSUS.get(s, {}).items():
        teks = "".join(t[0] for t in tk); i = teks.find(pot)
        assert i >= 0, (s, pot)
        # gabung token yang menutupi potongan itu
        pos, a, b = 0, None, None
        for j, t in enumerate(tk):
            if a is None and pos + len(t[0]) > i: a = j
            pos += len(t[0])
            if pos >= i + len(pot): b = j; break
        tk[a:b + 1] = [["".join(t[0] for t in tk[a:b + 1]), rd, "名詞", rd, tk[a][4]]]
        ubah = True
    seg = []
    for t in tk:
        for g in ruby(t[0], t[1]):
            if len(g) == 1 and seg and len(seg[-1]) == 1: seg[-1][0] += g[0]  # gabung kana yang berurutan
            else: seg.append(g)
    # romaji: partikel は/へ dibaca wa/e
    bunyi = ""
    for k, t in enumerate(tk):
        b = ("わ" if t[0] == "は" else "え" if t[0] == "へ" else t[1]) if t[2] == "助詞" else t[1]
        bunyi += ("" if k == 0 or t[4] else " ") + b
    # teks untuk suara: token yang dikoreksi diganti kana supaya dibaca benar
    tts = "".join(t[1] if (t[0] in GLOBAL or len(t) and t[2] == "名詞" and t[1] in KHUSUS.get(s, {}).values()) else t[0] for t in tk)
    return seg, bunyi.replace("、", " ").strip(), tts

def baca(n):
    out = []
    # n5-tambahan.tsv = kata di luar daftar JLPT (salam, kata Kotoba bab). Ditaruh di BELAKANG supaya nomor & audio kata lama tetap.
    for nama, tambah in [(n, False), (n + "-tambahan", True)]:
        f = os.path.join(AKAR, f"scripts/kosakata/{nama}.tsv")
        if not os.path.exists(f): continue
        for l in open(f, encoding="utf8"):
            if l.startswith("#") or not l.strip(): continue
            w, r, a, j, t, s, sa = l.rstrip("\n").split("|")
            seg, bunyi, tts = kalimat(s)
            x = {"w": w, "r": r, "a": a, "j": j, "t": t, "s": seg, "sb": bunyi, "sa": sa, "_tts": tts, "_s": s}
            if tambah: x["x"] = 1
            out.append(x)
    return out

def kotoba_bab():
    """content/kotoba-bab.ts -> {bab: [(grup, kana, arti)]} (urutan sama dengan halaman bab)."""
    s = open(os.path.join(AKAR, "content/kotoba-bab.ts"), encoding="utf8").read()
    bagian = re.split(r'\n  "(\d+\.\d+)": \[', s)
    out = {}
    for i in range(1, len(bagian), 2):
        for g, isi in re.findall(r'urai\("([^"]+)", `([^`]*)`', bagian[i + 1]):
            for b in isi.strip().split("\n"):
                jp, _, arti = [y.strip() for y in b.strip().split("|")]
                out.setdefault(bagian[i], []).append((g, jp, arti))
    return out

KATA_ARTI = lambda s: {w for w in re.split(r"[^a-z]+", s.lower()) if len(w) >= 2}
def cocokkan(data, jp, arti):
    """Cari kata di daftar lewat cara baca (tanpa spasi, bentuk pertama "a / b"); kalau homofon, pilih yang artinya nyambung."""
    r = re.sub(r"[\s、〜]", "", jp.split(" / ")[0])
    for n in ["n5", "n4"]:
        calon = [(i, x) for i, x in enumerate(data[n]) if re.sub(r"[\s、〜]", "", x["r"]) == r]
        cocok = [c for c in calon if KATA_ARTI(c[1]["a"]) & KATA_ARTI(arti)]
        if cocok or (calon and len(calon) == 1 and n == "n5"): return n, (cocok or calon)[0][0]
    return None

def kata_bab():
    """bacaan kana -> kode bab, dari contoh kata di slide 'kata' (mis. "くち kuchi · mulut")."""
    import glob
    peta = {}
    for f in sorted(glob.glob(os.path.join(AKAR, "content/bab/bab-*.json"))):
        d = json.load(open(f, encoding="utf8"))
        for sl in d["slides"]:
            for k in sl.get("kata", []) if sl.get("tipe") == "kata" else []:
                t = k.get("arti") or ""
                w, arti = t.split(" ")[0], t.split("·")[-1].strip().lower()
                if w and "·" in t: peta.setdefault(w, []).append((str(d["bab"]), arti))
    return peta

def kotoba_lanjut(data):
    """scripts/kosakata/kotoba-bab-n5.tsv (Modul 2–8) -> {bab: [(grup, (lv, nomor))]}."""
    out, salah = {}, []
    bab = None
    for l in open(os.path.join(AKAR, "scripts/kosakata/kotoba-bab-n5.tsv"), encoding="utf8"):
        l = l.strip()
        if not l or l.startswith("# "): continue
        if l.startswith("## "): bab = l[3:].strip(); out.setdefault(bab, []); continue
        g, isi = l.split(":", 1)
        for t in isi.split():
            n = "n4" if t.endswith("@n4") else "n5"
            t = t.removesuffix("@n4")
            m = re.fullmatch(r"(.+?)\((.+)\)", t)
            w, r = (m.group(1), m.group(2)) if m else (t, None)
            calon = [i for i, x in enumerate(data[n]) if x["w"] == w and (r is None or x["r"] == r)]
            if len(calon) != 1: salah.append(f"{bab} {t} ({len(calon)} cocok)"); continue
            out[bab].append((g.strip(), (n, calon[0])))
    if salah: print("PERINGATAN token kotoba-bab-n5.tsv:", ", ".join(salah))
    return out

def main():
    data = {n: baca(n) for n in ["n5", "n4"]}
    bab = kata_bab()
    for L in data.values():
        for x in L:
            # cocok kalau bacaan sama DAN artinya nyambung (hindari homofon: 雨/飴 あめ)
            kata = [k.strip() for k in re.split(r"[,;()]", x["a"].lower()) if len(k.strip()) > 2]
            kode = {b for b, arti in bab.get(x["r"], []) if any(k in arti or arti in k for k in kata)}
            if kode and x["j"] not in ("ak", "ung"): x["b"] = sorted(kode)
    # Kotoba per bab: {bab: [[grup, ["n5", nomor]], ...]} untuk menu Kotoba tab Per Bab + label bab di detail kata
    peta, hilang = {}, []
    for b, isi in kotoba_bab().items():
        for g, jp, arti in isi:
            c = cocokkan(data, jp, arti)
            if not c: hilang.append(f"{b} {jp}"); continue
            x = data[c[0]][c[1]]
            x["b"] = sorted(set(x.get("b", [])) | {b}, key=lambda k: [int(v) for v in k.split(".")])
            grup = peta.setdefault(b, [])
            if not grup or grup[-1][0] != g: grup.append([g, []])
            grup[-1][1].append([c[0], c[1]])
    sudah = {tuple(r) for v in peta.values() for g in v for r in g[1]}
    dobel = []
    for b, isi in kotoba_lanjut(data).items():
        for g, (n, i) in isi:
            if (n, i) in sudah: dobel.append(f"{b} {data[n][i]['w']}"); continue
            sudah.add((n, i))
            x = data[n][i]
            x["b"] = sorted(set(x.get("b", [])) | {b}, key=lambda k: [int(v) for v in k.split(".")])
            grup = peta.setdefault(b, [])
            if not grup or grup[-1][0] != g: grup.append([g, []])
            grup[-1][1].append([n, i])
    if dobel: print("PERINGATAN kata sudah ada di bab lain (dilewati):", ", ".join(dobel))
    sisa = [x["w"] for i, x in enumerate(data["n5"]) if ("n5", i) not in sudah]
    print(f"Kotoba per bab: {len(sudah)} kata di {len(peta)} bab; N5 belum masuk bab: {len(sisa)}", " ".join(sisa))
    if hilang: print("PERINGATAN kata Kotoba bab tidak ada di daftar (tambahkan ke n5-tambahan.tsv):", ", ".join(hilang))
    json.dump(peta, open(os.path.join(AKAR, "public/data/kotoba-bab-n5.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    os.makedirs(os.path.join(AKAR, "public/data"), exist_ok=True)
    for n, L in data.items():
        json.dump([{k: v for k, v in x.items() if not k.startswith("_")} for x in L],
                  open(os.path.join(AKAR, f"public/data/kosakata-{n}.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        print(n, len(L), "kata")
    if "--tanpa-audio" in sys.argv: return
    from pyopenjtalk.htsengine import HTSEngine
    mei = HTSEngine(os.path.join(sys.argv[1], "mei_normal.htsvoice").encode())
    def suara(teks, sp=0.95):
        teks = re.sub(r"[ 　＿〜]+", "", teks)
        lab = pyopenjtalk.extract_fullcontext(teks)
        if len(lab) < 3: return None, None
        mei.set_speed(sp); x = mei.synthesize(lab); sr = mei.get_sampling_frequency()
        i = np.where(np.abs(x) > 300)[0]
        if len(i): x = x[max(0, i[0] - int(.03 * sr)): i[-1] + int(.08 * sr)]
        return x, sr
    for n, L in data.items():
        for b in range(0, len(L), BAGIAN):
            tugas = {}
            for x in L[b:b + BAGIAN]:
                tugas.setdefault(kunci(x["r"]), (x["r"], 0.95))
                tugas.setdefault(kunci(x["_s"]), (x["_tts"], 0.9))
            tulis(tugas, f"kosakata-{n}-{b // BAGIAN + 1}", suara)

def tulis(tugas, nama, suara):
    potong, peta, pos, sr, jeda = [], {}, 0, 48000, None
    for k, (t, sp) in tugas.items():
        x, s2 = suara(t, sp)
        if x is None: continue
        sr = s2
        if jeda is None: jeda = np.zeros(int(.25 * sr))
        peta[k] = [round(pos / sr, 3), round(len(x) / sr, 3)]
        potong += [x, jeda]; pos += len(x) + len(jeda)
    with tempfile.TemporaryDirectory() as d:
        w = os.path.join(d, "s.wav")
        wavfile.write(w, sr, np.clip(np.concatenate(potong), -32768, 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", w, "-ac", "1", "-ar", "44100", "-b:a", "32k",
                        os.path.join(AKAR, f"public/audio/{nama}.mp3")], check=True)
    json.dump(peta, open(os.path.join(AKAR, f"public/audio/{nama}.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(nama, len(peta), "potong,", round(pos / sr), "detik")

if __name__ == "__main__":
    main()
