import createClient from "openapi-fetch";

import type { paths } from "@/api/schema";

const BASE_URL = import.meta.env.VITE_API_URL;

if (!BASE_URL) {
  throw new Error("VITE_API_URL is not set — fill it in .env");
}

export const api = createClient<paths>({
  baseUrl: BASE_URL,
  credentials: "include",
});
