// Ambil urutan goresan hiragana & katakana dari KanjiVG (CC BY-SA 3.0, Ulrich Apel, kanjivg.tagaini.net)
// ke content/goresan.json: { "あ": ["M...", ...] } (koordinat viewBox 0 0 109 109, urut sesuai goresan).
// Pakai: node scripts/ambil-goresan.cjs
const fs = require("fs");
const path = require("path");
const hira = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
  + "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゃゅょっ";
const kata = [...hira].map((c) => String.fromCharCode(c.charCodeAt(0) + 0x60)).join("") + "ー";
(async () => {
  const out = {};
  for (const ch of [...hira, ...kata]) {
    const kode = ch.codePointAt(0).toString(16).padStart(5, "0");
    const r = await fetch(`https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/${kode}.svg`);
    if (!r.ok) { console.warn("tidak ada:", ch); continue; }
    const svg = await r.text();
    out[ch] = [...svg.matchAll(/<path[^>]*\sd="([^"]+)"/g)].map((m) => m[1]);
  }
  fs.writeFileSync(path.join(__dirname, "../content/goresan.json"), JSON.stringify(out));
  console.log(Object.keys(out).length, "huruf");
})();
