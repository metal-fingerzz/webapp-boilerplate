import { setupServer } from "msw/node";

// Deliberately empty: every test declares the responses it needs. A request no
// test stubbed fails loudly (see `onUnhandledRequest` in `setup.ts`) instead of
// quietly falling back to a shared default.
export const server = setupServer();
