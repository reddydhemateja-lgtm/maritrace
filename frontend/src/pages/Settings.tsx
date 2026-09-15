import { useState } from "react";
import { api } from "../api/client";

export default function Settings() {
  const [health, setHealth] = useState<any>(null);

  const check = async () => {
    try {
      setHealth(await api.health());
    } catch (e: any) {
      setHealth({ error: e.message });
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Backend configuration & status</p>
      </div>

      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-6 space-y-4">
        <div>
          <div className="text-xs uppercase text-[var(--text-muted)]">API URL</div>
          <div className="font-mono text-sm mt-1">
            {import.meta.env.VITE_API_URL || "http://127.0.0.1:8001"}
          </div>
        </div>
        <button
          onClick={check}
          className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 rounded-md text-sm"
        >
          Check Backend Health
        </button>
        {health && (
          <pre className="bg-[var(--bg-secondary)] p-4 rounded text-xs overflow-auto">
            {JSON.stringify(health, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}