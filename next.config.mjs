const preview = process.env.NEXT_PUBLIC_PREVIEW === "1";
/** @type {import('next').NextConfig} */
export default {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // Pratinjau artifact: aset dimuat relatif (./_next/...) karena halaman tidak dilayani dari root domain.
  ...(preview ? { assetPrefix: "." } : {}),
};
