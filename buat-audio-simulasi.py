"""Audio soal mendengar Simulasi JFT/JLPT -> public/audio/bank/<level>-<n>.mp3 (satu sprite per Uji, hanya dimuat
saat Uji itu dibuka) + public/audio/bank/<level>.json (peta potongan semua Uji level itu: {"<n>": {kunci: [mulai, durasi]}}).
Peta per Uji disimpan di scripts/audio-bank/ (bukan di public, supaya jumlah file situs tidak membengkak). Sumber: baris `dengar` di semua public/data/bank/*.json.
  pip install pyopenjtalk numpy scipy
  python scripts/buat-audio-simulasi.py <folder berisi mei_normal.htsvoice & takumi_normal.htsvoice>
Kunci = teks tanpa spasi/tanda baca; awalan "l:" = suara laki-laki (Takumi), tanpa awalan = perempuan (Mei).
Suara: HTS Voice "Mei" & "Takumi" (c) Nagoya Institute of Technology, CC BY 3.0.
"""
import glob
import json, os, re, subprocess, sys, tempfile
import numpy as np, pyopenjtalk
from pyopenjtalk.htsengine import HTSEngine
from scipy.io import wavfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(AKAR, "scripts/audio-bank")
kunci = lambda t: re.sub(r"[\s、。・＿　!?！？]", "", t)

def sprite(eng, baris, tujuan):
    potong, peta, pos, sr = [], {}, 0, 48000
    for siapa, t in baris:
        e = eng[siapa]; e.set_speed(0.95)
        x = e.synthesize(pyopenjtalk.extract_fullcontext(re.sub(r"[ 　＿]+", "", t)))
        sr = e.get_sampling_frequency()
        a = np.abs(x); i = np.where(a > 300)[0]
        if len(i): x = x[max(0, i[0] - int(.03 * sr)): i[-1] + int(.08 * sr)]
        k = ("l:" if siapa == "l" else "") + kunci(t)
        peta[k] = [round(pos / sr, 3), round(len(x) / sr, 3)]
        jeda = np.zeros(int(.25 * sr))
        potong += [x, jeda]; pos += len(x) + len(jeda)
    with tempfile.TemporaryDirectory() as d:
        w = os.path.join(d, "s.wav")
        wavfile.write(w, sr, np.clip(np.concatenate(potong), -32768, 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", w, "-ac", "1", "-ar", "44100", "-b:a", "40k", tujuan + ".mp3"], check=True)
    json.dump(peta, open(os.path.join(CACHE, os.path.basename(tujuan) + ".json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(os.path.basename(tujuan), len(peta), "potong,", round(pos / sr), "detik")

def main(folder, semua=False):
    """Satu sprite per Uji: public/audio/bank/<level>-<n>.mp3/json (dimuat saat Uji itu dibuka).
    Sprite yang sudah lebih baru dari JSON soalnya dilewati, kecuali pakai --semua."""
    eng = {"p": HTSEngine(os.path.join(folder, "mei_normal.htsvoice").encode()),
           "l": HTSEngine(os.path.join(folder, "takumi_normal.htsvoice").encode())}
    os.makedirs(os.path.join(AKAR, "public/audio/bank"), exist_ok=True); os.makedirs(CACHE, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(AKAR, "public/data/bank/*.json"))):
        tujuan = os.path.join(AKAR, "public/audio/bank", os.path.basename(f)[:-5])
        c = os.path.join(CACHE, os.path.basename(tujuan) + ".json")
        if not semua and os.path.exists(c) and os.path.exists(tujuan + ".mp3") and os.path.getmtime(c) > os.path.getmtime(f):
            continue
        baris = []
        for q in json.load(open(f, encoding="utf8")):
            baris += [tuple(x) for x in q.get("dengar") or []]
        baris = list(dict.fromkeys(baris))
        if baris: sprite(eng, baris, tujuan)
    # gabung peta per level
    level = {}
    for c in sorted(glob.glob(os.path.join(CACHE, "*-*.json"))):
        lv, n = os.path.basename(c)[:-5].rsplit("-", 1)
        level.setdefault(lv, {})[n] = json.load(open(c, encoding="utf8"))
    for lv, isi in level.items():
        json.dump(isi, open(os.path.join(AKAR, "public/audio/bank", lv + ".json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for lama in glob.glob(os.path.join(AKAR, "public/audio/bank/*-*.json")): os.remove(lama)

if __name__ == "__main__":
    main(sys.argv[1], "--semua" in sys.argv)
