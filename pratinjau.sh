#!/usr/bin/env bash
# Bangun versi pratinjau satu-halaman (rute di hash) untuk dipublikasikan sebagai artifact claude.ai.
# Pakai: bash scripts/pratinjau.sh <folder-tujuan>
set -euo pipefail
DEST=${1:?folder tujuan}
NEXT_PUBLIC_PREVIEW=1 npx next build >/dev/null
rm -rf "$DEST" && mkdir -p "$DEST/brand"
cp out/index.html out/icon.svg out/apple-icon.png "$DEST/"
cp public/brand/kelas-nakama-ikon.svg public/brand/kelas-nakama-logo.svg public/brand/nakama-preloved-logo.svg "$DEST/brand/"
[ -d public/video ] && cp -r public/video "$DEST/video"
[ -d public/audio ] && cp -r public/audio "$DEST/audio"
[ -d public/data ] && cp -r public/data "$DEST/data"
[ -d public/fonts ] && cp -r public/fonts "$DEST/fonts"
# nama berawalan _ ditolak artifact: _next -> nx; hanya file yang dipakai index.html
for f in $(grep -o '\./_next/[^"?\\]*' out/index.html | sort -u); do
  mkdir -p "$DEST/$(dirname "${f/_next/nx}")"; cp "out/${f#./}" "$DEST/${f/_next/nx}"
done
grep -rl "\./_next/" "$DEST" | xargs sed -i 's#\./_next/#./nx/#g'
sed -i 's#href="/icon.svg#href="./icon.svg#g; s#href="/apple-icon.png#href="./apple-icon.png#g' "$DEST/index.html"
# kembalikan build biasa
npx next build >/dev/null
echo "pratinjau siap di $DEST"
