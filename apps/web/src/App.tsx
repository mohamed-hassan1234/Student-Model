import { useEffect, useState } from "react";

import { fetchSystemStatus, type SystemStatus } from "./api/client";
import { SystemStatusPage } from "./components/SystemStatusPage";

export function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      try {
        const result = await fetchSystemStatus();
        if (active) {
          setStatus(result);
          setError(null);
        }
      } catch {
        if (active) {
          setStatus(null);
          setError("The API status endpoint could not be reached.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadStatus();
    return () => {
      active = false;
    };
  }, []);

  return <SystemStatusPage status={status} loading={loading} error={error} />;
}
