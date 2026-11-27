// Salin kurikulum.json + data bab (materi/modul-*/data/bab-*.js) ke folder content/.
// Jalankan: node scripts/impor-materi.cjs /mnt/project-files
const fs = require("fs"), path = require("path");
const src = process.argv[2] || "/mnt/project-files";
const out = path.join(__dirname, "..", "content");
fs.mkdirSync(path.join(out, "bab"), { recursive: true });
fs.copyFileSync(path.join(src, "kurikulum/kurikulum.json"), path.join(out, "kurikulum.json"));
let n = 0;
for (const modul of fs.readdirSync(path.join(src, "materi")).filter((d) => /^modul-\d+$/.test(d))) {
  const dir = path.join(src, "materi", modul, "data");
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir).filter((f) => /^bab-[\d-]+\.js$/.test(f))) {
    const data = require(path.join(dir, f));
    const { slides, ...meta } = data;
    // buang catatan produksi (animasi, cek) yang tidak perlu di website
    const bersih = slides.map(({ animasi, cek, ...s }) => s);
    fs.writeFileSync(path.join(out, "bab", f.replace(/\.js$/, ".json")), JSON.stringify({ ...meta, slides: bersih }, null, 1));
    n++;
  }
}
console.log(`kurikulum + ${n} bab disalin ke content/`);

// indeks impor statis (tanpa fs) supaya data bab bisa dipakai di server maupun browser
const files = fs.readdirSync(path.join(out, "bab")).filter((f) => /^bab-[\d-]+\.json$/.test(f)).sort();
fs.writeFileSync(path.join(out, "bab", "index.ts"),
  "// Dibuat otomatis oleh scripts/impor-materi.cjs. Jangan diedit.\n" +
  files.map((f, i) => `import b${i} from "./${f}";`).join("\n") +
  "\n\nexport const BAB: Record<string, any> = {\n" +
  files.map((f, i) => `  "${f.replace(/^bab-|\.json$/g, "")}": b${i},`).join("\n") + "\n};\n");
