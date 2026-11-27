// Impor data lowongan dari file "Loker Kerja Jepang.html" (data dari SISKOP2MI & Maha-Job) ke public/data/jobs.json.
// Pakai: node scripts/impor-loker.cjs "<path ke Loker Kerja Jepang.html>"
// Ulangi setiap file loker diperbarui. Data dimuat halaman /jobs/ saat dibuka (tidak ikut bundel JS).
const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(process.argv[2], "utf8");
const m = html.match(/<script[^>]*id="data"[^>]*>([\s\S]*?)<\/script>/);
if (!m) throw new Error("blok data tidak ditemukan");
const d = JSON.parse(m[1]);
const hariIni = new Date().toISOString().slice(0, 10);
d.jobs = d.jobs.filter((j) => !j.end || j.end >= hariIni); // buang yang sudah lewat
fs.writeFileSync(path.join(__dirname, "../public/data/jobs.json"), JSON.stringify(d));
console.log(d.jobs.length, "lowongan, diambil", d.fetched);
