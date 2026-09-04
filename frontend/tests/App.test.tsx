import { render, screen } from "@testing-library/react";
import { HttpResponse, delay, http } from "msw";
import { expect, it } from "vitest";

import App from "@/App";

import { server } from "./server";

// Built from the same variable the client reads, so a handler can never end up
// stubbing an origin the application does not actually call.
const HEALTH_CHECK = `${import.meta.env.VITE_API_URL}/health-check`;

it("announces that the API is being contacted while the request is in flight", () => {
  server.use(http.get(HEALTH_CHECK, () => delay("infinite")));

  render(<App />);

  expect(screen.getByText("Contacting the API…")).toBeInTheDocument();
});

it("displays the payload returned by a successful health check", async () => {
  server.use(http.get(HEALTH_CHECK, () => HttpResponse.json("OK")));

  render(<App />);

  expect(await screen.findByText("OK")).toBeInTheDocument();
});

it("reports an error when the API answers with a failing status", async () => {
  server.use(
    http.get(HEALTH_CHECK, () =>
      HttpResponse.json({ detail: "Boom" }, { status: 500 }),
    ),
  );

  render(<App />);

  expect(
    await screen.findByText("The API answered with an error."),
  ).toBeInTheDocument();
});

it("surfaces the reason when the API cannot be reached at all", async () => {
  server.use(http.get(HEALTH_CHECK, () => HttpResponse.error()));

  render(<App />);

  // Matched loosely on purpose: the wording belongs to the fetch
  // implementation ("fetch failed" under Node, "Failed to fetch" in a browser).
  expect(await screen.findByText(/fetch/i)).toBeInTheDocument();
});
