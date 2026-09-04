import { HttpResponse, http } from "msw";
import { expect, it } from "vitest";

import { api } from "@/api";

import { server } from "../server";

// The origin is spelled out rather than read back from the environment: the
// point of this test is that the client goes where `.env.test` says, so
// deriving the handler from the same variable would make it tautological.
it("sends requests to the base URL declared by VITE_API_URL", async () => {
  server.use(
    http.get("http://api.test/health-check", () => HttpResponse.json("OK")),
  );

  const { data } = await api.GET("/health-check");

  expect(data).toBe("OK");
});
