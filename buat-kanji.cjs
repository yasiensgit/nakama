// Bangun content/kanji.json (N5 & N4, ikut bundle) + public/data/goresan-kanji.json
// + public/data/kanji-n3.json, -n2, -n1 (dimuat saat tab level dibuka; isi data + goresan).
// Sumber:
//  - scripts/kanji/n5.tsv, n4.tsv: arti Indonesia, tema, on/kun, contoh kata (ditulis manual)
//  - scripts/kanji/n3.tsv, n2.tsv, n1.tsv: sama tanpa tema, urut dari yang paling sering dipakai
//  - kanji-data (davidluzgouveia/kanji-data, MIT; data KANJIDIC CC BY-SA + level JLPT Waller/tanos): daftar N3–N1 & jumlah goresan
//  - KanjiVG (CC BY-SA 3.0, Ulrich Apel): urutan goresan N5 & N4
// Pakai: node scripts/buat-kanji.cjs <path/kanji.json dari kanji-data>
const fs = require("fs");
const path = require("path");
const K = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
// Kanji yang di daftar Waller ada di level lebih tinggi (atau tidak ada), tapi di daftar lain
// (JLPT lama level 4/3, Genki, Minna no Nihongo bab awal) sudah diajarkan di level ini → label "tambahan".
const TAMBAHAN = {
  5: [..."目道言分口古買花耳足多社週魚手空飲新安立駅少店会私"],
  4: [..."村短働弱薬説遠低暑乗区民寒所便合林顔産市都池洗光首門太軽暗好菜県声回森頭引進"],
};
const baca = (f) => fs.readFileSync(path.join(__dirname, "kanji", f), "utf8").split("\n")
  .filter((l) => l.trim() && !l.startsWith("#")).map((l) => {
    const b = l.split("|");
    const [k, a, t, on, kun, c] = b.length === 6 ? b : [b[0], b[1], "", ...b.slice(2)];
    return { k, a, t, on: on === "—" ? [] : on.split("、"), kun: kun === "—" ? [] : kun.split("、"),
      c: c.split(";").map((x) => x.split(":")) };
  });
const n5 = baca("n5.tsv"), n4 = baca("n4.tsv");
const sudah = new Set([...n5, ...n4].map((x) => x.k));
const lv = (n) => Object.keys(K).filter((k) => K[k].jlpt_new === n && !sudah.has(k))
  .sort((a, b) => (K[a].freq ?? 9999) - (K[b].freq ?? 9999));
const atas = { n3: baca("n3.tsv"), n2: baca("n2.tsv"), n1: baca("n1.tsv") };
for (const [n, L] of Object.entries(atas)) {
  const harus = lv(+n[1]).join(""), ada = L.map((x) => x.k).join("");
  if (harus !== ada) throw new Error(`${n}.tsv tidak sama dengan daftar ${n.toUpperCase()} (urutan/isi)`);
}
const CACHE = path.join(require("os").tmpdir(), "kanjivg-cache");
fs.mkdirSync(CACHE, { recursive: true });
(async () => {
  const gor = {};
  const semua = [...n5, ...n4];
  const ambil = async ({ k }) => {
    const kode = k.codePointAt(0).toString(16).padStart(5, "0");
    const f = path.join(CACHE, kode + ".svg");
    let svg = fs.existsSync(f) ? fs.readFileSync(f, "utf8") : null;
    if (!svg) {
      const r = await fetch(`https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/${kode}.svg`);
      if (!r.ok) { console.warn("goresan tidak ada:", k); return; }
      svg = await r.text(); fs.writeFileSync(f, svg);
    }
    gor[k] = [...svg.matchAll(/<path[^>]*\sd="([^"]+)"/g)].map((m) => m[1]);
  };
  const tinggi = Object.values(atas).flat();
  for (const L of [semua, tinggi]) for (let i = 0; i < L.length; i += 16) await Promise.all(L.slice(i, i + 16).map(ambil));
  const isi = (L, n) => L.map((x) => ({ ...x, g: gor[x.k]?.length ?? K[x.k]?.strokes, ...(TAMBAHAN[n]?.includes(x.k) ? { tb: 1 } : {}) }));
  const out = { n5: isi(n5, 5), n4: isi(n4, 4), n3: atas.n3.map((x) => x.k).join(""), n2: atas.n2.map((x) => x.k).join(""), n1: atas.n1.map((x) => x.k).join("") };
  for (const [n, L] of Object.entries(atas)) {
    // per level: d = data (tanpa tema), s = goresan per kanji (urutan sama dengan d)
    const d = isi(L, 0).map(({ t, ...y }) => y);
    fs.writeFileSync(path.join(__dirname, `../public/data/kanji-${n}.json`), JSON.stringify({ d, s: L.map((x) => gor[x.k] ?? []) }));
  }
  fs.writeFileSync(path.join(__dirname, "../content/kanji.json"), JSON.stringify(out));
  // bacaan tanpa tanda kurung, supaya ikut masuk sprite audio (scripts/buat-audio.py)
  const bunyi = [...new Set(semua.flatMap((x) => [...x.on, ...x.kun].map((r) => r.replace(/[()]/g, ""))))];
  // N3–N1: bacaan per bagian 100 kanji → sprite audio kanji-n3-1, kanji-n3-2, ... (scripts/buat-audio.py)
  const bagian = {};
  for (const [n, L] of Object.entries(atas)) for (let i = 0; i < L.length; i += 100)
    bagian[`kanji-${n}-${i / 100 + 1}`] = [...new Set(L.slice(i, i + 100).flatMap((x) => [...x.c.map((c) => c[1]), ...[...x.on, ...x.kun].map((r) => r.replace(/[()]/g, ""))]))];
  fs.writeFileSync(path.join(__dirname, "../content/kanji-bunyi-atas.json"), JSON.stringify(bagian));
  fs.writeFileSync(path.join(__dirname, "../content/kanji-bunyi.json"), JSON.stringify(bunyi));
  fs.mkdirSync(path.join(__dirname, "../public/data"), { recursive: true });
  fs.writeFileSync(path.join(__dirname, "../public/data/goresan-kanji.json"), JSON.stringify(Object.fromEntries(semua.map((x) => [x.k, gor[x.k]]).filter((e) => e[1]))));
  console.log("tanpa goresan:", tinggi.filter((x) => !gor[x.k]).map((x) => x.k).join(""));
  console.log("N5", n5.length, "N4", n4.length, "N3", out.n3.length, "N2", out.n2.length, "N1", out.n1.length, "goresan", Object.keys(gor).length);
})();
require("./buat-ingat.cjs");
