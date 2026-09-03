import { useEffect, useState } from "react";

import { api } from "@/api/client";

type HealthCheck =
  | { state: "loading" }
  | { state: "ok"; payload: string }
  | { state: "error"; message: string };

function App() {
  const [healthCheck, setHealthCheck] = useState<HealthCheck>({
    state: "loading",
  });

  useEffect(() => {
    let cancelled = false;

    async function runHealthCheck(): Promise<void> {
      try {
        const { data } = await api.GET("/health-check");
        if (cancelled) return;
        setHealthCheck(
          data === undefined
            ? { state: "error", message: "The API answered with an error." }
            : { state: "ok", payload: data },
        );
      } catch (error) {
        if (cancelled) return;
        setHealthCheck({
          state: "error",
          message:
            error instanceof Error ? error.message : "The API is unreachable.",
        });
      }
    }

    void runHealthCheck();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1>Webapp</h1>
      {healthCheck.state === "loading" && <p>Contacting the API…</p>}
      {healthCheck.state === "ok" && (
        <p>
          The API answered <code>{healthCheck.payload}</code>.
        </p>
      )}
      {healthCheck.state === "error" && <p>{healthCheck.message}</p>}
    </div>
  );
}

export default App;
