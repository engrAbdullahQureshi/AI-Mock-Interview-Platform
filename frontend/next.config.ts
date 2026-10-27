import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Client-rendered app behind auth — opt out of strict prerender features. */
  cacheComponents: false,
  partialPrefetching: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
