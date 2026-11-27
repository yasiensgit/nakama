# Kelas Nakama · website (MVP)

Next.js (App Router) + TypeScript, ekspor statis. Gaya neo-brutalism playful dengan palet Jepang (washi, sumi, ai, shu).

## Jalankan
```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # hasil statis di folder out/
```

## Data
- `content/kurikulum.json` = satu sumber data kelas, modul, bab, harga (salinan dari `kurikulum/kurikulum.json` proyek).
- `content/bab/bab-X-Y.json` = isi bab Modul 0–1, dibuat dari `materi/modul-*/data/bab-*.js`.
- Perbarui keduanya dari folder proyek: `node scripts/impor-materi.cjs /mnt/project-files`

## Halaman
- `/` Beranda · `/alur/` Alur Belajar · `/belajar/0-1/` … `/belajar/1-7/` halaman bab · `/kana/` Tabel Kana · `/harga/` Harga

## Status MVP
- Progres, kuis, dan "Cek dirimu" disimpan di localStorage browser (akun Supabase menyusul).
- Video sensei: slot kosong sampai video final siap.
- Suara: Web Speech API `ja-JP` sementara.
- Pembayaran belum aktif; harga dibaca dari kurikulum.json.
- Nama, tagline, dan Instagram di `lib/config.ts`; logo di `public/brand/` (dari brand/logo-final).
