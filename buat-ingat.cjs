// Cara ingat (mnemonik) kanji N5/N4, permintaan 20 Nov 2026.
// Sumber: scripts/kanji/ingat-n5.tsv, ingat-n4.tsv  (kanji|bagian huruf:arti;...|cerita)
// Kaitkan bunyi (boleh kosong): scripts/kanji/bunyi-n5.tsv, bunyi-n4.tsv  (kanji|teks, **tebal**)
// Menulis field m = { b: [[huruf, arti], ...], s: "cerita", u?: "kaitan bunyi" } ke content/kanji.json.
// Pakai: node scripts/buat-ingat.cjs   (juga dipanggil otomatis di akhir buat-kanji.cjs)
const fs = require("fs"), path = require("path");
const F = path.join(__dirname, "../content/kanji.json");
const d = JSON.parse(fs.readFileSync(F, "utf8"));
for (const lv of ["n5", "n4"]) {
  const peta = new Map();
  for (const l of fs.readFileSync(path.join(__dirname, "kanji", `ingat-${lv}.tsv`), "utf8").split("\n")) {
    if (!l.trim() || l.startsWith("#")) continue;
    const [k, b, s] = l.split("|");
    if (!s) throw new Error(`ingat-${lv}.tsv: baris rusak: ${l}`);
    peta.set(k, { b: b ? b.split(";").map((x) => x.split(":")) : [], s: s.trim() });
  }
  for (const l of fs.readFileSync(path.join(__dirname, "kanji", `bunyi-${lv}.tsv`), "utf8").split("\n")) {
    if (!l.trim() || l.startsWith("#")) continue;
    const i = l.indexOf("|"), k = l.slice(0, i), u = l.slice(i + 1).trim();
    if (!peta.has(k)) throw new Error(`bunyi-${lv}.tsv: ${k} tidak ada di ingat-${lv}.tsv`);
    if (u) peta.get(k).u = u;
  }
  const kurang = d[lv].filter((x) => !peta.has(x.k)).map((x) => x.k);
  if (kurang.length) console.warn(`ingat ${lv}: belum ada cara ingat untuk ${kurang.join("")}`);
  for (const x of d[lv]) { if (peta.has(x.k)) x.m = peta.get(x.k); else delete x.m; }
  console.log(`ingat ${lv}: ${d[lv].filter((x) => x.m).length}/${d[lv].length}, bunyi ${d[lv].filter((x) => x.m?.u).length}`);
}
// Rantai (23 Nov): bagian yang juga kanji N5/N4 DAN artinya cocok dengan arti kanji itu (木:pohon = 木 "pohon").
// Bagian yang cuma mirip bentuk (十:rumput, 月:daging, 口:kotak) tidak dihitung, jadi rantai palsu tidak muncul.
// Hasil: m.d = induk (kanji yang sudah dikenal). "Dipakai di" dihitung balik di lib/rantai.ts.
const ARTI = new Map([...d.n5, ...d.n4].map((x) => [x.k, x.a.toLowerCase().split(/,\s*/)]));
const cocok = (h, ar) => { const a = ar.toLowerCase().replace(/\(.*?\)/g, "").trim(); return ARTI.get(h).some((x) => x.includes(a) || a.includes(x)); };
let nR = 0;
for (const x of [...d.n5, ...d.n4]) {
  if (!x.m) continue;
  const dari = [...new Set(x.m.b.filter(([h, ar]) => h !== x.k && ARTI.has(h) && cocok(h, ar)).map(([h]) => h))];
  if (dari.length) { x.m.d = dari; nR++; } else delete x.m.d;
}
console.log(`rantai: ${nR} kanji punya induk`);
fs.writeFileSync(F, JSON.stringify(d));
