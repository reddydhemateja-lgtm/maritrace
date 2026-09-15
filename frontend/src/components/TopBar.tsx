import { useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { api } from "../api/client";

export default function TopBar() {
  const [aisCount, setAisCount] = useState(0);
  const [status, setStatus] = useState<"ok" | "error">("ok");

  useEffect(() => {
    const check = async () => {
      try {
        const res: any = await api.health();
        setAisCount(res?.ais?.vessel_count ?? 0);
        setStatus("ok");
      } catch {
        setStatus("error");
      }
    };
    check();
    const t = setInterval(check, 10000);
    return () => clearInterval(t);
  }, []);

  return (
    <header className="h-14 border-b border-[var(--border)] bg-[var(--bg-secondary)] flex items-center px-6 justify-between">
      <div className="flex items-center gap-3">
        <Activity size={16} className={status === "ok" ? "text-green-400" : "text-red-400"} />
        <span className="text-sm text-[var(--text-secondary)]">
          {status === "ok" ? "Backend online" : "Backend offline"}
        </span>
      </div>
      <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)]">
        <span>
          AIS cache:{" "}
          <span className="text-[var(--accent-hover)] font-mono">{aisCount}</span>{" "}
          vessels
        </span>
        <button
          onClick={() => window.location.reload()}
          className="p-1.5 rounded hover:bg-[var(--bg-card)]"
          title="Reload"
        >
          <RefreshCw size={14} />
        </button>
      </div>
    </header>
  );
}