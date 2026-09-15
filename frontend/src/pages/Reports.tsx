import { useEffect, useState } from "react";
import { FileText, Download, Trash2, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { Investigation } from "../api/types";

export default function Reports() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const r: any = await api.listInvestigations();
      setInvestigations(Array.isArray(r) ? r : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const downloadReport = (caseNumber: string) => {
    const url = api.reportUrl(caseNumber);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Evidence dossiers · {investigations.length} case
            {investigations.length === 1 ? "" : "s"} on file
          </p>
        </div>
        <button
          onClick={load}
          className="text-sm bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 rounded-md flex items-center gap-2 hover:bg-[var(--bg-secondary)]"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading && investigations.length === 0 && (
        <div className="p-12 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg text-center text-sm text-[var(--text-muted)]">
          Loading…
        </div>
      )}

      {!loading && investigations.length === 0 && (
        <div className="p-12 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg text-center">
          <FileText
            className="mx-auto mb-3 text-[var(--text-muted)]"
            size={32}
          />
          <p className="text-sm text-[var(--text-secondary)]">
            No investigations yet.
          </p>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Run one from the Investigation page — it will be saved here.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {investigations.map((inv) => {
          const top = inv.candidates?.[0];
          const createdAt = (inv as any).created_at
            ? new Date((inv as any).created_at).toLocaleString()
            : "—";
          return (
            <div
              key={inv.case_number}
              className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)] transition-colors"
            >
              <div className="flex items-start gap-3">
                <FileText
                  className="text-[var(--accent)] mt-1 flex-shrink-0"
                  size={22}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-bold font-mono text-sm text-[var(--text-primary)] truncate">
                      {inv.case_number}
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)] whitespace-nowrap">
                      {createdAt}
                    </span>
                  </div>

                  <div className="text-xs text-[var(--text-muted)] mt-1">
                    Slick #{inv.slick_id} ·{" "}
                    {new Date(inv.origin.time).toLocaleString()}
                  </div>

                  {top && (
                    <div className="text-xs mt-2 flex items-center gap-2 flex-wrap">
                      <span className="text-[var(--text-secondary)]">
                        Top suspect:
                      </span>
                      <span className="text-[var(--text-primary)] font-medium">
                        {top.name || `MMSI ${top.mmsi}`}
                      </span>
                      <span className="text-[var(--accent)] font-mono">
                        {top.total_score?.toFixed(1)}%
                      </span>
                      {top.synthetic && (
                        <span className="text-[10px] text-amber-500">
                          (demo)
                        </span>
                      )}
                    </div>
                  )}

                  <div className="mt-3 flex items-center gap-2">
                    <button
                      onClick={() => downloadReport(inv.case_number)}
                      className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded flex items-center gap-1.5"
                    >
                      <Download size={12} /> Download PDF
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}