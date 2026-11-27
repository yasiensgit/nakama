"""Buat audio latihan (suara sintesis gaya ujian, bukan Yuki Sensei) jadi satu file sprite.

Jalankan ulang setiap ada teks Jepang baru:
  pip install pyopenjtalk numpy scipy
  python scripts/buat-audio.py <folder berisi mei_normal.htsvoice & takumi_normal.htsvoice> [--hanya-kanji-atas]
Suara: HTS Voice "Mei" & "Takumi" (c) Nagoya Institute of Technology, MMDAgent, CC BY 3.0.
Hasil: public/audio/suara.mp3 + public/audio/suara.json {kunci: [mulai_detik, durasi_detik]}.
Kunci = teks tanpa spasi/、。・＿. Awalan "l:" = suara laki-laki, "s:" = versi pelan (dialog).
"""
import glob, json, os, re, subprocess, sys, tempfile
import numpy as np, pyopenjtalk
from pyopenjtalk.htsengine import HTSEngine
from scipy.io import wavfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JP = r"ぁ-ゟ゠-ヿㇰ-ㇿ一-鿿、。・ー"
kunci = lambda t: re.sub(r"[\s、。・＿　!?！？]", "", t)

def kumpulkan():
    keys = {}
    pola = re.compile(r"[%s](?:[%s ＿　]*[%s])?" % (JP, JP, JP))
    for pat in ["content/**/*.ts", "content/**/*.json", "components/**/*.tsx", "lib/**/*.ts"]:
        for f in glob.glob(os.path.join(AKAR, pat), recursive=True):
            if os.path.basename(f).startswith("kanji"): continue  # punya sprite sendiri (kanji.mp3)
            for m in pola.finditer(open(f, encoding="utf8").read()):
                baris = m.group(0)
                for t in [baris] + re.split(r"[ ＿　]+", baris) + re.split(r"[ ＿　、。・]+", baris):
                    k = kunci(t)
                    if k and re.search(r"[ぁ-ヿ一-鿿]", k):
                        keys.setdefault(k, t.strip(" ＿　"))
    return keys

def dialog():
    """Baris dialog di latihan.ts: (siapa, jp)."""
    s = open(os.path.join(AKAR, "content/latihan.ts"), encoding="utf8").read()
    return re.findall(r'siapa: "([^"]+)", jp: "([^"]+)"', s)

PEREMPUAN = {"リナ", "サラ", "ユキ"}

def main(folder):
    mei = HTSEngine(os.path.join(folder, "mei_normal.htsvoice").encode())
    takumi = HTSEngine(os.path.join(folder, "takumi_normal.htsvoice").encode())
    def suara(teks, eng, speed):
        # bahasa Jepang tidak berspasi: spasi di teks belajar jangan dibaca sebagai jeda
        teks = re.sub(r"[ 　＿]+", "", teks).lstrip("ー・")
        lab = pyopenjtalk.extract_fullcontext(teks)
        if len(lab) < 3: return None, None  # tidak ada bunyi (simbol saja)
        eng.set_speed(speed)
        x = eng.synthesize(lab)
        sr = eng.get_sampling_frequency()
        # buang hening di awal/akhir
        a = np.abs(x); i = np.where(a > 300)[0]
        if len(i): x = x[max(0, i[0] - int(.03 * sr)): i[-1] + int(.08 * sr)]
        return x, sr
    if "--hanya-kanji-atas" in sys.argv: return kanji_atas(mei, suara)
    tugas = [(k, t, mei, 0.95) for k, t in kumpulkan().items()]
    for siapa, jp in dialog():
        eng = mei if siapa in PEREMPUAN else takumi
        pre = "" if siapa in PEREMPUAN else "l:"
        if pre: tugas.append((pre + kunci(jp), jp, eng, 0.95))
        tugas.append(("s:" + pre + kunci(jp), jp, eng, 0.7))
    tulis(tugas, "suara", "40k", suara)
    # sprite terpisah untuk Tabel Kanji (hanya dimuat di halaman kanji): bacaan contoh kata + on/kun
    kj = json.load(open(os.path.join(AKAR, "content/kanji.json"), encoding="utf8"))
    bacaan = [c[1] for x in kj["n5"] + kj["n4"] for c in x["c"]]
    bacaan += json.load(open(os.path.join(AKAR, "content/kanji-bunyi.json"), encoding="utf8"))
    tulis([(kunci(t), t, mei, 0.95) for t in dict.fromkeys(bacaan)], "kanji", "32k", suara)
    kanji_atas(mei, suara)

def kanji_atas(mei, suara):
    """N3–N1: satu sprite per bagian 100 kanji (kanji-n3-1.mp3, ...), dimuat saat bagian itu dibuka."""
    bagian = json.load(open(os.path.join(AKAR, "content/kanji-bunyi-atas.json"), encoding="utf8"))
    for nama, bacaan in bagian.items():
        tulis([(kunci(t), t, mei, 0.95) for t in bacaan], nama, "32k", suara)

def tulis(tugas, nama, br, suara):
    potong, peta, pos, sr = [], {}, 0, 48000
    jeda = None
    for k, t, eng, sp in tugas:
        x, s2 = suara(t, eng, sp)
        if x is None: continue
        sr = s2
        if jeda is None: jeda = np.zeros(int(.25 * sr))
        peta[k] = [round(pos / sr, 3), round(len(x) / sr, 3)]
        potong += [x, jeda]; pos += len(x) + len(jeda)
    with tempfile.TemporaryDirectory() as d:
        w = os.path.join(d, "s.wav")
        wavfile.write(w, sr, np.clip(np.concatenate(potong), -32768, 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", w, "-ac", "1", "-ar", "44100", "-b:a", br,
                        os.path.join(AKAR, f"public/audio/{nama}.mp3")], check=True)
    json.dump(peta, open(os.path.join(AKAR, f"public/audio/{nama}.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(nama, len(peta), "potong,", round(pos / sr), "detik")

if __name__ == "__main__":
    main(sys.argv[1])
