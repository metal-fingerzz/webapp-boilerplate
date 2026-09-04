import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach } from "vitest";

import { server } from "./server";

// Started at module scope rather than in a `beforeAll` hook: setup files are
// evaluated before the test file is imported, whereas hooks only run once it
// has been. `openapi-fetch` captures `globalThis.fetch` when the client module
// is first imported, so MSW has to have patched it by then — a `beforeAll`
// would arrive after the client has already kept a reference to the pristine
// `fetch`, and every request would escape the interceptor.
server.listen({ onUnhandledRequest: "error" });

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
