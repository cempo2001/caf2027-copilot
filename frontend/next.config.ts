import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// next-intl config: čita src/i18n/request.ts (CLAUDE.md 6.2 — jezik je dio
// rute/sesije, ne samo lokalnog state-a preglednika).
const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Backend (FastAPI, port 8765 — vidi docker-compose.yml) je poseban servis;
  // ovdje se ne proksira preko Next.js-a, api-client.ts gađa ga direktno preko
  // NEXT_PUBLIC_API_URL da bi Server Actions i client fetch koristili istu bazu.
  experimental: {
    serverActions: {
      // Upload dokaza (6.1) ide kroz Server Action; podrazumijevani limit je
      // 1 MB. Backend dozvoljava 25 MB — +1 MB za multipart zaglavlja.
      bodySizeLimit: "26mb",
    },
  },
};

export default withNextIntl(nextConfig);
